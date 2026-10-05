import datetime
import random
import time
import logging

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

from .base import DataSource

logger = logging.getLogger(__name__)

class EventSchema(pw.Schema):
    timestamp: str
    source: str
    data: pw.Json
    location: pw.Json

class SocialMediaSource(DataSource):
    name = "social_media"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        keywords = self.config.get('data_sources', {}).get('social_media', {}).get('keywords', ['fire', 'accident', 'protest', 'emergency'])
        while True:
            keyword = random.choice(keywords) if keywords else "emergency"
            post = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "twitter",
                "data": {
                    "text": f"Emergency near downtown: {keyword}",
                    "user": f"citizen{random.randint(100, 999)}",
                    "hashtags": [f"#{keyword}"]
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield post
            time.sleep(1)

class PublicSafetySource(DataSource):
    name = "public_safety"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            incident = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "police_scanner",
                "data": {
                    "type": random.choice(["fire", "accident", "medical", "crime"]),
                    "priority": random.randint(1, 5),
                    "description": "Multiple vehicles involved"
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield incident
            time.sleep(2)

class IoTSensorSource(DataSource):
    name = "iot_sensors"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        sim_rate = self.config.get('data_sources', {}).get('iot_sensors', {}).get('simulation_rate', 0.5)
        while True:
            anomaly = random.random() < 0.05
            sensor_data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "city_sensors",
                "data": {
                    "noise_level": round(random.uniform(50, 70) if not anomaly else random.uniform(81, 100), 2),
                    "crowd_density": round(random.uniform(0.1, 0.5) if not anomaly else random.uniform(0.81, 1.0), 2),
                    "traffic_flow": round(random.uniform(0.3, 0.7) if not anomaly else random.uniform(0.0, 0.19), 2),
                    "anomaly": anomaly
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield sensor_data
            time.sleep(sim_rate)

