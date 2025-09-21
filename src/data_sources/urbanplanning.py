import pathway as pw
import datetime
import random
import requests
from .base import DataSource

class TransitSource(DataSource):
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
            # In production, connect to actual transit API
            transit_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "transit_api",
                "data": {
                    "route_id": f"M{random.randint(1, 9)}",
                    "delay": random.uniform(0, 15) if random.random() > 0.2 else random.uniform(15, 45),
                    "passenger_count": random.randint(10, 200),
                    "vehicle_location": {
                        "lat": random.uniform(40.7, 40.8),
                        "lon": random.uniform(-74.0, -73.9)
                    }
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield transit_data
            pw.sleep(3)

class TrafficSource(DataSource):
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
            # In production, connect to actual traffic API
            traffic_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "traffic_api",
                "data": {
                    "congestion_level": random.uniform(0.1, 0.9),
                    "average_speed": random.uniform(10, 40),
                    "incident_count": random.randint(0, 5)
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield traffic_data
            pw.sleep(2)

class EnvironmentSource(DataSource):
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
            # In production, connect to actual environment API
            env_data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "source": "environment_api",
                "data": {
                    "air_quality_index": random.uniform(20, 150),
                    "noise_level": random.uniform(40, 80),
                    "temperature": random.uniform(15, 30)
                },
                "location": {
                    "lat": random.uniform(40.7, 40.8),
                    "lon": random.uniform(-74.0, -73.9)
                }
            }
            yield env_data
            pw.sleep(5)
