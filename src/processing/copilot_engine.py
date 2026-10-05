"""
AI Urban Copilot & Human-in-the-Loop Decision Support Engine for Phase 6.

Combines deterministic intent classification, live City State grounding,
strict Human-in-the-Loop recommendation generation, and dashboard UI action binding.
"""

import logging
from typing import Dict, Any, List, Optional

from .copilot_intents import (
    classify_intent,
    extract_referenced_zones,
    INTENT_CITY_SUMMARY,
    INTENT_RISK_EXPLANATION,
    INTENT_ZONE_ANALYSIS,
    INTENT_EVENT_INVESTIGATION,
    INTENT_EVENT_COMPARISON,
    INTENT_TIME_WINDOW_ANALYSIS,
    INTENT_SOURCE_ANALYSIS,
    INTENT_EVIDENCE_LOOKUP
)

logger = logging.getLogger(__name__)

SAFETY_DISCLAIMER_PREFIX = "[HUMAN REVIEW RECOMMENDATION]"

class CopilotEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate_human_recommendations(self, intent: str, city_state: Dict[str, Any], target_zones: List[str]) -> List[str]:
        """
        Generates strict Human-in-the-Loop review recommendations based on live telemetry.
        All statements use advisory language and explicit 'HUMAN REVIEW RECOMMENDATION' markers.
        """
        recs = []
        if not city_state:
            return [f"{SAFETY_DISCLAIMER_PREFIX} Verify data source connectivity and monitor baseline telemetry stream."]

        risk_level = city_state.get("overall_risk_level", "LOW")
        zone_summaries = city_state.get("zone_summaries", {})
        anomalies = city_state.get("active_anomalies", [])
        correlations = city_state.get("correlations", [])

        # High / Critical Risk Recommendations
        if risk_level in ["HIGH", "CRITICAL"]:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} Priority review recommended for overall city risk state ({risk_level}).")

        # Zone Specific Recommendations
        high_risk_zones = [z for z, info in zone_summaries.items() if info.get("risk_level") in ["HIGH", "CRITICAL"]]
        if high_risk_zones:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} Operator inspection advised for high-risk zones: {', '.join(high_risk_zones)}.")
        elif target_zones:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} Recommended to inspect telemetry feed for {', '.join(target_zones)}.")

        # Correlation & Anomaly Recommendations
        if correlations:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} Cross-source corroboration detected across multiple feeds; human evaluation suggested.")
        
        if anomalies:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} {len(anomalies)} active rule anomaly flags require operator review.")

        if not recs:
            recs.append(f"{SAFETY_DISCLAIMER_PREFIX} System operating within normal baseline parameters. Routine observation recommended.")

        return recs

    def build_dashboard_actions(self, intent: str, city_state: Dict[str, Any], target_zones: List[str]) -> List[Dict[str, Any]]:
        """
        Constructs safe, client-side dashboard state mutation actions (e.g. Focus Zone, View Related Events).
        """
        actions = []
        zone_summaries = city_state.get("zone_summaries", {}) if city_state else {}

        # Determine highest risk zone if no target zone specified
        hottest_zone = None
        max_score = -1
        for z_name, z_info in zone_summaries.items():
            if z_info.get("risk_score", 0) > max_score:
                max_score = z_info.get("risk_score", 0)
                hottest_zone = z_name

        primary_zone = target_zones[0] if target_zones else (hottest_zone or "Zone A (Downtown)")

        # Focus Zone Action
        actions.append({
            "action": "focus_zone",
            "label": f"📍 Focus Map on {primary_zone}",
            "target": primary_zone
        })

        # View Evidence Action
        actions.append({
            "action": "view_evidence",
            "label": f"🔍 View Incidents in {primary_zone}",
            "target": primary_zone
        })

        # View Time Window Analysis Action
        if intent in [INTENT_TIME_WINDOW_ANALYSIS, INTENT_RISK_EXPLANATION]:
            actions.append({
                "action": "view_time_window",
                "label": "⏱️ View 15-Minute Acceleration Trend",
                "target": 15
            })

        # Compare Zones Action
        if intent == INTENT_EVENT_COMPARISON or len(high_risk_zones := [z for z, info in zone_summaries.items() if info.get("event_count", 0) > 0]) >= 2:
            actions.append({
                "action": "compare_zones",
                "label": "📊 Compare High-Risk Zones",
                "target": high_risk_zones[:2] if len(high_risk_zones) >= 2 else ["Zone A (Downtown)", "Zone B (Midtown)"]
            })

        return actions

    def process_copilot_request(self, question: str, city_state: Dict[str, Any], raw_llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches raw LLM response with intent classification, Human-in-the-Loop recommendations,
        and safe dashboard focus actions.
        """
        intent = classify_intent(question)
        target_zones = extract_referenced_zones(question)

        # Generate Human-in-the-Loop recommendations
        recommendations = self.generate_human_recommendations(intent, city_state, target_zones)
        dashboard_actions = self.build_dashboard_actions(intent, city_state, target_zones)

        # Merge into final Copilot structured response
        response = dict(raw_llm_response)
        response["intent"] = intent
        response["risk_score"] = city_state.get("overall_risk_score", 0) if city_state else 0
        response["recommended_actions"] = recommendations
        response["dashboard_actions"] = dashboard_actions

        # Sanitize against unauthorized autonomous claims
        ans = response.get("answer", "")
        import re
        ans = re.sub(r"(dispatched [a-z ]+|contacted [a-z ]+|changed traffic signals|executed order)", "[advisory note: recommendation subject to human review]", ans, flags=re.IGNORECASE)
        response["answer"] = ans

        return response
