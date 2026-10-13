"""Clearly labelled local generators for the optional urban-planning mode."""
import datetime
import random
import time
import uuid
from .base import DataSource
from .public_safety import EventSchema
from .real_sources import SOUTH_INDIA_CITIES

class UrbanSimulationSource(DataSource):
    status = "SIMULATED"
    def _define_schema(self):
        return EventSchema

    def _stream(self):
        while True:
            city = random.choice(SOUTH_INDIA_CITIES)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.last_updated = now
            yield {"timestamp": now, "source": self.name,
                   "data": {"event_id": uuid.uuid4().hex, "city": city["city"],
                            "state": city["state"], "mode": "SIMULATED", **self.reading()},
                   "location": {"lat": city["lat"], "lon": city["lon"]}}
            time.sleep(5)

class TransitSource(UrbanSimulationSource):
    name = "transit_simulation"
    def reading(self):
        return {"event_type": "transit_simulation", "delay_minutes": random.randint(0, 20)}

class TrafficSource(UrbanSimulationSource):
    name = "planning_traffic_simulation"
    def reading(self):
        return {"event_type": "planning_traffic_simulation", "traffic_flow": random.randint(10, 80)}

class EnvironmentSource(UrbanSimulationSource):
    name = "environment_simulation"
    def reading(self):
        return {"event_type": "environment_simulation", "noise_level": round(random.uniform(40, 80), 1)}
