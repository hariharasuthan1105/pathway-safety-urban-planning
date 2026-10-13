import datetime
from unittest.mock import MagicMock, patch
import pytest
import requests
from fastapi.testclient import TestClient
from src import webhook_server as api
from src.data_sources.real_sources import GTFSTransitSource, WeatherSource, AirQualitySource
from src.processing.shared_state import reset_shared_state, ingest_runtime_event, get_shared_city_state_manager, get_shared_rag_system

class StopPolling(BaseException):
    pass

def test_waiting_simulators_are_not_external_observations(monkeypatch):
    monkeypatch.setattr(api, '_SOURCE_STATUS_PROVIDER', lambda: {
        'social_media': {'status': 'RUNNING'}, 'webhook_api': {'status': 'RUNNING'}})
    report = api.source_freshness_report({'data_freshness': {}})
    assert report['twitter']['mode'] == 'SIMULATED'
    assert report['twitter']['status'] == 'WAITING'
    assert report['twitter']['event_count'] == 0
    assert report['webhook_ingestion']['mode'] == 'EVENT_DRIVEN'

@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.delenv('GTFS_FEED_URL', raising=False)
    monkeypatch.setattr(api, '_SOURCE_STATUS_PROVIDER', None)
    reset_shared_state()
    api.app.dependency_overrides[api.get_current_user] = lambda: {'id':'status-test'}
    yield
    api.app.dependency_overrides.clear()
    reset_shared_state()

def test_unconfigured_gtfs_never_becomes_live_or_an_observation(monkeypatch):
    source = GTFSTransitSource({})
    with patch('src.data_sources.real_sources.requests.get') as get:
        assert list(source._stream()) == []
        get.assert_not_called()
    # Reject older producers' notices too, including formerly fake feed updates.
    for kind in ['transit_status', 'transit_feed_update', 'connector_status']:
        ingest_runtime_event({'source':source.name, 'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                              'data':{'event_type':kind,'status':'NOT CONFIGURED'}, 'location':{}})
    monkeypatch.setattr(api, '_SOURCE_STATUS_PROVIDER', lambda:{source.name:{'status':source.status}})
    with TestClient(api.app) as client:
        health=client.get('/api/health').json()
        entry=health['data_freshness'][source.name]
        assert entry['status'] == 'NOT_CONFIGURED'
        assert entry['event_count'] == 0 and entry['last_update'] is None
        assert health['total_events_ingested'] == 0
        state=client.get('/api/state').json()
        assert not state['recent_events']
        assert next(s for s in state['sources'] if s['id']=='gtfs_transit')['status']=='NOT_CONFIGURED'
    assert not get_shared_rag_system().documents

@pytest.mark.parametrize('source_type', [WeatherSource, AirQualitySource])
@pytest.mark.parametrize('failure', ['network', 'http'])
def test_external_failure_is_not_reported_live(source_type, failure, monkeypatch):
    source=source_type({});source.cities=source.cities[:1]
    mgr=get_shared_city_state_manager()
    mgr.ingest_event({'source':source.name,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      'data':{'city':'Chennai'},'location':{'lat':13.0827,'lon':80.2707}})
    before=dict(mgr.source_freshness[source.name])
    response=MagicMock(status_code=503)
    with patch('src.data_sources.real_sources.requests.get', side_effect=requests.ConnectionError('offline') if failure=='network' else None,return_value=response), patch('src.data_sources.real_sources.time.sleep',side_effect=StopPolling):
        with pytest.raises(StopPolling): next(source._stream())
    expected='OFFLINE' if failure=='network' else 'DEGRADED'
    monkeypatch.setattr(api, '_SOURCE_STATUS_PROVIDER',lambda:{source.name:{'status':source.status}})
    with TestClient(api.app) as client:
        for endpoint in ['/api/health','/api/state']:
            entry=client.get(endpoint).json()['data_freshness'][source.name]
            assert entry['status']==entry['connector_status']==expected
            assert entry['event_count']==before['event_count']
            assert entry['last_update']==before['last_update']
            assert entry['observation_status']=='LIVE'

@pytest.mark.parametrize('status,expected',[(200,'REACHABLE'),(503,'DEGRADED')])
def test_gtfs_http_response_is_not_a_decoded_transit_observation(status,expected,monkeypatch):
    source=GTFSTransitSource({'data_sources':{'transit':{'feed_url':'https://example.test/gtfs'}}})
    assert source.status=='READY'
    with patch('src.data_sources.real_sources.requests.get',return_value=MagicMock(status_code=status)),patch('src.data_sources.real_sources.time.sleep',side_effect=StopPolling):
        with pytest.raises(StopPolling):next(source._stream())
    assert source.status==expected
    assert source.last_updated=='N/A'
    assert source.last_checked_at
