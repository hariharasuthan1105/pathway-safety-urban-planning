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
        entry = freshness.setdefault(key, {"last_update": None, "event_count": 0, "mode": mode, "status": "WAITING"})
        observed = entry.get("status", "WAITING")
        status_value = connector.get("status", "WAITING").replace(" ", "_")
        entry["observation_status"] = observed
        entry["connector_status"] = status_value
        if status_value in {"OFFLINE", "DEGRADED", "NOT_CONFIGURED"}:
            entry["status"] = status_value
        elif not entry.get("event_count"):
            entry["status"] = status_value if status_value in {"READY", "REACHABLE"} else "WAITING"
        entry["last_checked_at"] = connector.get("last_checked_at")
        if status_value == "NOT_CONFIGURED":
            entry["mode"] = "NOT_CONFIGURED"
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
        state["sources"] = [{"id": sid, "label": label, "mode": mode,
                             "status": freshness.get(sid, {}).get("status", "WAITING"),
                             "last_ok_at": freshness.get(sid, {}).get("last_update")}
                            for sid, label, mode in specs]
        state["sources"].append({"id": "gtfs_transit", "label": "GTFS TRANSIT", "mode": "NOT_CONFIGURED", "status": "NOT_CONFIGURED", "last_ok_at": freshness.get("gtfs_transit_api", {}).get("last_update")})
        runtime_status = _SOURCE_STATUS_PROVIDER() if _SOURCE_STATUS_PROVIDER else {}
        for source in state["sources"]:
            connector_id = {"webhook_ingestion": "webhook_api", "gtfs_transit": "gtfs_transit_api", "twitter": "social_media", "police_scanner": "public_safety", "city_sensors": "iot_sensors"}.get(source["id"], source["id"])
            connector = runtime_status.get(connector_id)
            if connector:
                status_value = connector.get("status", "WAITING").replace(" ", "_")
                if status_value in {"OFFLINE", "DEGRADED"}:
                    source["status"] = status_value
                elif status_value in {"READY", "NOT_CONFIGURED"}:
                    source["status"] = status_value
                if source["id"] == "gtfs_transit" and status_value != "NOT_CONFIGURED":
                    source["mode"] = "LIVE"
                    source["status"] = status_value
            elif runtime_status and source["mode"] != "EVENT_DRIVEN":
                source["status"] = "NOT_CONFIGURED"
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
async def stream_state_updates(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Server-Sent Events (SSE) streaming endpoint pushing real-time state deltas."""
    async def event_generator():
        city_state_mgr = get_shared_city_state_manager()

        while True:
            try:
                state = city_state_mgr.get_live_city_state()
                current_version = int(time.time() * 10)

                payload = {
                    "event": "state_update",
                    "state_version": current_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_risk_score": state.get("overall_risk_score", 0),
                    "overall_risk_level": state.get("overall_risk_level", "LOW"),
                    "recent_event_count": len(state.get("recent_events", [])),
                    "city_summaries": state.get("city_summaries", {})
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
    """Receives external incident reports and webhook payloads."""
    try:
        body = await request.json()
        event = ingest_webhook_payload(body)
        return {"status": "INGESTED", "event_id": event["data"]["event_id"], "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Webhook ingestion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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
