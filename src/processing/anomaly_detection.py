import pathway as pw
import datetime
from typing import Dict, Any

class AnomalyDetector:
    def __init__(self, config: Dict[str, Any]):
        self.rules = config.get('anomaly_rules', {})
        self.location_counts = {}
    
    @pw.udf
    def process(self, data: pw.Json) -> pw.Json:
        source = data.get("source", "")
        location_key = f"{data['location']['lat']:.2f},{data['location']['lon']:.2f}"
        
        # Initialize location tracking
        if location_key not in self.location_counts:
            self.location_counts[location_key] = {
                "social_media": 0,
                "last_reset": datetime.datetime.utcnow()
            }
        
        # Check for social media spikes
        if source == "twitter":
            self.location_counts[location_key]["social_media"] += 1
            
            # Reset counts every minute
            if (datetime.datetime.utcnow() - self.location_counts[location_key]["last_reset"]).total_seconds() > 60:
                if self.location_counts[location_key]["social_media"] > self.rules.get("social_media_spike", 10):
                    data["anomaly"] = True
                    data["anomaly_type"] = "social_media_spike"
                    data["anomaly_description"] = f"Spike in social media mentions at {location_key}"
                
                self.location_counts[location_key] = {
                    "social_media": 0,
                    "last_reset": datetime.datetime.utcnow()
                }
        
        # Check IoT sensor anomalies
        if source == "city_sensors":
            sensor_data = data.get("data", {})
            for metric, value in sensor_data.items():
                if metric in self.rules and value > self.rules[metric]:
                    data["anomaly"] = True
                    data["anomaly_type"] = f"{metric}_anomaly"
                    data["anomaly_description"] = f"High {metric} detected: {value}"
                    break
        
        return data
