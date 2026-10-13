import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.webhook_server import app, get_current_user
from src.processing.shared_state import reset_shared_state, get_shared_city_state_manager
from src.processing.rag_system import RAGSystem
from src.processing.llm_provider import GroqProvider

def test_history_is_empty_without_observations():
    reset_shared_state()
    app.dependency_overrides[get_current_user] = lambda: {"id": "test"}
    try:
        with TestClient(app) as client:
            result = client.get('/api/cities/Chennai/history').json()
            assert result['data_points'] == []
            assert client.get('/api/cities/Chen/history').status_code == 404
            state = client.get('/api/state').json()
            assert state['region']['cities_total'] == 20
            assert all(not s['last_ok_at'] for s in state['sources'])
    finally:
        app.dependency_overrides.clear()

def test_groq_failure_returns_grounded_fallback_without_model_citations():
    rag = RAGSystem({}, provider=GroqProvider(api_key='test-only-placeholder'))
    state = get_shared_city_state_manager().get_live_city_state()
    with patch.object(rag.provider, 'generate_structured_response', return_value={'error':'TIMEOUT', 'evidence':[{'event_id':'invented'}]}):
        result = rag.query_structured('Highest risk cities?', state)
    assert result['provider'] == 'deterministic_fallback'
    assert result['evidence'] == []
    assert 'unavailable' in result['answer']
    assert all(a['city'] in state['city_summaries'] for a in result['dashboard_actions'] if a.get('city'))

def test_traffic_zero_and_timestamp_are_preserved():
    reset_shared_state()
    mgr = get_shared_city_state_manager()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    mgr.ingest_event({'timestamp':now,'source':'traffic_simulation','location':{'lat':13.0827,'lon':80.2707},'data':{'city':'Chennai','congestion_level':0,'average_speed':0,'vehicle_count':0}})
    traffic = mgr.get_live_city_state()['city_summaries']['Chennai']['traffic']
    assert traffic['avg_speed_kmh'] == 0
    assert traffic['observed_at'] == now
