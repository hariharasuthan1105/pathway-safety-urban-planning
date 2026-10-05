"""
Unified Live City State Engine for Phase 4.

Aggregates streaming events, rolling time windows, geographic zone intelligence,
deterministic risk scoring, temporal anomaly detection, cross-source correlation,
and source data freshness into a single real-time queryable state.
"""

import datetime
import logging
from typing import Dict, Any, List

from .zones import ZoneManager
from .rolling_windows import RollingWindowAggregator
from .risk_engine import RiskScoringEngine
from .correlation import CrossSourceCorrelator
from .anomaly_detection import AnomalyDetector

logger = logging.getLogger(__name__)

class CityStateManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.zone_manager = ZoneManager(self.config)
        self.rolling_aggregator = RollingWindowAggregator(max_history_minutes=60)
        self.risk_engine = RiskScoringEngine(self.config)
        self.correlator = CrossSourceCorrelator(time_window_minutes=15)
        self.anomaly_detector = AnomalyDetector(self.config)

        self.source_freshness: Dict[str, Dict[str, Any]] = {
            "open_meteo_weather": {"last_update": None, "status": "OFFLINE", "event_count": 0, "mode": "LIVE"},
            "open_meteo_air_quality": {"last_update": None, "status": "OFFLINE", "event_count": 0, "mode": "LIVE"},
            "webhook_ingestion": {"last_update": None, "status": "OFFLINE", "event_count": 0, "mode": "LIVE"},
            "simulation_generator": {"last_update": None, "status": "OFFLINE", "event_count": 0, "mode": "SIMULATION"}
        }
        self.intelligence_feed: List[Dict[str, Any]] = []

    def update_source_freshness(self, source_name: str, mode: str = "LIVE", status: str = "LIVE"):
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if source_name not in self.source_freshness:
            self.source_freshness[source_name] = {"last_update": now_str, "status": status, "event_count": 0, "mode": mode}
        
        entry = self.source_freshness[source_name]
        entry["last_update"] = now_str
        entry["status"] = status
        entry["mode"] = mode
        entry["event_count"] += 1

    def ingest_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests a single streaming event, assigns zone, updates rolling aggregator and source freshness.
        """
        if not isinstance(event, dict):
            return event

        # Ensure zone assignment
        self.zone_manager.assign_zone(event)
        
        # Track source freshness
        source = event.get("source", "unknown")
        data_mode = event.get("mode", "LIVE").upper()
        self.update_source_freshness(source_name=source, mode=data_mode, status="LIVE")

        # Process through anomaly UDF
        processed_event = self.anomaly_detector.process(event)

        # Add to rolling window history
        self.rolling_aggregator.add_event(processed_event)

        return processed_event

    def get_live_city_state(self) -> Dict[str, Any]:
        """
        Computes the complete, up-to-the-second Live City State.
        """
        recent_60m_events = self.rolling_aggregator.get_events_in_window(60)
        window_metrics = self.rolling_aggregator.compute_metrics()
        zone_summaries = self.zone_manager.summarize_zones(recent_60m_events)

        # Collect active anomalies from events & temporal anomaly detection
        active_anomalies = []
        for ev in recent_60m_events:
            if ev.get("anomaly", False) or (isinstance(ev.get("data"), dict) and ev.get("data", {}).get("anomaly", False)):
                data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
                active_anomalies.append({
                    "event_id": data.get("event_id", ev.get("event_id", "unk")),
                    "source": ev.get("source", "unknown"),
                    "zone": ev.get("location", {}).get("zone", "Zone A (Downtown)"),
                    "anomaly_type": ev.get("anomaly_type", data.get("anomaly_type", "sensor_alert")),
                    "description": ev.get("anomaly_description", data.get("anomaly_description", "Anomaly detected")),
                    "timestamp": ev.get("timestamp")
                })

        # Temporal anomaly detection
        temporal_anomalies = self.anomaly_detector.detect_temporal_anomalies(recent_60m_events, window_metrics)
        active_anomalies.extend(temporal_anomalies)

        # Cross-source correlation
        correlations = self.correlator.detect_correlations(recent_60m_events, zone_summaries)

        # Deterministic Risk Computation
        risk_result = self.risk_engine.compute_risk(
            recent_events=recent_60m_events,
            window_metrics=window_metrics,
            zone_summaries=zone_summaries,
            active_anomalies=active_anomalies
        )

        # Event counts by severity, source, and type
        counts_by_severity = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
        counts_by_source = {}
        counts_by_type = {}

        for ev in recent_60m_events:
            src = ev.get("source", "unknown")
            counts_by_source[src] = counts_by_source.get(src, 0) + 1

            data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
            sev = str(data.get("severity", ev.get("severity", "LOW"))).upper()
            if sev in counts_by_severity:
                counts_by_severity[sev] += 1
            else:
                counts_by_severity["LOW"] += 1

            ev_type = data.get("event_type", ev.get("event_type", "incident"))
            counts_by_type[ev_type] = counts_by_type.get(ev_type, 0) + 1

        # Evaluate Data Freshness (mark STALE if no events in last 10 mins)
        now = datetime.datetime.now(datetime.timezone.utc)
        freshness_report = {}
        for src, info in self.source_freshness.items():
            freshness_copy = dict(info)
            if freshness_copy["last_update"]:
                try:
                    last_dt = datetime.datetime.fromisoformat(freshness_copy["last_update"].replace("Z", "+00:00"))
                    if (now - last_dt).total_seconds() > 600:
                        freshness_copy["status"] = "STALE"
                except Exception:
                    pass
            freshness_report[src] = freshness_copy

        # Generate fresh intelligence feed alerts
        if risk_result["risk_level"] in ["HIGH", "CRITICAL"]:
            self._add_intelligence_alert(
                f"CITY RISK LEVEL IS {risk_result['risk_level']} (Score: {risk_result['risk_score']}/100)",
                "risk_alert"
            )
        for corr in correlations:
            self._add_intelligence_alert(corr["reason"], "cross_source_correlation")

        return {
            "overall_risk_score": risk_result["risk_score"],
            "overall_risk_level": risk_result["risk_level"],
            "risk_trend": risk_result["risk_trend"],
            "contributing_factors": risk_result["contributing_factors"],
            "evidence": risk_result["evidence"],
            "zone_summaries": zone_summaries,
            "recent_events": recent_60m_events[-20:],  # last 20 events
            "active_anomalies": active_anomalies,
            "correlations": correlations,
            "event_counts_by_severity": counts_by_severity,
            "event_counts_by_source": counts_by_source,
            "event_counts_by_type": counts_by_type,
            "rolling_metrics": {
                "count_5m": window_metrics.get("count_5m", 0),
                "count_15m": window_metrics.get("count_15m", 0),
                "count_30m": window_metrics.get("count_30m", 0),
                "count_60m": window_metrics.get("count_60m", 0),
                "acceleration_ratio": window_metrics.get("acceleration_ratio", 1.0)
            },
            "data_freshness": freshness_report,
            "intelligence_feed": self.intelligence_feed[-15:],
            "last_updated": now.isoformat()
        }

    def _add_intelligence_alert(self, msg: str, category: str):
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
        alert = {"time": now_str, "message": msg, "category": category}
        if not self.intelligence_feed or self.intelligence_feed[-1]["message"] != msg:
            self.intelligence_feed.append(alert)
