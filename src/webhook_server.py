"""
Commercial-Grade FastAPI Web & Telemetry Server for South India Urban Intelligence (§3, §4, §5).

Endpoints:
- POST /api/auth/signup, POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me
- GET /api/state (Protected, complete real-time state with provenance)
- GET /api/stream (Protected, SSE real-time delta updates)
- GET /api/cities/{id}/history (Protected, metric history)
- POST /api/ask (Protected, Grounded RAG + Groq decision support)
- POST /events (Public/Authenticated webhook ingestion)
- GET /api/health (Public health check)
"""

import os
import json
import time
import asyncio
import logging
import threading
import hmac
import hashlib
from collections import deque
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, Field
import uvicorn

from .auth import signup_user, authenticate_user, get_session_user, delete_session
from .data_sources.real_sources import ingest_webhook_payload
from .processing.shared_state import get_shared_city_state_manager, get_shared_rag_system

logger = logging.getLogger("webhook_server")

# Global handle for AI RAG query handler function
_AI_QUERY_HANDLER: Optional[Any] = None
_SOURCE_STATUS_PROVIDER = None

# Thread-safe in-memory deduplication cache and rate limiting
_WEBHOOK_DEDUP_CACHE: Dict[str, float] = {}
_WEBHOOK_RATE_LIMIT_LOG: Dict[str, deque] = {}
_WEBHOOK_LOCK = threading.Lock()

def _verify_webhook_authorization(request: Request, raw_body: bytes) -> None:
    """
    Verifies webhook authorization using configurable secret or HMAC signature.
    Uses constant-time comparison to prevent timing side-channel attacks.
    If WEBHOOK_SECRET is unconfigured, allows request (for local dev testing).
    """
    webhook_secret = os.getenv("WEBHOOK_SECRET", "").strip()
    is_prod = os.getenv("ENVIRONMENT", "development").lower() in {"production", "prod"}
    if not webhook_secret:
        if is_prod:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized webhook: WEBHOOK_SECRET must be configured in production environment."
            )
        return

    # 1. Header: X-Webhook-Secret
    secret_header = request.headers.get("X-Webhook-Secret", "").strip()
    if secret_header and hmac.compare_digest(secret_header, webhook_secret):
        return

    # 2. Header: Authorization: Bearer <secret>
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if hmac.compare_digest(token, webhook_secret):
            return

    # 3. Header: X-Webhook-Signature: sha256=<hex>
    sig_header = request.headers.get("X-Webhook-Signature", "").strip()
    if sig_header:
        expected_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        provided_sig = sig_header.lower().replace("sha256=", "").strip()
        if hmac.compare_digest(provided_sig, expected_sig):
            return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized webhook: invalid or missing authorization secret/signature."
    )

def _get_client_ip(request: Request) -> str:
    """
    Safely resolves client IP respecting trusted proxy settings to prevent IP spoofing.
    If TRUSTED_PROXIES is configured, inspects X-Forwarded-For safely if direct peer is trusted.
    Otherwise strictly defaults to the direct TCP peer (request.client.host).
    """
    direct_ip = request.client.host if request.client else "unknown"
    trusted_cfg = os.getenv("TRUSTED_PROXIES", "").strip()
    if not trusted_cfg:
        return direct_ip

    trusted_proxies = {p.strip() for p in trusted_cfg.split(",") if p.strip()}
    if direct_ip in trusted_proxies or "all" in trusted_proxies or "render" in trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For", "").strip()
        if forwarded:
            hops = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
            if hops:
                return hops[0]

    return direct_ip

def _check_webhook_rate_limit(client_ip: str) -> None:
    """Sliding-window IP rate limiter for webhook endpoint."""
    rpm_limit = int(os.getenv("WEBHOOK_RATE_LIMIT_RPM", "120"))
    now = time.time()
    with _WEBHOOK_LOCK:
        if client_ip not in _WEBHOOK_RATE_LIMIT_LOG:
            _WEBHOOK_RATE_LIMIT_LOG[client_ip] = deque()
        timestamps = _WEBHOOK_RATE_LIMIT_LOG[client_ip]
        while timestamps and (now - timestamps[0] > 60.0):
            timestamps.popleft()
        if len(timestamps) >= rpm_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Webhook rate limit of {rpm_limit} requests/min exceeded.",
                headers={"Retry-After": "60"}
            )
        timestamps.append(now)

def _check_webhook_deduplication(event_id: str) -> bool:
    """Returns True if already seen (duplicate), otherwise records it and returns False."""
    now = time.time()
    with _WEBHOOK_LOCK:
        stale_keys = [k for k, ts in _WEBHOOK_DEDUP_CACHE.items() if (now - ts) > 3600]
        for k in stale_keys:
            del _WEBHOOK_DEDUP_CACHE[k]

        if event_id in _WEBHOOK_DEDUP_CACHE:
            return True
        _WEBHOOK_DEDUP_CACHE[event_id] = now
        return False

def register_source_status_provider(provider):
    global _SOURCE_STATUS_PROVIDER
    _SOURCE_STATUS_PROVIDER = provider

def source_freshness_report(state):
    """Observation history and current connector availability are separate facts."""
    freshness = {key: dict(value) for key, value in state.get("data_freshness", {}).items()}
    runtime = _SOURCE_STATUS_PROVIDER() if _SOURCE_STATUS_PROVIDER else {}
    aliases = {"webhook_api": "webhook_ingestion", "social_media": "twitter",
               "public_safety": "police_scanner", "iot_sensors": "city_sensors"}
    simulated = {"traffic_simulation", "twitter", "police_scanner", "city_sensors",
                 "simulation_generator", "transit_simulation",
                 "planning_traffic_simulation", "environment_simulation"}
    for connector_id, connector in runtime.items():
        key = aliases.get(connector_id, connector_id)
        mode = "SIMULATED" if key in simulated else "EVENT_DRIVEN" if key == "webhook_ingestion" else "LIVE"
        entry = freshness.setdefault(key, {
            "source_id": key,
            "last_update": None,
            "observed_at": None,
            "received_at": None,
            "last_checked_at": None,
            "event_count": 0,
            "mode": mode,
            "status": "WAITING",
            "observation_status": "WAITING",
            "connector_status": "WAITING",
            "freshness_age_seconds": None,
            "error_code": None
        })
        observed = entry.get("observation_status") or entry.get("status", "WAITING")
        status_value = connector.get("status", "WAITING").replace(" ", "_")
        entry["source_id"] = key
        entry["observation_status"] = observed
        entry["connector_status"] = status_value
        if status_value in {"OFFLINE", "DEGRADED", "NOT_CONFIGURED"}:
            entry["status"] = status_value
        elif not entry.get("event_count"):
            entry["status"] = status_value if status_value in {"READY", "REACHABLE"} else "WAITING"
        entry["last_checked_at"] = connector.get("last_checked_at") or entry.get("last_checked_at")
        if status_value == "NOT_CONFIGURED":
            entry["mode"] = "NOT_CONFIGURED"
    # Ensure standardized fields on every entry
    for k, entry in freshness.items():
        entry["source_id"] = k
        entry.setdefault("connector_status", entry.get("status", "WAITING"))
        entry.setdefault("observation_status", entry.get("status", "WAITING"))
        entry.setdefault("observed_at", entry.get("last_update"))
        entry.setdefault("received_at", entry.get("last_update"))
        entry.setdefault("freshness_age_seconds", None)
        entry.setdefault("error_code", None)
    return freshness


def register_ai_query_handler(handler: Any):
    """Registers global handler function for POST /api/ask endpoint."""
    global _AI_QUERY_HANDLER
    _AI_QUERY_HANDLER = handler
    logger.info("[FastAPI Server] Registered AI RAG query handler for /api/ask.")

# Initialize FastAPI App
app = FastAPI(
    title="South India Urban Intelligence API",
    description="Real-time urban operations and decision-support platform API for Tamil Nadu, Kerala, and Andhra Pradesh.",
    version="1.0.0"
)

# Configure CORS Middleware
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8000,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper for secure session cookie configuration
def set_auth_cookie(response: Response, token: str, max_age: int):
    is_secure = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    samesite_val = os.getenv("COOKIE_SAMESITE", "none" if is_secure else "lax")
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite=samesite_val,
        secure=is_secure,
        max_age=max_age,
        path="/"
    )

# Pydantic Request Models
class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=10)

class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)

# Dependency: Session Cookie Authentication Guard
async def get_current_user(request: Request) -> Dict[str, Any]:
    session_token = request.cookies.get("session_token")
    if not session_token:
        # Also check Authorization header Bearer token if present
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]

    user = get_session_user(session_token) if session_token else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in to access urban operations state."
        )
    return user

# Optional user dependency for endpoints that handle guest/user distinction
async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]

    return get_session_user(session_token) if session_token else None

# ==============================================================================
# AUTHENTICATION ENDPOINTS (§4)
# ==============================================================================

@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
async def auth_signup(req: SignupRequest, response: Response):
    try:
        user = signup_user(req.full_name, req.email, req.password)
        # Automatically authenticate upon successful signup
        auth_res = authenticate_user(req.email, req.password, remember=True)
        token = auth_res["token"]
        set_auth_cookie(response, token, max_age=30 * 86400)
        return {"user": auth_res["user"], "token": token, "message": "Account created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")

@app.post("/api/auth/login")
async def auth_login(req: LoginRequest, response: Response):
    try:
        auth_res = authenticate_user(req.email, req.password, remember=req.remember)
        token = auth_res["token"]
        max_age = 30 * 86400 if req.remember else 86400
        set_auth_cookie(response, token, max_age=max_age)
        return {"user": auth_res["user"], "token": token, "message": "Authenticated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def auth_me(user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"authenticated": False, "error": "No active session"}
        )
    return {"authenticated": True, "user": user}

# ==============================================================================
# REAL-TIME OPERATIONAL STATE & TELEMETRY ENDPOINTS (§5)
# ==============================================================================

@app.get("/api/state")
async def get_state(current_user: Dict[str, Any] = Depends(get_current_user)):
    try:
        city_state_mgr = get_shared_city_state_manager()
        state = city_state_mgr.get_live_city_state()

        freshness = source_freshness_report(state)
        state["data_freshness"] = freshness
        timestamps = [v["last_update"] for v in freshness.values() if v.get("last_update")]
        last_batch = max(timestamps) if timestamps else None
        state["meta"] = {
            "mode": os.getenv("DATA_MODE", "HYBRID").upper(),
            "server_time": datetime.now(timezone.utc).isoformat(),
            "state_version": sum(v.get("event_count", 0) for v in freshness.values()),
            "pathway": {"status": "RECEIVING" if last_batch else "WAITING", "last_batch_at": last_batch}
        }
        specs = [("weather_api", "WEATHER API (OPEN-METEO)", "LIVE"),
                 ("air_quality_api", "AIR QUALITY API (OPEN-METEO)", "LIVE"),
                 ("traffic_simulation", "TRAFFIC SIMULATION STREAM", "SIMULATED"),
                 ("webhook_ingestion", "WEBHOOK INGESTION", "EVENT_DRIVEN"),
                 ("twitter", "SOCIAL SIGNAL SIMULATION", "SIMULATED"),
                 ("police_scanner", "PUBLIC SAFETY SIMULATION", "SIMULATED"),
                 ("city_sensors", "IOT SENSOR SIMULATION", "SIMULATED")]
        if os.getenv("DATA_MODE", "hybrid").lower() != "live":
            for sid, label in [("transit_simulation", "TRANSIT SIMULATION"),
                               ("planning_traffic_simulation", "PLANNING TRAFFIC SIMULATION"),
                               ("environment_simulation", "ENVIRONMENT SIMULATION")]:
                if sid in freshness:
                    specs.append((sid, label, "SIMULATED"))
        state["sources"] = [{"id": sid, "source_id": sid, "label": label, "mode": mode,
                             "status": freshness.get(sid, {}).get("status", "WAITING"),
                             "connector_status": freshness.get(sid, {}).get("connector_status", "WAITING"),
                             "observation_status": freshness.get(sid, {}).get("observation_status", "WAITING"),
                             "last_ok_at": freshness.get(sid, {}).get("last_update"),
                             "observed_at": freshness.get(sid, {}).get("observed_at"),
                             "received_at": freshness.get(sid, {}).get("received_at"),
                             "freshness_age_seconds": freshness.get(sid, {}).get("freshness_age_seconds")}
                            for sid, label, mode in specs]
        state["sources"].append({
            "id": "gtfs_transit", "source_id": "gtfs_transit_api", "label": "GTFS TRANSIT",
            "mode": freshness.get("gtfs_transit_api", {}).get("mode", "NOT_CONFIGURED"),
            "status": freshness.get("gtfs_transit_api", {}).get("status", "NOT_CONFIGURED"),
            "connector_status": freshness.get("gtfs_transit_api", {}).get("connector_status", "NOT_CONFIGURED"),
            "observation_status": freshness.get("gtfs_transit_api", {}).get("observation_status", "NOT_CONFIGURED"),
            "last_ok_at": freshness.get("gtfs_transit_api", {}).get("last_update"),
            "observed_at": freshness.get("gtfs_transit_api", {}).get("observed_at"),
            "received_at": freshness.get("gtfs_transit_api", {}).get("received_at"),
            "freshness_age_seconds": freshness.get("gtfs_transit_api", {}).get("freshness_age_seconds")
        })
        runtime_status = _SOURCE_STATUS_PROVIDER() if _SOURCE_STATUS_PROVIDER else {}
        for source in state["sources"]:
            connector_id = {"webhook_ingestion": "webhook_api", "gtfs_transit": "gtfs_transit_api", "twitter": "social_media", "police_scanner": "public_safety", "city_sensors": "iot_sensors"}.get(source["id"], source["id"])
            connector = runtime_status.get(connector_id)
            if connector:
                status_value = connector.get("status", "WAITING").replace(" ", "_")
                if status_value in {"OFFLINE", "DEGRADED"}:
                    source["status"] = status_value
                    source["connector_status"] = status_value
                elif status_value in {"READY", "NOT_CONFIGURED"}:
                    source["status"] = status_value
                    source["connector_status"] = status_value
                if source["id"] == "gtfs_transit" and status_value != "NOT_CONFIGURED":
                    source["mode"] = "LIVE"
                    source["status"] = status_value
                    source["connector_status"] = status_value
            elif runtime_status and source["mode"] != "EVENT_DRIVEN":
                source["status"] = "NOT_CONFIGURED"
                source["connector_status"] = "NOT_CONFIGURED"
        summaries = state.get("city_summaries", {})
        state["region"] = {"overall_risk_score": state["overall_risk_score"],
            "overall_risk_level": state["overall_risk_level"], "risk_trend": state["risk_trend"],
            "active_events": state["rolling_metrics"]["count_60m"],
            "active_anomalies": len(state["active_anomalies"]),
            "cities_online": sum(c["event_count"] > 0 for c in summaries.values()), "cities_total": len(summaries)}
        return state
    except Exception as e:
        logger.error(f"[API] GET /api/state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream")
async def stream_state_updates(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Server-Sent Events (SSE) streaming endpoint pushing real-time state deltas."""
    async def event_generator():
        city_state_mgr = get_shared_city_state_manager()

        while True:
            if await request.is_disconnected():
                break
            try:
                state = city_state_mgr.get_live_city_state()
                freshness = source_freshness_report(state)
                current_version = sum(v.get("event_count", 0) for v in freshness.values())

                payload = {
                    "event": "state_update",
                    "state_version": current_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_risk_score": state.get("overall_risk_score", 0),
                    "overall_risk_level": state.get("overall_risk_level", "LOW"),
                    "risk_trend": state.get("risk_trend", "STABLE"),
                    "recent_event_count": len(state.get("recent_events", [])),
                    "city_summaries": state.get("city_summaries", {}),
                    "active_anomalies": state.get("active_anomalies", []),
                    "correlations": state.get("correlations", []),
                    "data_freshness": freshness
                }
                yield f"event: state_update\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(2.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                await asyncio.sleep(5.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/cities/{city_id}/history")
async def get_city_history(
    city_id: str,
    metric: str = "risk",
    window: str = "1h",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Returns timeseries history for charts."""
    city_state_mgr = get_shared_city_state_manager()
    state = city_state_mgr.get_live_city_state()

    # Only measured telemetry; never manufacture historical risk scores.
    normalized = city_id.replace("_", " ").casefold()
    city = next((c for c in state.get("city_summaries", {}) if c.casefold() == normalized), None)
    if city is None:
        raise HTTPException(status_code=404, detail="Unknown city")
    windows = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}
    if window not in windows:
        raise HTTPException(status_code=400, detail="Unsupported history window")
    points = []
    for event in city_state_mgr.rolling_aggregator.get_events_in_window(windows[window]):
        data = event.get("data", {})
        if data.get("city", event.get("location", {}).get("city")) != city:
            continue
        point = {"timestamp": event.get("timestamp"), "aqi": data.get("air_quality_index"),
                 "temperature": data.get("temperature"), "congestion": data.get("congestion_level")}
        value = point.get(metric)
        if value is not None:
            points.append({**point, "value": value, "metric": metric})
    return {"city_id": city_id, "metric": metric, "window": window, "data_points": points,
            "history": points, "source": "CityStateManager.recorded_events"}

@app.get("/api/health")
async def health_check():
    """Unauthenticated health check endpoint for deployment monitoring."""
    city_state_mgr = get_shared_city_state_manager()
    state = city_state_mgr.get_live_city_state()
    rag_sys = get_shared_rag_system()

    return {
        "status": "HEALTHY",
        "pathway_engine": "RECEIVING" if state.get("recent_events") else "WAITING",
        "data_mode": os.getenv("DATA_MODE", "HYBRID").upper(),
        "llm_configured": getattr(rag_sys, "has_valid_key", False),
        "data_freshness": source_freshness_report(state),
        "total_events_ingested": len(state.get("recent_events", []))
    }

@app.get("/api/risk")
async def get_risk_assessment(current_user: Dict[str, Any] = Depends(get_current_user)):
    city_state_mgr = get_shared_city_state_manager()
    state = city_state_mgr.get_live_city_state()
    return {
        "overall_risk_score": state.get("overall_risk_score", 0),
        "overall_risk_level": state.get("overall_risk_level", "LOW"),
        "risk_trend": state.get("risk_trend", "STABLE"),
        "contributing_factors": state.get("contributing_factors", []),
        "zone_summaries": state.get("zone_summaries", {})
    }

@app.get("/api/anomalies")
async def get_anomalies(current_user: Dict[str, Any] = Depends(get_current_user)):
    city_state_mgr = get_shared_city_state_manager()
    state = city_state_mgr.get_live_city_state()
    return {
        "active_anomalies": state.get("active_anomalies", []),
        "correlations": state.get("correlations", []),
        "count": len(state.get("active_anomalies", []))
    }

@app.get("/api/events")
async def get_recent_events(current_user: Dict[str, Any] = Depends(get_current_user)):
    city_state_mgr = get_shared_city_state_manager()
    state = city_state_mgr.get_live_city_state()
    events = state.get("recent_events", [])
    return {"events": events, "count": len(events)}

# ==============================================================================
# WEBHOOK & AI ASK ENDPOINTS (§7)
# ==============================================================================

@app.post("/events")
async def ingest_webhook_event(request: Request):
    """
    Receives external incident reports and webhook payloads with production security:
    - Payload size limit (default 64KB, configurable via MAX_WEBHOOK_PAYLOAD_BYTES)
    - Configurable constant-time shared secret / HMAC signature verification
    - Schema & coordinate bounds validation
    - IP-based sliding window rate limiting
    - Event deduplication cache
    """
    client_ip = _get_client_ip(request)
    _check_webhook_rate_limit(client_ip)

    max_bytes = int(os.getenv("MAX_WEBHOOK_PAYLOAD_BYTES", "65536"))
    raw_body = await request.body()
    if len(raw_body) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Webhook payload size ({len(raw_body)} bytes) exceeds configured limit ({max_bytes} bytes)."
        )

    _verify_webhook_authorization(request, raw_body)

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON webhook payload.")

    if not isinstance(body, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Payload must be a JSON object.")

    # Validate coordinate boundaries
    lat = body.get("latitude") if body.get("latitude") is not None else body.get("location", {}).get("lat") if isinstance(body.get("location"), dict) else None
    lon = body.get("longitude") if body.get("longitude") is not None else body.get("location", {}).get("lon") if isinstance(body.get("location"), dict) else None

    if lat is None or lon is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coordinates required: latitude and longitude must be provided."
        )

    try:
        f_lat, f_lon = float(lat), float(lon)
        if not (-90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Coordinates out of valid range: lat [-90, 90], lon [-180, 180]. Got ({f_lat}, {f_lon})."
            )
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Coordinates must be numeric.")

    # Deduplication check
    event_id = str(body.get("event_id") or "").strip()
    if event_id:
        if _check_webhook_deduplication(event_id):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"status": "DUPLICATE", "event_id": event_id, "detail": f"Event '{event_id}' has already been processed."}
            )

    try:
        event = ingest_webhook_payload(body)
        return {
            "status": "INGESTED",
            "event_id": event["data"]["event_id"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        logger.error(f"Webhook ingestion error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/ask")
def ask_copilot(req: AskRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Grounded RAG query execution against Groq LLM or fallback Copilot."""
    if _AI_QUERY_HANDLER:
        res = _AI_QUERY_HANDLER(req.question)
        res["state_version_used"] = int(time.time() * 10)
        return res

    city_state_mgr = get_shared_city_state_manager()
    rag_sys = get_shared_rag_system()
    live_state = city_state_mgr.get_live_city_state()
    res = rag_sys.query_structured(req.question, city_state=live_state)
    res["state_version_used"] = int(time.time() * 10)
    return res

# Thread handle for background server
_SERVER_THREAD: Optional[threading.Thread] = None

def start_webhook_server(host: str = "0.0.0.0", port: int = 8000):
    """Launches FastAPI uvicorn web server in a background daemon thread."""
    global _SERVER_THREAD
    if _SERVER_THREAD and _SERVER_THREAD.is_alive():
        logger.info("[FastAPI Server] Server is already running.")
        return

    def run_app():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    _SERVER_THREAD = threading.Thread(target=run_app, daemon=True)
    _SERVER_THREAD.start()
    logger.info(f"[FastAPI Server] Successfully launched background web server on http://{host}:{port}")
