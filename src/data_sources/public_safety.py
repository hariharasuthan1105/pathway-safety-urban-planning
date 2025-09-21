import pathway as pw
import datetime
import random
import requests
from .base import DataSource

class SocialMediaSource(DataSource):
    def _define_schema(self):
        return pw.schema(
            timestamp=str,
            source=str,
            data=pw.Json,
            location=pw.Json,
        )
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            # In production, use actual API calls
            post = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "twitter",
                "data": {
                    "text": f"Emergency near downtown: {random.choice(['fire', 'accident', 'protest'])}",
                    "user": "citizen123",
                    "hashtags": [f"#{random.choice(['fire', 'accident', 'protest'])}"]
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield post
            pw.sleep(1)

class PublicSafetySource(DataSource):
    def _define_schema(self):
        return pw.schema(
            timestamp=str,
            source=str,
            data=pw.Json,
            location=pw.Json,
        )
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            # In production, connect to actual scanner API
            incident = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "police_scanner",
                "data": {
                    "type": random.choice(["fire", "accident", "medical", "crime"]),
                    "priority": random.randint(1, 5),
                    "description": "Multiple vehicles involved"
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield incident
            pw.sleep(2)

class IoTSensorSource(DataSource):
    def _define_schema(self):
        return pw.schema(
            timestamp=str,
            source=str,
            data=pw.Json,
            location=pw.Json,
        )
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            anomaly = random.random() < 0.05
            sensor_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "city_sensors",
                "data": {
                    "noise_level": random.uniform(50, 70) if not anomaly else random.uniform(80, 100),
                    "crowd_density": random.uniform(0.1, 0.5) if not anomaly else random.uniform(0.8, 1.0),
                    "traffic_flow": random.uniform(0.3, 0.7) if not anomaly else random.uniform(0.0, 0.2),
                    "anomaly": anomaly
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield sensor_data
            pw.sleep(self.config['data_sources']['iot_sensors']['simulation_rate'])
