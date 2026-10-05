"""
Deterministic Risk Scoring Engine & Evidence Generator for Phase 4.

Calculates a transparent 0-100 city risk score and generates an audit trail
of evidence explaining the exact contributing factors.

Formula:
  Risk Score = min(100, max(0, BaseSeverityPoints + RecencyBoost + SpatialDensityBoost + SourceDiversityBoost + AccelerationBoost + AnomalyBoost))

Risk Ranges:
  0 - 25:   LOW
  26 - 50:  MODERATE
  51 - 75:  HIGH
  76 - 100: CRITICAL
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MODERATE": 8,
    "LOW": 2
}

class RiskScoringEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.high_threshold = self.config.get("RISK_HIGH_THRESHOLD", 50)
        self.critical_threshold = self.config.get("RISK_CRITICAL_THRESHOLD", 75)

    def compute_risk(self,
                     recent_events: List[Dict[str, Any]],
                     window_metrics: Dict[str, Any],
                     zone_summaries: Dict[str, Dict[str, Any]],
                     active_anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes deterministic city-wide risk score (0-100), risk level,
        risk trend, and structured evidence explanations.
        """
        if not recent_events and not active_anomalies:
            return {
                "risk_score": 0,
                "risk_level": "LOW",
                "risk_trend": "STABLE",
                "contributing_factors": ["No recent incidents recorded."],
                "evidence": ["0 events in last 60 minutes.", "No active anomalies detected."]
            }

        evidence: List[str] = []
        factors: List[str] = []

        # 1. Base Severity Points
        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
        sources = set()
        
        for ev in recent_events:
            data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
            sev = str(data.get("severity", ev.get("severity", "LOW"))).upper()
            sev_counts[sev] = sev_counts.get(sev, 0) + 1
            sources.add(ev.get("source", "unknown"))

        base_score = (
            sev_counts["CRITICAL"] * SEVERITY_WEIGHTS["CRITICAL"] +
            sev_counts["HIGH"] * SEVERITY_WEIGHTS["HIGH"] +
            sev_counts["MODERATE"] * SEVERITY_WEIGHTS["MODERATE"] +
            sev_counts["LOW"] * SEVERITY_WEIGHTS["LOW"]
        )

        evidence.append(f"Recorded {len(recent_events)} events in window (Critical: {sev_counts['CRITICAL']}, High: {sev_counts['HIGH']}, Moderate: {sev_counts['MODERATE']}).")
        if sev_counts["CRITICAL"] > 0:
            factors.append(f"{sev_counts['CRITICAL']} critical-severity incident(s)")
        if sev_counts["HIGH"] > 0:
            factors.append(f"{sev_counts['HIGH']} high-severity incident(s)")

        # 2. Source Diversity Boost
        source_boost = 0
        num_sources = len(sources)
        if num_sources >= 3:
            source_boost = 15
            factors.append(f"Cross-source corroboration across {num_sources} distinct sources ({', '.join(sorted(sources))})")
            evidence.append(f"Multi-source corroboration bonus applied (+15 pts) for {num_sources} distinct sources.")
        elif num_sources == 2:
            source_boost = 8
            factors.append(f"Events corroborated by {num_sources} sources ({', '.join(sorted(sources))})")
            evidence.append(f"Dual-source corroboration bonus applied (+8 pts).")

        # 3. Spatial Density / High-Risk Zone Concentration
        zone_boost = 0
        max_zone_events = 0
        hottest_zone = None
        for z_name, z_info in zone_summaries.items():
            ev_count = z_info.get("event_count", 0)
            if ev_count > max_zone_events:
                max_zone_events = ev_count
                hottest_zone = z_name

        if max_zone_events >= 3 and hottest_zone:
            zone_boost = 15
            factors.append(f"High spatial event density in {hottest_zone} ({max_zone_events} events)")
            evidence.append(f"Spatial concentration bonus (+15 pts) due to {max_zone_events} events in {hottest_zone}.")

        # 4. Rate of Change / Temporal Acceleration Boost
        acceleration_boost = 0
        accel_ratio = window_metrics.get("acceleration_ratio", 1.0)
        if accel_ratio >= 1.8:
            acceleration_boost = 15
            factors.append(f"Rapid event spike ({int(accel_ratio * 100)}% increase over 15m baseline)")
            evidence.append(f"Temporal acceleration bonus (+15 pts) for 5m rate acceleration ({accel_ratio:.1f}x).")
        elif accel_ratio >= 1.3:
            acceleration_boost = 8
            factors.append(f"Accelerating event rate ({int(accel_ratio * 100)}% of baseline)")
            evidence.append(f"Moderate acceleration bonus (+8 pts) for event rate increase ({accel_ratio:.1f}x).")

        # 5. Anomaly Boost
        anomaly_boost = 0
        if active_anomalies:
            anomaly_boost = len(active_anomalies) * 10
            factors.append(f"{len(active_anomalies)} active operational anomalies detected")
            evidence.append(f"Active anomalies penalty (+{anomaly_boost} pts) for {len(active_anomalies)} anomalies.")

        # Compute Total Normalized Score
        total_score = base_score + source_boost + zone_boost + acceleration_boost + anomaly_boost
        final_score = int(min(100, max(0, total_score)))

        # Determine Level
        if final_score >= self.critical_threshold:
            level = "CRITICAL"
        elif final_score >= self.high_threshold:
            level = "HIGH"
        elif final_score > 25:
            level = "MODERATE"
        else:
            level = "LOW"

        # Determine Trend
        if accel_ratio > 1.2 or sev_counts["CRITICAL"] > 0:
            trend = "INCREASING"
        elif accel_ratio < 0.8:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        return {
            "risk_score": final_score,
            "risk_level": level,
            "risk_trend": trend,
            "contributing_factors": factors or ["Normal baseline activity."],
            "evidence": evidence
        }
