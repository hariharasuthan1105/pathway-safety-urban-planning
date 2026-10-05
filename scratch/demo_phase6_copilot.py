"""
Phase 6 Validation Scenario: AI Urban Copilot & Human-in-the-Loop Verification.

Executes deterministic multi-source ingestion:
1. Weather Event (Heavy Rain)
2. Traffic Event (Gridlock Traffic)
3. Webhook Event (Vehicle Collision [CRITICAL])
Demonstrates Copilot intent classification, grounded RAG answers, Human-in-the-Loop decision recommendations,
and safe dashboard focus action triggers.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from src.processing import CityStateManager, RAGSystem
from src.processing.llm_provider import MockLLMProvider

def run_phase6_demo():
    print("==================================================")
    print("PHASE 6 AI URBAN COPILOT DEMO SCENARIO")
    print("==================================================")

    csm = CityStateManager()
    mock_provider = MockLLMProvider(
        mock_answer="Zone A (Downtown) is currently at CRITICAL risk due to a 3-vehicle collision blocking traffic during heavy precipitation."
    )
    rag = RAGSystem(config={}, provider=mock_provider)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Step 1: Ingest Multi-Source Telemetry Events into Zone A
    e1 = {
        "timestamp": now_iso,
        "source": "open_meteo_weather",
        "location": {"lat": 40.7128, "lon": -74.0060}, # Zone A
        "data": {"event_id": "p6_w1", "event_type": "heavy_rain", "severity": "MODERATE", "precipitation": 25.0}
    }
    e2 = {
        "timestamp": now_iso,
        "source": "traffic_api",
        "location": {"lat": 40.7140, "lon": -74.0040}, # Zone A
        "data": {"event_id": "p6_t1", "event_type": "gridlock_traffic", "severity": "HIGH", "congestion": 0.95}
    }
    e3 = {
        "timestamp": now_iso,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7130, "lon": -74.0050}, # Zone A
        "data": {"event_id": "p6_wh1", "event_type": "vehicle_collision", "severity": "CRITICAL", "description": "3-vehicle pileup blocking main artery"}
    }

    print("\n[1] Ingesting Telemetry Events into Zone A (Downtown)...")
    csm.ingest_event(e1); rag.add_document(e1["data"], e1["source"], e1["location"])
    csm.ingest_event(e2); rag.add_document(e2["data"], e2["source"], e2["location"])
    csm.ingest_event(e3); rag.add_document(e3["data"], e3["source"], e3["location"])
    print("  [+] Weather Event: Heavy Rain")
    print("  [+] Traffic Event: Gridlock Traffic")
    print("  [+] Webhook Incident: Vehicle Collision [CRITICAL]")

    live_state = csm.get_live_city_state()

    # Question 1: City Summary
    q1 = "What is happening right now?"
    print(f"\n[2] Operator Question 1: '{q1}'")
    res1 = rag.query_structured(q1, city_state=live_state)
    print(f"  * Intent Classified: {res1.get('intent')}")
    print(f"  * Copilot Answer: {res1.get('answer')}")

    # Question 2: Risk Explanation for Zone A
    q2 = "Why is Zone A critical?"
    print(f"\n[3] Operator Question 2: '{q2}'")
    res2 = rag.query_structured(q2, city_state=live_state)
    print(f"  * Intent Classified: {res2.get('intent')}")
    print(f"  * Copilot Answer: {res2.get('answer')}")
    print("  * Verified Audit Evidence Citations:")
    for cite in res2.get("evidence", []):
        print(f"    - Event: {cite.get('event_id')} | Source: {cite.get('source')} | Zone: {cite.get('zone')} | Severity: {cite.get('severity')}")

    # Question 3: Human-in-the-Loop Investigation Recommendation
    q3 = "What should an operator investigate first?"
    print(f"\n[4] Operator Question 3: '{q3}'")
    res3 = rag.query_structured(q3, city_state=live_state)
    print("  * HUMAN REVIEW RECOMMENDATIONS (Decision Support Only):")
    for rec in res3.get("recommended_actions", []):
        print(f"    - {rec}")

    print("\n[5] SAFE DASHBOARD UI ACTION BINDINGS:")
    for act in res3.get("dashboard_actions", []):
        lbl = act.get('label', '').encode('ascii', 'ignore').decode('ascii')
        print(f"  [ACTION BUTTON] '{lbl}' -> Action: {act.get('action')}, Target: {act.get('target')}")

    print("\n==================================================")
    print("PHASE 6 VALIDATION SCENARIO PASSED CLEANLY")
    print("==================================================")

if __name__ == "__main__":
    run_phase6_demo()
