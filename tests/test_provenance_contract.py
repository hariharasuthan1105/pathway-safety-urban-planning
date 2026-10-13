import datetime
from pathlib import Path
from src.processing.provenance import SourceClass, SourceStatus
from src.processing.city_state import CityStateManager
from src import webhook_server as api


def test_shared_frontend_source_enums_match_backend():
    types = Path('frontend/src/types/provenance.ts').read_text()
    for enum in (SourceClass, SourceStatus):
        for entry in enum:
            assert f"'{entry.value}'" in types


def test_simulation_is_never_live_and_ingestion_is_separate(monkeypatch):
    monkeypatch.setattr(api, '_SOURCE_STATUS_PROVIDER', None)
    mgr = CityStateManager({'freshness_seconds': {'traffic_simulation': 1}})
    observed = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
    mgr.ingest_event({'source':'traffic_simulation','timestamp':observed,'data':{'city':'Chennai'},'location':{}})
    entry = api.source_freshness_report(mgr.get_live_city_state())['traffic_simulation']
    assert entry['source_class'] == 'SIMULATED'
    assert entry['status'] == 'STALE'
    assert entry['observed_at'] == observed
    assert entry['ingested_at'] != observed
    assert entry['stale_after_seconds'] == 1


def test_no_observations_means_unavailable_risk():
    state = CityStateManager().get_live_city_state()
    assert state['overall_risk_score'] is None
    assert state['risk_unavailable_reason']
    assert all(city['risk_score'] is None and city['unavailable_reason'] for city in state['city_summaries'].values())
