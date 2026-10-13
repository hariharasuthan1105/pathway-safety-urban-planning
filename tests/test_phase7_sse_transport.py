"""
Tests for Phase 7 Server-Sent Events (SSE) Transport endpoint (/api/stream).
"""

import json
from unittest.mock import MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient

from src.webhook_server import app, stream_state_updates, get_current_user
from src.processing.shared_state import reset_shared_state

@pytest.fixture(autouse=True)
def clean_state():
    reset_shared_state()
    yield
    reset_shared_state()
    app.dependency_overrides.clear()

def test_sse_stream_unauthorized_without_auth():
    """Unauthenticated requests to /api/stream must be rejected with 401."""
    client = TestClient(app)
    resp = client.get("/api/stream")
    assert resp.status_code == 401

@pytest.mark.anyio
async def test_sse_generator_yields_state_updates_and_handles_disconnect():
    """
    Verifies that stream_state_updates yields structured SSE payload
    and terminates gracefully when client disconnects.
    """
    mock_request = MagicMock()
    mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

    user = {"id": "op-01", "full_name": "Command Operator"}
    resp = await stream_state_updates(mock_request, current_user=user)
    assert resp.media_type == "text/event-stream"

    chunks = []
    async for chunk in resp.body_iterator:
        chunks.append(chunk)

    assert len(chunks) == 1
    chunk_str = chunks[0]
    assert "event: state_update\n" in chunk_str
    assert "data: " in chunk_str

    # Extract JSON data block
    for line in chunk_str.strip().split("\n"):
        if line.startswith("data: "):
            data = json.loads(line[6:])
            assert data["event"] == "state_update"
            assert "overall_risk_score" in data
            assert "overall_risk_level" in data
            assert "city_summaries" in data
            assert "data_freshness" in data
            break
    else:
        pytest.fail("SSE event payload did not contain data line")
