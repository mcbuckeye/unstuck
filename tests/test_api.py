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


def test_create_task():
    response = client.post(
        '/api/tasks',
        json={
            'title': 'Draft welcome screen',
            'category': 'build',
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload['title'] == 'Draft welcome screen'
    assert payload['done'] is False


def test_start_sprint():
    response = client.post('/api/sprints', json={'minutes': 10, 'task_title': 'Draft welcome screen'})
    assert response.status_code == 201
    payload = response.json()
    assert payload['minutes'] == 10
    assert payload['status'] == 'active'
