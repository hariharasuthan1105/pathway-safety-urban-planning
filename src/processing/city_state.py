"""
Unified Live City State Engine for Phase 4.

Aggregates streaming events, rolling time windows, geographic zone intelligence,
deterministic risk scoring, temporal anomaly detection, cross-source correlation,
and source data freshness into a single real-time queryable state.
"""

import datetime
import os
import logging
import threading
from functools import wraps
from typing import Dict, Any, List, Optional

from .zones import ZoneManager
from .rolling_windows import RollingWindowAggregator
from .risk_engine import RiskScoringEngine
from .correlation import CrossSourceCorrelator
from .anomaly_detection import AnomalyDetector

logger = logging.getLogger(__name__)

def is_status_notice(event):
    data = event.get("data", {})
    if not isinstance(data, dict):
        data = {}
    kind = data.get("event_type", event.get("event_type"))
    return kind in {"transit_status", "transit_feed_update", "connector_status"} or data.get("record_kind") == "connector_status"


def synchronized(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return locked

class CityStateManager:
    def __init__(self, config: Dict[str, Any] = None):
        self._lock = threading.RLock()
        self.config = config or {}
        self.zone_manager = ZoneManager(self.config)
        self.rolling_aggregator = RollingWindowAggregator(max_history_minutes=60)
        self.risk_engine = RiskScoringEngine(self.config)
        self.correlator = CrossSourceCorrelator(time_window_minutes=15)
        self.anomaly_detector = AnomalyDetector(self.config)

        feed_url = (self.config.get("data_sources", {}).get("transit", {}).get("feed_url") or os.getenv("GTFS_FEED_URL") or "").strip()
        self.source_freshness: Dict[str, Dict[str, Any]] = {
            "weather_api": {
                "source_id": "weather_api", "mode": "LIVE", "connector_status": "WAITING",
                "observation_status": "WAITING", "status": "WAITING", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            },
            "air_quality_api": {
                "source_id": "air_quality_api", "mode": "LIVE", "connector_status": "WAITING",
                "observation_status": "WAITING", "status": "WAITING", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            },
            "traffic_simulation": {
                "source_id": "traffic_simulation", "mode": "SIMULATED", "connector_status": "WAITING",
                "observation_status": "WAITING", "status": "WAITING", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            },
            "webhook_ingestion": {
                "source_id": "webhook_ingestion", "mode": "EVENT_DRIVEN", "connector_status": "READY",
                "observation_status": "WAITING", "status": "WAITING", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            },
            "gtfs_transit_api": {
                "source_id": "gtfs_transit_api", "mode": "LIVE" if feed_url else "NOT_CONFIGURED",
                "connector_status": "WAITING" if feed_url else "NOT_CONFIGURED",
                "observation_status": "WAITING" if feed_url else "NOT_CONFIGURED",
                "status": "WAITING" if feed_url else "NOT_CONFIGURED", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            },
            "simulation_generator": {
                "source_id": "simulation_generator", "mode": "SIMULATED", "connector_status": "WAITING",
                "observation_status": "WAITING", "status": "WAITING", "last_update": None,
                "observed_at": None, "received_at": None, "last_checked_at": None,
                "event_count": 0, "freshness_age_seconds": None, "error_code": None
            }
        }
        self.intelligence_feed: List[Dict[str, Any]] = []

    def update_source_freshness(self, source_name: str, mode: str = "LIVE", status: str = "LIVE",
                                observed_at: Optional[str] = None, received_at: Optional[str] = None,
                                last_checked_at: Optional[str] = None, error_code: Optional[str] = None):
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if source_name not in self.source_freshness:
            self.source_freshness[source_name] = {
                "source_id": source_name,
                "mode": mode,
                "connector_status": status,
                "observation_status": status,
                "status": status,
                "last_update": now_str,
                "observed_at": observed_at or now_str,
                "received_at": received_at or now_str,
                "last_checked_at": last_checked_at or now_str,
                "event_count": 0,
                "freshness_age_seconds": 0,
                "error_code": error_code
            }

        entry = self.source_freshness[source_name]
        entry["last_update"] = now_str
        entry["status"] = status
        entry["observation_status"] = status
        entry["mode"] = mode
        if observed_at:
            entry["observed_at"] = observed_at
        if received_at:
            entry["received_at"] = received_at
        if last_checked_at:
            entry["last_checked_at"] = last_checked_at
        if error_code is not None:
            entry["error_code"] = error_code
        entry["event_count"] += 1

    @synchronized
    def ingest_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests a single streaming event, assigns zone, updates rolling aggregator and source freshness.
        """
        if not isinstance(event, dict):
            return event

        if is_status_notice(event):
            return event

        # Ensure zone assignment
        self.zone_manager.assign_zone(event)
        
        # Track source freshness
        source = event.get("source", "unknown")
        simulated_sources = {"traffic_simulation", "twitter", "police_scanner", "city_sensors",
                             "simulation_generator", "transit_simulation",
                             "planning_traffic_simulation", "environment_simulation"}
        if source in simulated_sources:
            if isinstance(event.get("data"), dict):
                event["data"]["mode"] = "SIMULATED"
            data_mode = "SIMULATED"
        else:
            data_mode = event.get("mode", event.get("data", {}).get("mode", "LIVE")).upper()

        data_dict = event.get("data", {}) if isinstance(event.get("data"), dict) else {}
        obs_time = data_dict.get("observed_at") or event.get("timestamp")
        recv_time = data_dict.get("received_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.update_source_freshness(source_name=source, mode=data_mode, status="LIVE",
                                    observed_at=obs_time, received_at=recv_time)

        # Process through anomaly UDF
        processed_event = self.anomaly_detector.process(event)

        # Add to rolling window history
        self.rolling_aggregator.add_event(processed_event)

        return processed_event

    @synchronized
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

        # Compute per-city summaries across South India cities
        try:
            from ..data_sources.real_sources import SOUTH_INDIA_CITIES
            city_summaries = {}
            for c in SOUTH_INDIA_CITIES:
                c_name = c["city"]
                city_summaries[c_name] = {
                    "city": c_name,
                    "state": c["state"],
                    "lat": c["lat"],
                    "lon": c["lon"],
                    "event_count": 0,
                    "critical_count": 0,
                    "high_count": 0,
                    "anomaly_count": 0,
                    "weather": None,
                    "air_quality": None,
                    "risk_score": 0,
                    "risk_level": "LOW"
                }

            for ev in recent_60m_events:
                data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
                c_name = data.get("city")
                if not c_name:
                    loc = ev.get("location", {})
                    lat, lon = loc.get("lat"), loc.get("lon")
                    if lat is not None and lon is not None:
                        best_city, min_dist = None, 999.0
                        for c in SOUTH_INDIA_CITIES:
                            dist = abs(c["lat"] - lat) + abs(c["lon"] - lon)
                            if dist < min_dist:
                                min_dist = dist
                                best_city = c["city"]
                        if min_dist < 0.5:
                            c_name = best_city

                if c_name and c_name in city_summaries:
                    cs = city_summaries[c_name]
                    cs["event_count"] += 1
                    sev = str(data.get("severity", ev.get("severity", "LOW"))).upper()
                    if sev == "CRITICAL": cs["critical_count"] += 1
                    elif sev == "HIGH": cs["high_count"] += 1
                    if data.get("anomaly", False): cs["anomaly_count"] += 1

                    if ev.get("source") == "weather_api" or data.get("event_type") == "weather_update":
                        cs["weather"] = {
                            "temperature": data.get("temperature"),
                            "condition": data.get("condition"),
                            "wind_speed": data.get("wind_speed"), "observed_at": ev.get("timestamp")
                        }
                    if ev.get("source") == "air_quality_api" or data.get("event_type") == "air_quality_update":
                        cs["air_quality"] = {
                            "aqi": data.get("air_quality_index"),
                            "pm2_5": data.get("pm2_5"),
                            "pm10": data.get("pm10"), "no2": data.get("no2"), "observed_at": ev.get("timestamp")
                        }

                    if ev.get("source") == "traffic_simulation":
                        cs["traffic"] = {"congestion_level": data.get("congestion_level"),
                            "avg_speed_kmh": data.get("average_speed"), "vehicle_count": data.get("vehicle_count"),
                            "observed_at": ev.get("timestamp"), "mode": "SIMULATED"}

            for cs in city_summaries.values():
                score = (cs["critical_count"] * 30) + (cs["high_count"] * 18) + (cs["anomaly_count"] * 15) + (cs["event_count"] * 2)
                cs["risk_score"] = min(100, score)
                cs["risk_level"] = "CRITICAL" if score > 75 else ("HIGH" if score > 50 else ("MODERATE" if score > 25 else "LOW"))
        except Exception as e:
            logger.warning(f"Error computing city_summaries: {e}")
            city_summaries = {}

        # Evaluate Data Freshness (mark STALE if no events in last 10 mins)
        now = datetime.datetime.now(datetime.timezone.utc)
        freshness_report = {}
        for src, info in self.source_freshness.items():
            freshness_copy = dict(info)
            ts = freshness_copy.get("observed_at") or freshness_copy.get("last_update")
            if ts:
                try:
                    last_dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    age = (now - last_dt).total_seconds()
                    freshness_copy["freshness_age_seconds"] = max(0, int(age))
                    if age > 600:
                        freshness_copy["observation_status"] = "STALE"
                        if freshness_copy.get("status") in {"LIVE", "RUNNING"}:
                            freshness_copy["status"] = "STALE"
                except Exception:
                    freshness_copy["freshness_age_seconds"] = None
            else:
                freshness_copy["freshness_age_seconds"] = None
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
            "city_summaries": city_summaries,
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
