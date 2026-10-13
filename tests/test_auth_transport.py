import datetime
import uuid
import pytest
from fastapi.testclient import TestClient
from src import auth
from src import webhook_server as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'auth.db'))
    auth.init_auth_db()
    with TestClient(api.app) as client:
        yield client


def signup(client):
    result = client.post('/api/auth/signup', json={
        'full_name': 'Transport test', 'email': f'{uuid.uuid4()}@example.test',
        'password': uuid.uuid4().hex, 'session_mode': 'memory',
    })
    assert result.status_code == 201
    return result.json()['token']


def test_memory_token_works_without_cookie_and_logout_revokes(client):
    token = signup(client)
    client.cookies.clear()
    headers = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/state', headers=headers).status_code == 200
    with auth.get_db_connection() as db:
        expires = db.execute('SELECT expires_at FROM sessions WHERE token=?', (token,)).fetchone()[0]
    seconds = (datetime.datetime.fromisoformat(expires) - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    assert 0 < seconds <= 900
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    assert client.get('/api/state', headers=headers).status_code == 401
    assert client.get('/api/stream', headers=headers).status_code == 401


def test_production_cookie_mutations_require_trusted_origin(client, monkeypatch):
    token = signup(client)
    monkeypatch.setenv('ENVIRONMENT', 'production')
    assert client.post('/api/auth/logout').status_code == 403
    assert client.post('/api/auth/logout', headers={'Origin': 'https://evil.invalid'}).status_code == 403
    assert auth.get_session_user(token)
    assert client.post('/api/auth/logout', headers={
        'Origin': api.allowed_origins[0], 'X-Requested-With': 'XMLHttpRequest',
    }).status_code == 200
    assert auth.get_session_user(token) is None


def test_production_cookie_is_secure_even_without_override(client, monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('COOKIE_SECURE', 'false')
    from fastapi import Response
    response = Response()
    api.set_auth_cookie(response, 'not-a-real-session', 900)
    cookie = response.headers['set-cookie'].lower()
    assert 'secure' in cookie and 'httponly' in cookie and 'samesite=none' in cookie


def test_expired_bearer_rejected_for_state_and_stream(client):
    token = signup(client)
    with auth.get_db_connection() as db:
        db.execute('UPDATE sessions SET expires_at=? WHERE token=?', ('2000-01-01T00:00:00+00:00', token))
    client.cookies.clear()
    headers = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/state', headers=headers).status_code == 401
    assert client.get('/api/stream', headers=headers).status_code == 401


def test_cors_allows_configured_origin_and_rejects_foreign_origin(client):
    headers = {'Origin': api.allowed_origins[0], 'Access-Control-Request-Method':'POST',
               'Access-Control-Request-Headers':'authorization,content-type,x-requested-with'}
    response = client.options('/api/ask', headers=headers)
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == api.allowed_origins[0]
    assert response.headers['access-control-allow-credentials'] == 'true'
    headers['Origin'] = 'https://untrusted.invalid'
    response = client.options('/api/ask', headers=headers)
    assert 'access-control-allow-origin' not in response.headers
