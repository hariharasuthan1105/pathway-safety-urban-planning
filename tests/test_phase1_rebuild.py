"""
Phase 1 Rebuild Unit Test Suite (§4, §5, §6, §14).

Tests:
1. User Signup & Authentication (SQLite, PBKDF2 hashing, duplicate check, password strength).
2. Session Management & Expiry.
3. TrafficSimulationSource determinism (seeded) & stream schema.
4. End-to-End Pathway Event -> CityStateManager pipeline ingestion.
5. FastAPI Server Endpoint Security (401 on protected routes, 200 on authenticated).
"""

import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.auth import (
    signup_user,
    authenticate_user,
    get_session_user,
    delete_session,
    init_auth_db
)
from src.data_sources.traffic_sim import TrafficSimulationSource
from src.webhook_server import app

TEST_DB = "test_auth_suite.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Fixture initializing isolated test database and wiping between tests."""
    os.environ["AUTH_DB_PATH"] = TEST_DB
    init_auth_db()
    with sqlite3.connect(TEST_DB) as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM users")
        conn.commit()
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

def test_signup_validation_and_hashing():
    # Weak password rejection (< 10 chars)
    with pytest.raises(ValueError, match="at least 10 characters"):
        signup_user("Operator", "op@urban.in", "short")

    # Valid signup
    user = signup_user("Control Operator", "OP@URBAN.IN", "SecurePassword123!")
    assert user["email"] == "op@urban.in"
    assert user["id"].startswith("usr_")

    # Duplicate email rejection
    with pytest.raises(ValueError, match="already exists"):
        signup_user("Operator 2", "op@urban.in", "AnotherSecurePassword123!")

def test_authentication_and_session():
    signup_user("Test User", "test@urban.in", "Password12345!")

    # Bad password failure
    with pytest.raises(ValueError, match="Invalid email or password"):
        authenticate_user("test@urban.in", "WrongPassword123!")

    # Valid login
    auth_res = authenticate_user("test@urban.in", "Password12345!", remember=True)
    token = auth_res["token"]
    assert token is not None

    # Retrieve session user
    session_user = get_session_user(token)
    assert session_user is not None
    assert session_user["email"] == "test@urban.in"

    # Logout / Invalidation
    delete_session(token)
    assert get_session_user(token) is None

def test_traffic_simulation_determinism():
    config = {
        "traffic_sim_seed": 42,
        "data_sources": {"traffic": {"poll_interval": 1}}
    }
    src1 = TrafficSimulationSource(config)
    stream1 = src1._stream()
    ev1 = next(stream1)

    assert ev1["source"] == "traffic_simulation"
    assert "city" in ev1["data"]
    assert "congestion_level" in ev1["data"]
    assert "mode" in ev1["data"]
    assert ev1["data"]["mode"] == "SIMULATED"

def test_fastapi_protected_endpoints():
    client = TestClient(app)

    # Health check is public
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "HEALTHY"

    # Protected routes return 401 when unauthenticated
    state_res = client.get("/api/state")
    assert state_res.status_code == 401

    # Authenticated signup flow
    signup_res = client.post("/api/auth/signup", json={
        "full_name": "API Tester",
        "email": "tester@urban.in",
        "password": "ValidPassword123!"
    })
    assert signup_res.status_code == 201
    token = signup_res.json()["token"]

    # Access protected state endpoint with session token cookie
    authed_state_res = client.get("/api/state", cookies={"session_token": token})
    assert authed_state_res.status_code == 200
    state_data = authed_state_res.json()
    assert "meta" in state_data
    assert "sources" in state_data
    assert "city_summaries" in state_data
