from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_today_screen_payload():
    response = client.get('/api/today')
    assert response.status_code == 200
    payload = response.json()
    assert 'main_focus' in payload
    assert 'tasks' in payload
    assert 'energy' in payload


def test_unstuck_flow_returns_small_next_step():
    response = client.post(
        '/api/unstuck',
        json={
            'avoiding': 'Write the landing page copy',
            'blocker': 'overwhelm',
            'feeling': 'anxious',
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'next_step' in payload
    assert 'suggested_sprint_minutes' in payload
