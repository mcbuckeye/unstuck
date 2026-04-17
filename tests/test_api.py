import os

from fastapi.testclient import TestClient

os.environ['DATABASE_URL'] = 'sqlite:///./unstuck_test.db'

from backend.main import app, reset_state  # noqa: E402

client = TestClient(app)


def setup_function():
    reset_state()


# -- helpers --

def signup_and_login(email='steve@example.com', password='secret123'):
    client.post('/api/auth/signup', json={'email': email, 'password': password})
    login = client.post('/api/auth/login', json={'email': email, 'password': password})
    data = login.json()
    return data['token'], data['user_id']


def auth_header(token):
    return {'Authorization': f'Bearer {token}'}


# -- health --

def test_healthcheck():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


# -- auth: signup and login --

def test_signup_and_login_flow():
    signup = client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    assert signup.status_code == 201
    payload = signup.json()
    assert payload['email'] == 'steve@example.com'
    assert 'password_hash' not in payload

    login = client.post('/api/auth/login', json={'email': 'steve@example.com', 'password': 'secret123'})
    assert login.status_code == 200
    data = login.json()
    assert 'token' in data
    assert 'user_id' in data
    # token should be a real JWT (three dot-separated base64 segments)
    assert data['token'].count('.') == 2


def test_login_rejects_bad_password():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    login = client.post('/api/auth/login', json={'email': 'steve@example.com', 'password': 'wrong'})
    assert login.status_code == 401


def test_login_rejects_nonexistent_user():
    login = client.post('/api/auth/login', json={'email': 'ghost@example.com', 'password': 'whatever'})
    assert login.status_code == 401


def test_signup_rejects_duplicate_email():
    client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'secret123'})
    dup = client.post('/api/auth/signup', json={'email': 'steve@example.com', 'password': 'other123'})
    assert dup.status_code == 400


def test_signup_rejects_blank_email():
    resp = client.post('/api/auth/signup', json={'email': '', 'password': 'secret123'})
    assert resp.status_code == 422


def test_signup_rejects_short_password():
    resp = client.post('/api/auth/signup', json={'email': 'a@b.com', 'password': '12'})
    assert resp.status_code == 422


# -- JWT protected routes --

def test_today_requires_auth():
    resp = client.get('/api/today')
    assert resp.status_code == 401


def test_today_rejects_bad_token():
    resp = client.get('/api/today', headers={'Authorization': 'Bearer garbage'})
    assert resp.status_code == 401


def test_today_screen_payload_is_user_scoped():
    token, uid = signup_and_login()
    response = client.get('/api/today', headers=auth_header(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload['main_focus'] == 'Start the most avoided meaningful task'
    assert payload['tasks'] == []
    assert payload['energy'] == 'unknown'


def test_create_task_requires_auth():
    resp = client.post('/api/tasks', json={'title': 'Draft welcome screen', 'category': 'build'})
    assert resp.status_code == 401


def test_create_and_complete_task():
    token, uid = signup_and_login()
    created = client.post(
        '/api/tasks',
        json={'title': 'Draft welcome screen', 'category': 'build'},
        headers=auth_header(token),
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload['title'] == 'Draft welcome screen'
    assert payload['done'] is False

    task_id = payload['id']
    completed = client.post(f'/api/tasks/{task_id}/complete', headers=auth_header(token))
    assert completed.status_code == 200
    assert completed.json()['done'] is True


def test_complete_task_404_for_wrong_user():
    token_a, _ = signup_and_login('a@example.com', 'pass1234')
    token_b, _ = signup_and_login('b@example.com', 'pass1234')
    created = client.post('/api/tasks', json={'title': 'Mine', 'category': 'focus'}, headers=auth_header(token_a))
    task_id = created.json()['id']
    resp = client.post(f'/api/tasks/{task_id}/complete', headers=auth_header(token_b))
    assert resp.status_code == 404


def test_start_and_complete_sprint():
    token, uid = signup_and_login()
    response = client.post(
        '/api/sprints',
        json={'minutes': 10, 'task_title': 'Draft welcome screen'},
        headers=auth_header(token),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload['minutes'] == 10
    assert payload['status'] == 'active'

    sprint_id = payload['id']
    completed = client.post(f'/api/sprints/{sprint_id}/complete', headers=auth_header(token))
    assert completed.status_code == 200
    assert completed.json()['status'] == 'completed'


def test_unstuck_flow_returns_small_next_step_and_persists_record():
    token, uid = signup_and_login()
    response = client.post(
        '/api/unstuck',
        json={'avoiding': 'Write the landing page copy', 'blocker': 'overwhelm', 'feeling': 'anxious'},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'next_step' in payload
    assert 'suggested_sprint_minutes' in payload

    today = client.get('/api/today', headers=auth_header(token)).json()
    assert len(today['interventions']) == 1


def test_daily_checkin_persists():
    token, uid = signup_and_login()
    response = client.post(
        '/api/checkins',
        json={'energy': 'low', 'mood': 'anxious', 'clarity': 'foggy', 'resistance': 'high'},
        headers=auth_header(token),
    )
    assert response.status_code == 201

    today = client.get('/api/today', headers=auth_header(token)).json()
    assert today['energy'] == 'low'
    assert today['latest_checkin']['mood'] == 'anxious'


# -- validation --

def test_create_task_rejects_blank_title():
    token, uid = signup_and_login()
    resp = client.post('/api/tasks', json={'title': '', 'category': 'focus'}, headers=auth_header(token))
    assert resp.status_code == 422


def test_sprint_rejects_invalid_minutes():
    token, uid = signup_and_login()
    resp = client.post('/api/sprints', json={'minutes': 0}, headers=auth_header(token))
    assert resp.status_code == 422


def test_unstuck_rejects_unknown_blocker():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/unstuck',
        json={'avoiding': 'thing', 'blocker': 'fake_blocker', 'feeling': 'anxious'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_checkin_rejects_invalid_energy():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/checkins',
        json={'energy': 'mega', 'mood': 'steady', 'clarity': 'clear', 'resistance': 'low'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422
