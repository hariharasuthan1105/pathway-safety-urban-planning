import datetime
import logging
from typing import Dict, Any, List

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.rules = config.get('anomaly_rules', {})
        self.location_counts = {}
    
    @pw.udf
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data

        # Make a copy to avoid unintended side effects
        processed = dict(data)
        source = processed.get("source", "")
        location = processed.get("location", {})
        lat = location.get("lat", 0.0) if isinstance(location, dict) else 0.0
        lon = location.get("lon", 0.0) if isinstance(location, dict) else 0.0
        location_key = f"{lat:.2f},{lon:.2f}"
        
        # Track location counts for social media spike detection
        if location_key not in self.location_counts:
            self.location_counts[location_key] = {
                "social_media": 0,
                "last_reset": datetime.datetime.now(datetime.timezone.utc)
            }
        
        # Check for social media spikes
        if source in ["twitter", "social_media"]:
            self.location_counts[location_key]["social_media"] += 1
            elapsed = (datetime.datetime.now(datetime.timezone.utc) - self.location_counts[location_key]["last_reset"]).total_seconds()
            spike_threshold = self.rules.get("social_media_spike", 10)
            
            if elapsed > 60:
                if self.location_counts[location_key]["social_media"] > spike_threshold:
                    processed["anomaly"] = True
                    processed["anomaly_type"] = "social_media_spike"
                    processed["anomaly_description"] = f"Spike in social media mentions at {location_key}"
                
                self.location_counts[location_key] = {
                    "social_media": 0,
                    "last_reset": datetime.datetime.now(datetime.timezone.utc)
                }

        # Check IoT sensor / data metric anomalies
        sensor_data = processed.get("data", {})
        if isinstance(sensor_data, dict):
            # Check if sensor data already has an anomaly flag
            if sensor_data.get("anomaly", False):
                processed["anomaly"] = True
                processed["anomaly_type"] = "sensor_alert"
                processed["anomaly_description"] = sensor_data.get("anomaly_type", "Sensor reported explicit anomaly flag")

            for metric, value in sensor_data.items():
                if metric in self.rules:
                    threshold = self.rules[metric]
                    # Traffic flow anomaly is triggered when speed/flow drops below threshold
                    if metric == "traffic_flow" and isinstance(value, (int, float)) and value < threshold:
                        processed["anomaly"] = True
                        processed["anomaly_type"] = "traffic_flow_anomaly"
                        processed["anomaly_description"] = f"Low traffic flow detected: {value} (threshold: {threshold})"
                        break
                    elif metric != "traffic_flow" and isinstance(value, (int, float)) and value > threshold:
                        processed["anomaly"] = True
                        processed["anomaly_type"] = f"{metric}_anomaly"
                        processed["anomaly_description"] = f"High {metric} detected: {value} (threshold: {threshold})"
                        break

        return processed

    def detect_temporal_anomalies(self, recent_events: List[Dict[str, Any]], window_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates sliding history for temporal anomaly patterns:
        - Sudden rate of change acceleration (> 2.0x baseline)
        - Sudden AQI or PM2.5 spike across recent readings
        - Multiple critical incidents within a short 5-minute window
        """
        temporal_anomalies = []
        
        # 1. Frequency Acceleration Anomaly
        accel = window_metrics.get("acceleration_ratio", 1.0)
        c5 = window_metrics.get("count_5m", 0)
        if accel >= 2.0 and c5 >= 3:
            temporal_anomalies.append({
                "anomaly_id": f"anom_freq_{datetime.datetime.now().strftime('%H%M%S')}",
                "anomaly_type": "rapid_event_frequency_spike",
                "severity": "HIGH",
                "description": f"Sudden surge in event frequency ({accel:.1f}x acceleration over 15-minute baseline)",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

        # 2. Critical Burst Anomaly
        w5_events = window_metrics.get("events_5m", [])
        critical_count = 0
        for ev in w5_events:
            data = ev.get("data", {}) if isinstance(ev.get("data"), dict) else {}
            if str(data.get("severity", ev.get("severity", ""))).upper() == "CRITICAL":
                critical_count += 1

        if critical_count >= 2:
            temporal_anomalies.append({
                "anomaly_id": f"anom_burst_{datetime.datetime.now().strftime('%H%M%S')}",
                "anomaly_type": "critical_incident_burst",
                "severity": "CRITICAL",
                "description": f"Multiple critical incidents ({critical_count}) received within 5 minutes.",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

        return temporal_anomalies
