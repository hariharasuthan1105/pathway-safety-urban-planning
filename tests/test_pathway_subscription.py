"""
Regression tests for Pathway subscription callback signature compatibility (Pathway 0.33.0)
and actual non-empty stream execution with pw.run().
"""

import time
import pytest

from src.main import make_pathway_sink
from src.data_sources.base import GeneratorConnectorSubject
from src.processing.shared_state import (
    get_shared_city_state_manager,
    get_shared_rag_system,
    reset_shared_state,
)

try:
    import pathway as pw
except ImportError:
    from src.pathway_compat import pw


@pytest.fixture(autouse=True)
def clean_state():
    reset_shared_state()
    if hasattr(pw, "_active_streams"):
        pw._active_streams.clear()
    yield
    reset_shared_state()
    if hasattr(pw, "_active_streams"):
        pw._active_streams.clear()


def test_pathway_sink_signature_compatibility():
    """
    Verifies that the Pathway sink callback correctly accepts:
    1. Native Pathway 0.33.0 keyword arguments: (key=..., row=..., time=..., is_addition=...)
    2. Native Pathway 0.33.0 positional arguments: (key, row, time, is_addition)
    3. Retraction/deletion events (is_addition=False) which must not be ingested
    4. Legacy single positional argument: (row,)
    5. Arbitrary extra keyword arguments without raising TypeError
    """
    config = {
        "mode": "public_safety",
        "city_bounds": {"name": "Chennai", "center_lat": 13.0827, "center_lon": 80.2707, "radius_km": 25.0},
    }
    sink = make_pathway_sink(config)
    mgr = get_shared_city_state_manager(config)

    # 1. Native Pathway 0.33.0 keyword invocation (the exact cause of Render's unexpected keyword argument 'key' error)
    ev_kw = {
        "timestamp": "2026-10-12T07:30:00Z",
        "source": "traffic_cameras",
        "data": {"event_id": "SINK_KW_001", "traffic_flow": 0.9, "status": "severe_gridlock"},
        "location": {"lat": 13.08, "lon": 80.27},
    }
    sink(key="item_key_001", row=ev_kw, time=1760000000, is_addition=True)

    state = mgr.get_live_city_state()
    recent = state.get("recent_events", [])
    assert any(e.get("data", {}).get("event_id") == "SINK_KW_001" for e in recent), (
        "Event with keyword arguments should be ingested into CityStateManager"
    )

    # 2. Native Pathway positional invocation: (key, row, time, is_addition)
    ev_pos = {
        "timestamp": "2026-10-12T07:31:00Z",
        "source": "emergency_calls",
        "data": {"event_id": "SINK_POS_002", "call_type": "fire_alarm"},
        "location": {"lat": 13.05, "lon": 80.25},
    }
    sink("item_key_002", ev_pos, 1760000010, True)
    state = mgr.get_live_city_state()
    assert any(e.get("data", {}).get("event_id") == "SINK_POS_002" for e in state["recent_events"])

    # 3. Pathway deletion event (is_addition=False) - must NOT be ingested
    ev_del = {
        "timestamp": "2026-10-12T07:32:00Z",
        "source": "emergency_calls",
        "data": {"event_id": "SINK_DEL_003"},
        "location": {"lat": 13.05, "lon": 80.25},
    }
    sink(key="item_key_003", row=ev_del, time=1760000020, is_addition=False)
    state = mgr.get_live_city_state()
    assert not any(e.get("data", {}).get("event_id") == "SINK_DEL_003" for e in state["recent_events"]), (
        "Deletion event should not be ingested"
    )

    # 4. Legacy single positional argument (row)
    ev_single = {
        "timestamp": "2026-10-12T07:33:00Z",
        "source": "weather_stations",
        "data": {"event_id": "SINK_LEGACY_004", "temperature": 34.5},
        "location": {"lat": 13.08, "lon": 80.27},
    }
    sink(ev_single)
    state = mgr.get_live_city_state()
    assert any(e.get("data", {}).get("event_id") == "SINK_LEGACY_004" for e in state["recent_events"])

    # 5. Future-proof extra kwargs
    ev_extra = {
        "timestamp": "2026-10-12T07:34:00Z",
        "source": "iot_sensors",
        "data": {"event_id": "SINK_EXTRA_005", "aqi": 180},
        "location": {"lat": 13.08, "lon": 80.27},
    }
    sink(key="item_key_005", row=ev_extra, time=1760000030, is_addition=True, partition=0, engine_id="pw-1")
    state = mgr.get_live_city_state()
    assert any(e.get("data", {}).get("event_id") == "SINK_EXTRA_005" for e in state["recent_events"])


def test_pathway_stream_execution_with_pw_run_and_subscription():
    """
    Task 2 Regression Test:
    Executes an actual, non-empty Pathway stream using pw.run() and verifies that
    the subscription callback successfully receives and processes the streamed event.
    """
    config = {
        "mode": "public_safety",
        "city_bounds": {"name": "Chennai", "center_lat": 13.0827, "center_lon": 80.2707, "radius_km": 25.0},
    }
    mgr = get_shared_city_state_manager(config)
    rag = get_shared_rag_system(config)

    # 1. Non-empty streaming event generator
    def sample_event_stream():
        yield {
            "timestamp": "2026-10-12T07:35:00Z",
            "source": "traffic_cameras",
            "data": {
                "event_id": "PW_STREAM_EXEC_001",
                "traffic_flow": 0.15,
                "congestion_level": "CRITICAL",
                "anomaly": True,
                "description": "Severe arterial blockage on Anna Salai Corridor",
            },
            "location": {"lat": 13.0600, "lon": 80.2500, "city": "Chennai"},
        }

    class EventSchema(pw.Schema):
        timestamp: str
        source: str
        data: pw.Json
        location: pw.Json

    # 2. Build ConnectorSubject and Pathway Table
    subject = GeneratorConnectorSubject(sample_event_stream)
    stream = pw.io.python.read(subject, schema=EventSchema)

    # 3. Transform / select
    processed = stream.select(
        timestamp=stream.timestamp,
        source=stream.source,
        data=stream.data,
        location=stream.location,
    )

    # 4. Attach subscription callback using standard Pathway API
    received_in_callback = []

    def custom_sink(key=None, row=None, time=None, is_addition=True, *args, **kwargs):
        # Resolve row whether passed as kwargs, positional, or single arg
        if row is None and isinstance(key, dict):
            r = key
        elif row is not None:
            r = row
        else:
            r = kwargs.get("row", key)
        if is_addition:
            received_in_callback.append(r)

    production_sink = make_pathway_sink(config)

    if hasattr(pw.io, "subscribe"):
        pw.io.subscribe(processed, custom_sink)
        pw.io.subscribe(processed, production_sink)
    elif hasattr(processed, "subscribe"):
        processed.subscribe(custom_sink)
        processed.subscribe(production_sink)

    # 5. Execute stream using pw.run()
    pw.run()

    # Allow streaming background threads to process
    time.sleep(0.5)

    # 6. Verify callback received and processed the event
    assert len(received_in_callback) > 0, "Subscription callback must receive at least one event from pw.run()"
    first_received = received_in_callback[0]
    assert first_received.get("source") == "traffic_cameras"
    assert first_received.get("data", {}).get("event_id") == "PW_STREAM_EXEC_001"

    # 7. Verify production sink updated shared CityStateManager
    live_state = mgr.get_live_city_state()
    recent = live_state.get("recent_events", [])
    assert any(e.get("data", {}).get("event_id") == "PW_STREAM_EXEC_001" for e in recent), (
        "pw.run() stream must propagate event to shared CityStateManager"
    )

    # 8. Verify RAG system received document
    assert len(rag.documents) > 0
    assert any(doc.get("data", {}).get("event_id") == "PW_STREAM_EXEC_001" for doc in rag.documents)


def test_pathway_compat_multiple_subscriber_signatures():
    """
    Verifies pathway_compat Table.subscribe handles both 4-argument and 1-argument callbacks
    without raising TypeError.
    """
    from src.pathway_compat import Table

    tbl = Table()

    # 4-argument callback (Pathway 0.33.0 standard)
    events_4arg = []
    def sub_4arg(key, row, time, is_addition):
        events_4arg.append((key, row, time, is_addition))

    # 1-argument callback (Legacy)
    events_1arg = []
    def sub_1arg(row):
        events_1arg.append(row)

    tbl.subscribe(sub_4arg)
    tbl.subscribe(sub_1arg)

    test_row = {"id": "ROW_01", "source": "sensors", "value": 42}
    tbl.publish(test_row)

    assert len(events_4arg) == 1
    assert events_4arg[0][0] == "ROW_01"
    assert events_4arg[0][1] == test_row
    assert events_4arg[0][3] is True

    assert len(events_1arg) == 1
    assert events_1arg[0] == test_row
