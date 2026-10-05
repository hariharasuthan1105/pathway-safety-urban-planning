"""
Integration tests for real-time event ingestion, live CityStateManager updates,
RAG context formatting, and AI Urban Copilot dynamic responses.
"""

import datetime
import pytest
from src.data_sources.real_sources import ingest_webhook_payload
from src.processing.shared_state import get_shared_city_state_manager, get_shared_rag_system, reset_shared_state
from src.processing.llm_provider import MockLLMProvider
from src.processing.rag_system import RAGSystem

@pytest.fixture(autouse=True)
def clean_shared_state():
    reset_shared_state()
    yield
    reset_shared_state()

def test_realtime_event_flow_to_copilot():
    mgr = get_shared_city_state_manager()
    rag = get_shared_rag_system()
    rag.provider = MockLLMProvider()  # Dynamic parsing mock provider

    # 1. Verify clean initial state
    initial_state = mgr.get_live_city_state()
    assert len(initial_state.get("recent_events", [])) == 0

    # 2. Inject Event REALTIME_TEST_001
    payload_1 = {
        "event_id": "REALTIME_TEST_001",
        "event_type": "vehicle_collision",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "severity": "CRITICAL",
        "source": "webhook_ingestion",
        "data": {
            "event_id": "REALTIME_TEST_001",
            "event_type": "vehicle_collision",
            "severity": "CRITICAL",
            "description": "Multi-car pileup causing major road closure in Zone A",
            "priority": 5
        }
    }

    event1 = ingest_webhook_payload(payload_1)
    assert event1["data"]["event_id"] == "REALTIME_TEST_001"

    # 3. Check CityStateManager updated
    state_after_ev1 = mgr.get_live_city_state()
    assert len(state_after_ev1["recent_events"]) >= 1
    assert state_after_ev1["recent_events"][-1]["data"]["event_id"] == "REALTIME_TEST_001"

    # 4. Query RAG System
    res1 = rag.query_structured("What is happening in the city right now?", city_state=state_after_ev1)
    assert "REALTIME_TEST_001" in res1["answer"]
    assert "vehicle_collision" in res1["answer"]
    assert len(res1["evidence"]) >= 1
    assert res1["evidence"][-1]["event_id"] == "REALTIME_TEST_001"

    # 5. Inject Event REALTIME_TEST_002
    payload_2 = {
        "event_id": "REALTIME_TEST_002",
        "event_type": "air_quality",
        "latitude": 40.7580,
        "longitude": -73.9855,
        "severity": "HIGH",
        "source": "webhook_ingestion",
        "data": {
            "event_id": "REALTIME_TEST_002",
            "event_type": "hazardous_gas_leak",
            "severity": "HIGH",
            "description": "Chemical gas leak detected in Midtown industrial building",
            "air_quality_index": 185
        }
    }

    event2 = ingest_webhook_payload(payload_2)
    assert event2["data"]["event_id"] == "REALTIME_TEST_002"

    # 6. Verify Copilot updates answer to feature REALTIME_TEST_002
    state_after_ev2 = mgr.get_live_city_state()
    res2 = rag.query_structured("What is the latest significant event?", city_state=state_after_ev2)
    assert "REALTIME_TEST_002" in res2["answer"]
    assert "air_quality" in res2["answer"]
    assert "Chemical gas leak" in res2["answer"]
    assert res2["evidence"][-1]["event_id"] == "REALTIME_TEST_002"

def test_combine_pathway_streams_regression():
    from src.main import combine_pathway_streams
    try:
        import pathway as pw
    except ImportError:
        from src.pathway_compat import pw

    # 1. Empty list error handling
    with pytest.raises(ValueError, match="No data streams provided"):
        combine_pathway_streams([])

    # 2. Single stream case returns stream directly
    t1 = pw.Table()
    res_single = combine_pathway_streams([t1])
    assert res_single is t1

    # 3. Multiple streams list combination
    t2 = pw.Table()
    t3 = pw.Table()
    res_multi = combine_pathway_streams([t1, t2, t3])
    assert res_multi is not None
    assert hasattr(res_multi, "select")


