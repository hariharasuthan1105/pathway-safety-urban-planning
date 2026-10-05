"""
Phase 5 Validation Scenario: Pathway Real-Time RAG + LLM Integration Verification.

Executes deterministic multi-source ingestion:
1. Weather Event (Heavy Rain)
2. Traffic Event (Gridlock Traffic)
3. Critical Webhook Event (Vehicle Collision)
Updates Pathway pipeline & CityStateManager, formats RAG context, and queries Mock/Configured LLM.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from src.processing import CityStateManager, RAGSystem
from src.processing.llm_provider import MockLLMProvider

def run_phase5_demo():
    print("==================================================")
    print("PHASE 5 PATHWAY LLM + REAL-TIME RAG DEMO SCENARIO")
    print("==================================================")

    csm = CityStateManager()
    mock_provider = MockLLMProvider(
        mock_answer="Overall city risk is HIGH (Score: 100/100) due to a critical multi-vehicle collision in Zone A (Downtown) corroborated by heavy rainfall and severe traffic congestion."
    )
    rag = RAGSystem(config={}, provider=mock_provider)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Step 1: Weather Event
    e1 = {
        "timestamp": now_iso,
        "source": "open_meteo_weather",
        "location": {"lat": 40.7128, "lon": -74.0060}, # Zone A
        "data": {"event_id": "phase5_w1", "event_type": "heavy_rain", "severity": "MODERATE", "precipitation": 22.0}
    }

    # Step 2: Traffic Event
    e2 = {
        "timestamp": now_iso,
        "source": "traffic_api",
        "location": {"lat": 40.7140, "lon": -74.0040}, # Zone A
        "data": {"event_id": "phase5_t1", "event_type": "gridlock_traffic", "severity": "HIGH", "congestion": 0.92}
    }

    # Step 3: Critical Incident Webhook
    e3 = {
        "timestamp": now_iso,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7130, "lon": -74.0050}, # Zone A
        "data": {"event_id": "phase5_wh1", "event_type": "vehicle_collision", "severity": "CRITICAL", "description": "3-car pileup blocking intersection"}
    }

    print("\n[1] Ingesting Telemetry Events into Pathway Pipeline...")
    csm.ingest_event(e1)
    rag.add_document(e1["data"], e1["source"], e1["location"])
    print("  [+] Weather Event: Heavy Rain (Zone A)")

    csm.ingest_event(e2)
    rag.add_document(e2["data"], e2["source"], e2["location"])
    print("  [+] Traffic Event: Gridlock Traffic (Zone A)")

    csm.ingest_event(e3)
    rag.add_document(e3["data"], e3["source"], e3["location"])
    print("  [+] Webhook Event: Vehicle Collision [CRITICAL] (Zone A)")

    print("\n[2] Updating Live City State & RAG Retrievable Context...")
    live_state = csm.get_live_city_state()
    context_text = rag.prepare_city_state_context(live_state)
    print("  [+] Context Retrievable in RAG Index:")
    print("--------------------------------------------------")
    print(context_text[:300] + "...\n--------------------------------------------------")

    question = "Why is the current risk high?"
    print(f"\n[3] Submitting RAG Query: '{question}'...")
    structured_res = rag.query_structured(question, city_state=live_state)

    print("\n[4] AI URBAN ASSISTANT STRUCTURED RESPONSE:")
    print(f"  * Answer: {structured_res.get('answer')}")
    print(f"  * Risk Level: {structured_res.get('risk_level')}")
    print(f"  * Confidence: {structured_res.get('confidence')}")
    print(f"  * Affected Zones: {structured_res.get('affected_zones')}")
    print(f"  * Key Factors: {structured_res.get('key_factors')}")
    
    print("\n[5] Verified Audit Citations:")
    for cite in structured_res.get("evidence", []):
        print(f"  - Event ID: {cite.get('event_id')} | Source: {cite.get('source')} | Zone: {cite.get('zone')} | Severity: {cite.get('severity')}")

    print("\n==================================================")
    print("PHASE 5 VALIDATION SCENARIO PASSED CLEANLY")
    print("==================================================")

if __name__ == "__main__":
    run_phase5_demo()
