"""
Cross-Source Correlation Engine for Phase 4.

Correlates independent streaming data sources (e.g., weather + traffic + webhook)
occurring within close temporal and geographic proximity to produce compound risk signals.
"""

import uuid
import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CrossSourceCorrelator:
    def __init__(self, time_window_minutes: int = 15, min_sources: int = 2):
        self.time_window_minutes = time_window_minutes
        self.min_sources = min_sources

    def detect_correlations(self, events: List[Dict[str, Any]], zone_summaries: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Groups recent events by geographic zone and evaluates if multi-source clusters exist.
        Returns a list of structured CorrelationRecord objects.
        """
        if not events:
            return []

        # Group events by zone
        events_by_zone: Dict[str, List[Dict[str, Any]]] = {}
        for ev in events:
            loc = ev.get("location", {})
            zone_name = loc.get("zone", "Zone A (Downtown)") if isinstance(loc, dict) else "Zone A (Downtown)"
            if zone_name not in events_by_zone:
                events_by_zone[zone_name] = []
            events_by_zone[zone_name].append(ev)

        correlations: List[Dict[str, Any]] = []

        for zone_name, zone_events in events_by_zone.items():
            sources = set()
            critical_high_count = 0
            event_types = set()

            for ev in zone_events:
                sources.add(ev.get("source", "unknown"))
                data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
                sev = str(data.get("severity", ev.get("severity", "LOW"))).upper()
                if sev in ["CRITICAL", "HIGH"]:
                    critical_high_count += 1
                ev_type = data.get("event_type", ev.get("event_type", "incident"))
                event_types.add(ev_type)

            # Check if correlation threshold is satisfied (>= min_sources)
            if len(sources) >= self.min_sources:
                corr_id = f"corr_{uuid.uuid4().hex[:8]}"
                
                # Determine risk level of correlation
                if critical_high_count >= 2 or len(sources) >= 3:
                    risk_level = "CRITICAL"
                elif critical_high_count == 1:
                    risk_level = "HIGH"
                else:
                    risk_level = "MODERATE"

                source_list = sorted(list(sources))
                reason = f"Multi-source correlation detected: {len(zone_events)} events across sources [{', '.join(source_list)}] in {zone_name}."

                correlation_record = {
                    "correlation_id": corr_id,
                    "zone": zone_name,
                    "events": [ev.get("data", {}).get("event_id", ev.get("event_id", "unknown")) for ev in zone_events],
                    "sources": source_list,
                    "event_types": sorted(list(event_types)),
                    "event_count": len(zone_events),
                    "risk_level": risk_level,
                    "reason": reason,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                correlations.append(correlation_record)

        return correlations
