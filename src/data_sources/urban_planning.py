import datetime
import random
import time
import logging

try:
    import pathway as pw
except ImportError:
    from ..pathway_compat import pw

from .base import DataSource, GeneratorConnectorSubject
from .public_safety import EventSchema

logger = logging.getLogger(__name__)

class TransitSource(DataSource):
    name = "transit"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

class TrafficSource(DataSource):
    name = "traffic"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

class EnvironmentSource(DataSource):
    name = "environment"

    def _define_schema(self):
        return EventSchema
    
    def get_stream(self):
        subject = GeneratorConnectorSubject(self._stream, source_instance=self)
        return pw.io.python.read(subject, schema=self.schema)

    
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

