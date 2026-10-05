import datetime
import random
import time
import logging

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

from .base import DataSource
from .public_safety import EventSchema

logger = logging.getLogger(__name__)

class TransitSource(DataSource):
    name = "transit"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            transit_data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "transit_api",
                "data": {
                    "route_id": f"M{random.randint(1, 9)}",
                    "delay": round(random.uniform(0, 15) if random.random() > 0.2 else random.uniform(15, 45), 1),
                    "passenger_count": random.randint(10, 200),
                    "vehicle_location": {
                        "lat": round(random.uniform(40.7, 40.8), 4),
                        "lon": round(random.uniform(-74.0, -73.9), 4)
                    }
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield transit_data
            time.sleep(3)

class TrafficSource(DataSource):
    name = "traffic"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            traffic_data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "traffic_api",
                "data": {
                    "congestion_level": round(random.uniform(0.1, 0.9), 2),
                    "average_speed": round(random.uniform(10, 40), 1),
                    "incident_count": random.randint(0, 5)
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield traffic_data
            time.sleep(2)

class EnvironmentSource(DataSource):
    name = "environment"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        return pw.io.python.read(self._stream, schema=self.schema)
    
    def _stream(self):
        while True:
            env_data = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "environment_api",
                "data": {
                    "air_quality_index": round(random.uniform(20, 150), 1),
                    "noise_level": round(random.uniform(40, 80), 1),
                    "temperature": round(random.uniform(15, 30), 1)
                },
                "location": {
                    "lat": round(random.uniform(40.7, 40.8), 4),
                    "lon": round(random.uniform(-74.0, -73.9), 4)
                }
            }
            yield env_data
            time.sleep(5)

