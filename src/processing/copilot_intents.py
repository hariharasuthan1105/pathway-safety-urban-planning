"""
Lightweight Deterministic Intent Detection Engine for Phase 6 AI Urban Copilot.

Classifies incoming operator queries into explainable system intents to guide
context retrieval, recommendation generation, and dashboard UI action binding.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# System Intent Constants
INTENT_CITY_SUMMARY = "CITY_SUMMARY"
INTENT_RISK_EXPLANATION = "RISK_EXPLANATION"
INTENT_ZONE_ANALYSIS = "ZONE_ANALYSIS"
INTENT_EVENT_INVESTIGATION = "EVENT_INVESTIGATION"
INTENT_EVENT_COMPARISON = "EVENT_COMPARISON"
INTENT_TIME_WINDOW_ANALYSIS = "TIME_WINDOW_ANALYSIS"
INTENT_SOURCE_ANALYSIS = "SOURCE_ANALYSIS"
INTENT_EVIDENCE_LOOKUP = "EVIDENCE_LOOKUP"

INTENT_PATTERNS = [
    (INTENT_CITY_SUMMARY, r"(happening right now|summary|overview|status of the city|current situation)"),
    (INTENT_EVENT_COMPARISON, r"(compare|difference between|versus|vs|how has risk changed)"),
    (INTENT_RISK_EXPLANATION, r"(why is (the )?risk|why did (the )?risk|contributing factors|why is city risk)"),
    (INTENT_ZONE_ANALYSIS, r"(zone [a-d]|highest risk|which (area|zone)|why is zone|about zone)"),
    (INTENT_TIME_WINDOW_ANALYSIS, r"(last 15 minutes|15-minute|time window|recent 5 minutes|recent window)"),
    (INTENT_SOURCE_ANALYSIS, r"(multiple sources|data sources|active sources|which source|source corroboration)"),
    (INTENT_EVENT_INVESTIGATION, r"(incidents|events responsible|what happened|investigate first|action|should an operator)"),
    (INTENT_EVIDENCE_LOOKUP, r"(evidence|anomalies|rule violation|audit trail)")
]

def classify_intent(query: str) -> str:
    """
    Deterministically classifies operator query string into a system intent.
    Defaults to CITY_SUMMARY or RISK_EXPLANATION if unclassified.
    """
    if not query or not query.strip():
        return INTENT_CITY_SUMMARY

    q_lower = query.strip().lower()

    for intent, pattern in INTENT_PATTERNS:
        if re.search(pattern, q_lower):
            return intent

    return INTENT_RISK_EXPLANATION

def extract_referenced_zones(query: str, available_zones: List[str] = None) -> List[str]:
    """
    Extracts explicit or contextually referenced zone names from query string.
    """
    if not query:
        return []

    q_lower = query.lower()
    found_zones = []

    # Check for Zone A, Zone B, Zone C, Zone D keywords
    zone_map = {
        "zone a": "Zone A (Downtown)",
        "downtown": "Zone A (Downtown)",
        "zone b": "Zone B (Midtown)",
        "midtown": "Zone B (Midtown)",
        "zone c": "Zone C (Uptown)",
        "uptown": "Zone C (Uptown)",
        "zone d": "Zone D (Outer District)",
        "outer": "Zone D (Outer District)"
    }

    for key, full_name in zone_map.items():
        if key in q_lower and full_name not in found_zones:
            found_zones.append(full_name)

    return found_zones
