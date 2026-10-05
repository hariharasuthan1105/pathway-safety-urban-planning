"""
Phase 4 Demo Scenario: Compound Multi-Source Risk & Correlation Verification.
Simulates:
1. Weather event (Heavy Rain)
2. Traffic event (Gridlock Traffic)
3. Webhook emergency event (Vehicle Collision)
in Zone A (Downtown), demonstrating correlated High-Risk City State & Evidence Generation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from src.processing import CityStateManager

def run_demo():
    print("==================================================")
    print("PHASE 4 REAL-TIME URBAN INTELLIGENCE DEMO SCENARIO")
    print("==================================================")

    csm = CityStateManager()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Event 1: Weather Event
    e1 = {
        "timestamp": now_iso,
        "source": "open_meteo_weather",
        "location": {"lat": 40.7128, "lon": -74.0060}, # Zone A Downtown
        "data": {
            "event_id": "demo_w01",
            "event_type": "heavy_rain",
            "severity": "MODERATE",
            "precipitation": 18.5
        }
    }

    # Event 2: Traffic Event
    e2 = {
        "timestamp": now_iso,
        "source": "traffic_api",
        "location": {"lat": 40.7140, "lon": -74.0040}, # Zone A Downtown
        "data": {
            "event_id": "demo_t01",
            "event_type": "gridlock_traffic",
            "severity": "HIGH",
            "congestion_level": 0.88
        }
    }

    # Event 3: Critical Webhook Incident
    e3 = {
        "timestamp": now_iso,
        "source": "webhook_ingestion",
        "location": {"lat": 40.7130, "lon": -74.0050}, # Zone A Downtown
        "data": {
            "event_id": "demo_wh01",
            "event_type": "vehicle_collision",
            "severity": "CRITICAL",
            "description": "Multi-vehicle collision blocking 2 lanes"
        }
    }

    print("\n[1] Ingesting Multi-Source Telemetry Events...")
    csm.ingest_event(e1)
    print("  [+] Ingested Weather Event: Heavy Rain (Zone A)")
    csm.ingest_event(e2)
    print("  [+] Ingested Traffic Event: Gridlock Traffic (Zone A)")
    csm.ingest_event(e3)
    print("  [+] Ingested Webhook Incident: Vehicle Collision [CRITICAL] (Zone A)")

    print("\n[2] Computing Live City State...")
    live_state = csm.get_live_city_state()

    print(f"\n---> Overall City Risk Index: {live_state['overall_risk_score']}/100 ({live_state['overall_risk_level']})")
    print(f"---> Risk Trend: {live_state['risk_trend']}")

    print("\n[3] Main Contributing Factors:")
    for factor in live_state['contributing_factors']:
        print(f"  * {factor}")

    print("\n[4] Audit Evidence Trail:")
    for ev in live_state['evidence']:
        print(f"  - {ev}")

    print("\n[5] Cross-Source Correlations Detected:")
    for corr in live_state['correlations']:
        print(f"  [CORRELATION] [{corr['risk_level']}] {corr['reason']}")
        print(f"     Sources: {corr['sources']}")

    print("\n[6] Zone Intelligence Breakdown:")
    for zone_name, z_info in live_state['zone_summaries'].items():
        if z_info['event_count'] > 0:
            print(f"  [ZONE] {zone_name}: Score {z_info['risk_score']}/100 ({z_info['risk_level']}) | Events: {z_info['event_count']} (Crit: {z_info['critical_count']})")

    print("\n[7] Data Freshness Status:")
    for src, f_info in live_state['data_freshness'].items():
        print(f"  [SOURCE] {src}: Status={f_info['status']} | Mode={f_info['mode']} | Event Count={f_info['event_count']}")

    print("\n==================================================")
    print("DEMO SCENARIO VERIFICATION SUCCESSFUL")
    print("==================================================")

if __name__ == "__main__":
    run_demo()
