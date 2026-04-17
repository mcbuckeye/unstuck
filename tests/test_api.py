import os

from fastapi.testclient import TestClient

os.environ['DATABASE_URL'] = 'sqlite:///./unstuck_test.db'

from backend.main import app, reset_state  # noqa: E402

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
    assert login.json()['token'].startswith('demo-token-')


def test_today_screen_payload_is_user_scoped():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.get('/api/today?user_id=1')
    assert response.status_code == 200
    payload = response.json()
    assert payload['main_focus'] == 'Start the most avoided meaningful task'
    assert payload['tasks'] == []
    assert payload['energy'] == 'unknown'


def test_create_and_complete_task():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    created = client.post(
        '/api/tasks',
        json={
            'user_id': 1,
            'title': 'Draft welcome screen',
            'category': 'build',
        },
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload['title'] == 'Draft welcome screen'
    assert payload['done'] is False

    completed = client.post('/api/tasks/1/complete', json={'user_id': 1})
    assert completed.status_code == 200
    assert completed.json()['done'] is True


def test_start_and_complete_sprint():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.post('/api/sprints', json={'user_id': 1, 'minutes': 10, 'task_title': 'Draft welcome screen'})
    assert response.status_code == 201
    payload = response.json()
    assert payload['minutes'] == 10
    assert payload['status'] == 'active'

    completed = client.post('/api/sprints/1/complete', json={'user_id': 1})
    assert completed.status_code == 200
    assert completed.json()['status'] == 'completed'


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


def test_daily_checkin_persists():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    response = client.post(
        '/api/checkins',
        json={
            'user_id': 1,
            'energy': 'low',
            'mood': 'anxious',
            'clarity': 'foggy',
            'resistance': 'high',
        },
    )
    assert response.status_code == 201

    today = client.get('/api/today?user_id=1').json()
    assert today['energy'] == 'low'
    assert today['latest_checkin']['mood'] == 'anxious'
