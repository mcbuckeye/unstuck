from fastapi.testclient import TestClient

from backend.main import app, reset_state

client = TestClient(app)


def setup_function():
    reset_state()


def test_healthcheck():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_signup_and_login_flow():
    signup = client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    assert signup.status_code == 201
    payload = signup.json()
    assert payload['email'] == 'steve@example.com'

    login = client.post('/api/auth/login', json={'email': 'steve@example.com', 'password': 'secret123'})
    assert login.status_code == 200
    assert login.json()['token'] == 'demo-token-1'


def test_today_screen_payload_is_user_scoped():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.get('/api/today?user_id=1')
    assert response.status_code == 200
    payload = response.json()
    assert payload['main_focus'] == 'Start the most avoided meaningful task'
    assert payload['tasks'] == []
    assert payload['energy'] == 'unknown'


def test_create_task():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.post(
        '/api/tasks',
        json={
            'user_id': 1,
            'title': 'Draft welcome screen',
            'category': 'build',
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload['title'] == 'Draft welcome screen'
    assert payload['done'] is False


def test_start_sprint():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.post('/api/sprints', json={'user_id': 1, 'minutes': 10, 'task_title': 'Draft welcome screen'})
    assert response.status_code == 201
    payload = response.json()
    assert payload['minutes'] == 10
    assert payload['status'] == 'active'


def test_unstuck_flow_returns_small_next_step_and_persists_record():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.post(
        '/api/unstuck',
        json={
            'user_id': 1,
            'avoiding': 'Write the landing page copy',
            'blocker': 'overwhelm',
            'feeling': 'anxious',
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'next_step' in payload
    assert 'suggested_sprint_minutes' in payload

    today = client.get('/api/today?user_id=1').json()
    assert len(today['interventions']) == 1
