"""Run directly on Linux for the native Pathway 0.33.0 regression."""
import os
import datetime
import sys
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pathway_compat import pw, IS_NATIVE_PATHWAY
from src.main import create_pathway_sink, anomaly_flag
from src.processing import AnomalyDetector
from src.processing.shared_state import get_shared_city_state_manager, reset_shared_state
from src.data_sources.base import GeneratorConnectorSubject

if os.getenv("REQUIRE_NATIVE_PATHWAY") == "1":
    assert IS_NATIVE_PATHWAY, "Native Pathway required; compatibility fallback is forbidden"

reset_shared_state()
class Events(pw.Schema):
    timestamp: str
    source: str
    data: pw.Json
    location: pw.Json

def records():
    for number in range(2):
        yield {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "source": "subscription_regression", "data": {"noise_level": 95, "event_id": f"regression-{number}", "city": "Chennai"},
               "location": {"lat": 13.0827, "lon": 80.2707}}

table = pw.io.python.read(GeneratorConnectorSubject(records), schema=Events)
detector = AnomalyDetector({"anomaly_rules": {"noise_level": 80}})
processed = table.select(timestamp=table.timestamp, source=table.source,
                         data=detector.process(table.data), location=table.location)
sink = create_pathway_sink({})
seen = []
done = threading.Event()
def on_change(key, row, time, is_addition):
    sink(key=key, row=row, time=time, is_addition=is_addition)
    if is_addition:
        seen.append(row)
        if len(seen) == 2:
            done.set()
pw.io.subscribe(processed, on_change=on_change)
anomalies = []
pw.io.subscribe(processed.filter(anomaly_flag(processed.data)), on_change=lambda key,row,time,is_addition: anomalies.append(row) if is_addition else None)
pw.run()
assert done.wait(10), "Non-empty stream never reached output sink"
assert len(seen) == 2, "Events must arrive exactly once"
events = get_shared_city_state_manager().get_live_city_state()["recent_events"]
assert len(events) == 2
assert len(anomalies) == 2
assert all(e["data"]["anomaly"] for e in events)
print(f"STREAM_REGRESSION_OK events={len(events)} native={IS_NATIVE_PATHWAY}")
