"""
Regression tests for Phase 5 (Webhook Security, Verification, Deduplication, and Pipeline State Change).
"""

import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from src.webhook_server import app, get_current_user
from src.processing.shared_state import reset_shared_state, get_shared_city_state_manager

@pytest.fixture(autouse=True)
def clean_state():
    reset_shared_state()
    from src.webhook_server import _WEBHOOK_RATE_LIMIT_LOG, _WEBHOOK_DEDUP_CACHE
    _WEBHOOK_RATE_LIMIT_LOG.clear()
    _WEBHOOK_DEDUP_CACHE.clear()
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-admin", "full_name": "Test Operator"}
    yield
    reset_shared_state()
    _WEBHOOK_RATE_LIMIT_LOG.clear()
    _WEBHOOK_DEDUP_CACHE.clear()
    app.dependency_overrides.clear()

def test_webhook_unauthorized_when_secret_configured(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "super-secret-key-1234")
    client = TestClient(app)

    payload = {
        "event_type": "traffic_accident",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "severity": "CRITICAL"
    }

    # 1. No auth headers -> 401
    resp = client.post("/events", json=payload)
    assert resp.status_code == 401
    assert "invalid or missing" in resp.json()["detail"]

    # 2. Invalid secret header -> 401
    resp = client.post("/events", json=payload, headers={"X-Webhook-Secret": "wrong-secret"})
    assert resp.status_code == 401

    # 3. Valid secret header -> 200
    resp = client.post("/events", json=payload, headers={"X-Webhook-Secret": "super-secret-key-1234"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "INGESTED"

def test_webhook_hmac_signature_verification(monkeypatch):
    secret = "hmac-testing-secret-789"
    monkeypatch.setenv("WEBHOOK_SECRET", secret)
    client = TestClient(app)

    payload = {
        "event_type": "scanner_alert",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "severity": "HIGH",
        "data": {"message": "Structural alert reported"}
    }
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    # Valid HMAC signature in header
    resp = client.post(
        "/events",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": f"sha256={sig}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "INGESTED"

    # Corrupted HMAC signature in header -> 401
    resp_bad = client.post(
        "/events",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": "sha256=invalidhexdigest"}
    )
    assert resp_bad.status_code == 401

def test_webhook_payload_size_limit(monkeypatch):
    monkeypatch.setenv("MAX_WEBHOOK_PAYLOAD_BYTES", "500")
    client = TestClient(app)

    # Payload exceeding 500 bytes limit
    large_payload = {
        "event_type": "sensor_dump",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "data": {"big_blob": "A" * 1000}
    }
    resp = client.post("/events", json=large_payload)
    assert resp.status_code == 413
    assert "exceeds" in resp.json()["detail"]

def test_webhook_schema_and_coordinate_bounds_validation():
    client = TestClient(app)

    # 1. Missing coordinates -> 422
    resp = client.post("/events", json={"event_type": "test_missing_coords"})
    assert resp.status_code == 422
    assert "Coordinates required" in resp.json()["detail"]

    # 2. Latitude out of range (> 90.0) -> 422
    resp = client.post("/events", json={"event_type": "invalid_lat", "latitude": 95.5, "longitude": 80.27})
    assert resp.status_code == 422
    assert "out of valid range" in resp.json()["detail"]

    # 3. Longitude out of range (< -180.0) -> 422
    resp = client.post("/events", json={"event_type": "invalid_lon", "latitude": 13.08, "longitude": -195.0})
    assert resp.status_code == 422
    assert "out of valid range" in resp.json()["detail"]

    # 4. Non-numeric coordinates -> 422
    resp = client.post("/events", json={"event_type": "bad_type", "latitude": "not-a-number", "longitude": 80.27})
    assert resp.status_code == 422

def test_webhook_deduplication():
    client = TestClient(app)
    payload = {
        "event_id": "evt-dedup-unique-9999",
        "event_type": "critical_power_outage",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "severity": "CRITICAL",
        "data": {"city": "Chennai"}
    }

    # First submission -> 200 INGESTED
    resp1 = client.post("/events", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "INGESTED"

    # Second submission with same event_id -> 409 DUPLICATE
    resp2 = client.post("/events", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["status"] == "DUPLICATE"
    assert resp2.json()["event_id"] == "evt-dedup-unique-9999"

def test_webhook_pipeline_integration_changes_api_state():
    client = TestClient(app)

    # Initial state
    initial_state = client.get("/api/state").json()
    initial_event_count = len(initial_state.get("recent_events", []))
    initial_chennai_events = initial_state["city_summaries"]["Chennai"]["event_count"]

    # Send valid webhook event
    unique_id = "test-webhook-state-change-01"
    payload = {
        "event_id": unique_id,
        "event_type": "flash_flood_warning",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "severity": "CRITICAL",
        "data": {
            "city": "Chennai",
            "event_type": "flash_flood_warning",
            "severity": "CRITICAL",
            "description": "Severe localized flooding near Guindy industrial estate"
        }
    }
    post_resp = client.post("/events", json=payload)
    assert post_resp.status_code == 200
    assert post_resp.json()["status"] == "INGESTED"

    # Query updated state from GET /api/state
    updated_state = client.get("/api/state").json()
    updated_chennai = updated_state["city_summaries"]["Chennai"]

    # Verify event entered state and changed metrics
    assert updated_chennai["event_count"] == initial_chennai_events + 1
    assert updated_chennai["critical_count"] >= 1
    assert updated_chennai["risk_score"] > 0
    assert any(
        e.get("event_id") == unique_id or e.get("data", {}).get("event_id") == unique_id
        for e in updated_state.get("recent_events", [])
    )

def test_webhook_production_rejects_missing_secret(monkeypatch):
    """Verifies that in production, missing WEBHOOK_SECRET strictly blocks all requests."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    client = TestClient(app)

    payload = {"event_type": "fire_alert", "latitude": 13.08, "longitude": 80.27}
    resp = client.post("/events", json=payload)
    assert resp.status_code == 401
    assert "WEBHOOK_SECRET must be configured in production" in resp.json()["detail"]

def test_webhook_ip_spoofing_prevented_and_trusted_proxy_respected(monkeypatch):
    """
    Verifies that spoofed X-Forwarded-For headers from untrusted clients cannot
    bypass sliding-window rate limiting.
    """
    monkeypatch.setenv("WEBHOOK_RATE_LIMIT_RPM", "2")
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    client = TestClient(app)

    payload = {"event_type": "rate_limit_test", "latitude": 13.08, "longitude": 80.27}

    # 1. Attacker sends requests attempting to spoof different client IPs via X-Forwarded-For
    resp1 = client.post("/events", json=payload, headers={"X-Forwarded-For": "1.1.1.1"})
    assert resp1.status_code == 200

    resp2 = client.post("/events", json=payload, headers={"X-Forwarded-For": "2.2.2.2"})
    assert resp2.status_code == 200

    # 3rd request from same direct connection must be blocked at limit 2, regardless of forged header
    resp3 = client.post("/events", json=payload, headers={"X-Forwarded-For": "3.3.3.3"})
    assert resp3.status_code == 429
    assert "rate limit" in resp3.json()["detail"]
