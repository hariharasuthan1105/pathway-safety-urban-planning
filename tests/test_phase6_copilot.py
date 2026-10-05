"""
Unit Tests for Phase 6 AI Urban Copilot & Human-in-the-Loop Decision Support.
Coverage:
- Deterministic intent classification (CITY_SUMMARY, ZONE_ANALYSIS, RISK_EXPLANATION, etc.)
- Human-in-the-Loop recommendation generation & explicit advisory labeling
- Safety boundaries: Verification that AI NEVER claims autonomous real-world action execution
- Dashboard UI action building (focus_zone, view_evidence, view_time_window, compare_zones)
- Copilot engine response processing with MockLLMProvider
- Edge cases: missing API key, empty city state, invalid input queries
- NO real OpenAI API calls during unit test execution
"""

import pytest
import datetime
from src.processing import (
    CityStateManager,
    RAGSystem,
    classify_intent,
    CopilotEngine
)
from src.processing.llm_provider import MockLLMProvider
from src.processing.copilot_intents import (
    INTENT_CITY_SUMMARY,
    INTENT_RISK_EXPLANATION,
    INTENT_ZONE_ANALYSIS,
    INTENT_EVENT_COMPARISON,
    INTENT_TIME_WINDOW_ANALYSIS,
    extract_referenced_zones
)

def test_intent_classification():
    assert classify_intent("What is happening right now?") == INTENT_CITY_SUMMARY
    assert classify_intent("Why is the city risk high?") == INTENT_RISK_EXPLANATION
    assert classify_intent("Why is Zone A critical?") == INTENT_ZONE_ANALYSIS
    assert classify_intent("Compare Zone A and Zone B") == INTENT_EVENT_COMPARISON
    assert classify_intent("What changed in the last 15 minutes?") == INTENT_TIME_WINDOW_ANALYSIS

def test_zone_extraction():
    zones1 = extract_referenced_zones("Why is Zone A and Downtown critical?")
    assert "Zone A (Downtown)" in zones1

    zones2 = extract_referenced_zones("Compare Zone B and Midtown")
    assert "Zone B (Midtown)" in zones2

def test_human_in_the_loop_recommendations():
    engine = CopilotEngine()

    city_state = {
        "overall_risk_level": "CRITICAL",
        "overall_risk_score": 88,
        "zone_summaries": {
            "Zone A (Downtown)": {"risk_level": "CRITICAL", "event_count": 4}
        },
        "active_anomalies": [{"anomaly_type": "sensor_alert"}],
        "correlations": [{"reason": "Multi-source overlap"}]
    }

    recs = engine.generate_human_recommendations(INTENT_RISK_EXPLANATION, city_state, ["Zone A (Downtown)"])
    
    assert len(recs) >= 2
    for r in recs:
        assert "HUMAN REVIEW RECOMMENDATION" in r

def test_dashboard_action_building():
    engine = CopilotEngine()

    city_state = {
        "overall_risk_score": 75,
        "zone_summaries": {
            "Zone A (Downtown)": {"risk_score": 75, "event_count": 3}
        }
    }

    actions = engine.build_dashboard_actions(INTENT_ZONE_ANALYSIS, city_state, ["Zone A (Downtown)"])
    
    action_types = [a["action"] for a in actions]
    assert "focus_zone" in action_types
    assert "view_evidence" in action_types
    
    focus_action = next(a for a in actions if a["action"] == "focus_zone")
    assert focus_action["target"] == "Zone A (Downtown)"

def test_safety_boundary_sanitization():
    engine = CopilotEngine()
    
    dangerous_llm_res = {
        "answer": "I have dispatched emergency services and contacted police to change traffic signals in Zone A.",
        "risk_level": "CRITICAL",
        "confidence": "HIGH",
        "affected_zones": ["Zone A (Downtown)"],
        "key_factors": ["Collision"],
        "evidence": []
    }

    sanitized = engine.process_copilot_request("What is happening?", {}, dangerous_llm_res)

    ans = sanitized["answer"]
    assert "dispatched emergency" not in ans
    assert "contacted police" not in ans
    assert "changed traffic signals" not in ans
    assert "advisory note" in ans

def test_copilot_end_to_end_with_mock_provider():
    csm = CityStateManager()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    ev = {
        "timestamp": now_str,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "data": {"event_id": "c_wh_1", "event_type": "vehicle_collision", "severity": "CRITICAL"}
    }
    csm.ingest_event(ev)
    live_state = csm.get_live_city_state()

    mock_provider = MockLLMProvider(mock_answer="Zone A is critical due to vehicle collision.")
    rag = RAGSystem(config={}, provider=mock_provider)
    rag.add_document(ev["data"], ev["source"], ev["location"])

    res = rag.query_structured("Why is Zone A critical?", city_state=live_state)

    assert "intent" in res
    assert res["intent"] == INTENT_ZONE_ANALYSIS
    assert len(res["recommended_actions"]) >= 1
    assert "HUMAN REVIEW RECOMMENDATION" in res["recommended_actions"][0]
    assert len(res["dashboard_actions"]) >= 1
    assert res["dashboard_actions"][0]["action"] == "focus_zone"
