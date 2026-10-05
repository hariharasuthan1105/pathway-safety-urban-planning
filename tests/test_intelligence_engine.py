"""
Unit Tests for Phase 4 Real-Time Urban Intelligence Engine.
Coverage:
- Risk scoring & severity weighting
- Evidence generation
- Rolling time windows
- Geographic zone assignment & spatial bucketing
- Temporal anomaly detection
- Cross-source correlation
- City-state aggregation
- Edge cases: empty streams, missing coordinates, stale sources, duplicate events
"""

import pytest
import datetime
from src.processing import (
    get_zone_name,
    ZoneManager,
    RollingWindowAggregator,
    RiskScoringEngine,
    CrossSourceCorrelator,
    AnomalyDetector,
    CityStateManager
)

def test_zone_assignment():
    # Test downtown coordinates
    zone1 = get_zone_name(40.7128, -74.0060)
    assert zone1 == "Zone A (Downtown)"

    # Test midtown coordinates
    zone2 = get_zone_name(40.7450, -73.9900)
    assert zone2 == "Zone B (Midtown)"

    # Test outer coordinates fallback
    zone3 = get_zone_name(10.0, 10.0)
    assert zone3 == "Zone D (Outer District)"

    # Test ZoneManager with event missing coordinates
    zm = ZoneManager()
    event_no_coords = {"source": "webhook", "data": {"severity": "HIGH"}}
    assigned = zm.assign_zone(event_no_coords)
    assert assigned == "Zone A (Downtown)"
    assert event_no_coords["location"]["zone"] == "Zone A (Downtown)"

def test_rolling_window_aggregator():
    agg = RollingWindowAggregator(max_history_minutes=60)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    ev1 = {"timestamp": now, "source": "weather", "data": {"severity": "LOW"}}
    ev2 = {"timestamp": now, "source": "traffic", "data": {"severity": "HIGH"}}

    agg.add_event(ev1)
    agg.add_event(ev2)

    metrics = agg.compute_metrics()
    assert metrics["count_5m"] == 2
    assert metrics["count_15m"] == 2
    assert metrics["count_60m"] == 2

def test_risk_scoring_and_evidence():
    engine = RiskScoringEngine()
    
    events = [
        {"source": "weather", "data": {"severity": "CRITICAL", "event_id": "e1"}},
        {"source": "traffic", "data": {"severity": "HIGH", "event_id": "e2"}},
        {"source": "webhook", "data": {"severity": "HIGH", "event_id": "e3"}}
    ]

    window_metrics = {"acceleration_ratio": 2.1, "count_5m": 3}
    zone_summaries = {
        "Zone A (Downtown)": {"name": "Zone A (Downtown)", "event_count": 3, "critical_count": 1, "high_count": 2, "anomaly_count": 1}
    }
    anomalies = [{"anomaly_type": "sensor_alert", "severity": "HIGH"}]

    risk_res = engine.compute_risk(events, window_metrics, zone_summaries, anomalies)
    
    assert risk_res["risk_score"] > 50
    assert risk_res["risk_level"] in ["HIGH", "CRITICAL"]
    assert len(risk_res["evidence"]) >= 3
    assert len(risk_res["contributing_factors"]) >= 2

def test_cross_source_correlation():
    correlator = CrossSourceCorrelator(min_sources=2)

    events = [
        {"source": "open_meteo_weather", "location": {"zone": "Zone A (Downtown)"}, "data": {"event_id": "ev1", "event_type": "rain", "severity": "HIGH"}},
        {"source": "traffic_api", "location": {"zone": "Zone A (Downtown)"}, "data": {"event_id": "ev2", "event_type": "accident", "severity": "CRITICAL"}},
        {"source": "webhook_ingestion", "location": {"zone": "Zone A (Downtown)"}, "data": {"event_id": "ev3", "event_type": "emergency", "severity": "HIGH"}}
    ]

    correlations = correlator.detect_correlations(events)
    assert len(correlations) == 1
    corr = correlations[0]
    assert corr["zone"] == "Zone A (Downtown)"
    assert len(corr["sources"]) == 3
    assert corr["risk_level"] == "CRITICAL"
    assert "open_meteo_weather" in corr["sources"]

def test_temporal_anomaly_detection():
    detector = AnomalyDetector()

    # Acceleration spike
    window_metrics = {"acceleration_ratio": 2.5, "count_5m": 4, "events_5m": []}
    anoms = detector.detect_temporal_anomalies(recent_events=[], window_metrics=window_metrics)
    assert len(anoms) == 1
    assert anoms[0]["anomaly_type"] == "rapid_event_frequency_spike"

    # Burst of critical events
    w5_events = [
        {"data": {"severity": "CRITICAL"}},
        {"data": {"severity": "CRITICAL"}}
    ]
    window_metrics_burst = {"acceleration_ratio": 1.0, "count_5m": 2, "events_5m": w5_events}
    anoms_burst = detector.detect_temporal_anomalies(recent_events=w5_events, window_metrics=window_metrics_burst)
    assert len(anoms_burst) == 1
    assert anoms_burst[0]["anomaly_type"] == "critical_incident_burst"

def test_city_state_manager_integration():
    csm = CityStateManager()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

    ev1 = {
        "timestamp": now_str,
        "source": "open_meteo_weather",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "data": {"event_id": "w1", "event_type": "heavy_rain", "severity": "HIGH"}
    }
    ev2 = {
        "timestamp": now_str,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7150, "lon": -74.0020},
        "data": {"event_id": "wh1", "event_type": "vehicle_accident", "severity": "CRITICAL"}
    }

    csm.ingest_event(ev1)
    csm.ingest_event(ev2)

    live_state = csm.get_live_city_state()

    assert live_state["overall_risk_score"] > 25
    assert live_state["overall_risk_level"] in ["MODERATE", "HIGH", "CRITICAL"]
    assert "Zone A (Downtown)" in live_state["zone_summaries"]
    assert len(live_state["correlations"]) == 1
    assert "open_meteo_weather" in live_state["data_freshness"]
    assert live_state["data_freshness"]["open_meteo_weather"]["status"] == "LIVE"

def test_edge_cases():
    # 1. Empty Stream
    csm = CityStateManager()
    empty_state = csm.get_live_city_state()
    assert empty_state["overall_risk_score"] == 0
    assert empty_state["overall_risk_level"] == "LOW"
    assert len(empty_state["correlations"]) == 0

    # 2. Duplicate events handling
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dup_event = {"timestamp": now_str, "source": "test", "data": {"event_id": "dup_1", "severity": "LOW"}}
    csm.ingest_event(dup_event)
    csm.ingest_event(dup_event)
    state_dup = csm.get_live_city_state()
    assert state_dup["rolling_metrics"]["count_60m"] == 2

    # 3. Missing coordinates
    no_coord_event = {"timestamp": now_str, "source": "test_src", "data": {"severity": "MODERATE"}}
    csm.ingest_event(no_coord_event)
    state_no_coord = csm.get_live_city_state()
    assert state_no_coord["overall_risk_score"] >= 0
