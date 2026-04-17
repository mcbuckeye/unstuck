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
    assert response.json()['status'] == 'ok'


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


# -- CORS --

def test_cors_allows_unstuckinator_origin():
    resp = client.options(
        '/api/health',
        headers={'Origin': 'https://unstuckinator.com', 'Access-Control-Request-Method': 'GET'},
    )
    assert resp.headers.get('access-control-allow-origin') in (
        'https://unstuckinator.com', '*',
    )


# -- idempotency / edge cases --

def test_complete_already_completed_task_stays_done():
    token, uid = signup_and_login()
    created = client.post('/api/tasks', json={'title': 'Ship it'}, headers=auth_header(token))
    task_id = created.json()['id']
    client.post(f'/api/tasks/{task_id}/complete', headers=auth_header(token))
    second = client.post(f'/api/tasks/{task_id}/complete', headers=auth_header(token))
    assert second.status_code == 200
    assert second.json()['done'] is True


def test_complete_sprint_404_for_wrong_user():
    token_a, _ = signup_and_login('a@example.com', 'pass1234')
    token_b, _ = signup_and_login('b@example.com', 'pass1234')
    created = client.post('/api/sprints', json={'minutes': 10}, headers=auth_header(token_a))
    sprint_id = created.json()['id']
    resp = client.post(f'/api/sprints/{sprint_id}/complete', headers=auth_header(token_b))
    assert resp.status_code == 404


def test_sprint_rejects_over_max_minutes():
    token, uid = signup_and_login()
    resp = client.post('/api/sprints', json={'minutes': 999}, headers=auth_header(token))
    assert resp.status_code == 422


def test_today_shows_completed_tasks_in_wins():
    token, uid = signup_and_login()
    created = client.post('/api/tasks', json={'title': 'Win task'}, headers=auth_header(token))
    task_id = created.json()['id']
    client.post(f'/api/tasks/{task_id}/complete', headers=auth_header(token))
    today = client.get('/api/today', headers=auth_header(token)).json()
    assert 'Win task' in today['wins']
    # completed tasks should not appear in open task list
    assert all(t['title'] != 'Win task' for t in today['tasks'])


def test_unstuck_reframe_contains_feeling():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/unstuck',
        json={'avoiding': 'Taxes', 'blocker': 'fear', 'feeling': 'terrified'},
        headers=auth_header(token),
    )
    payload = resp.json()
    assert 'terrified' in payload['reframe']


def test_signup_does_not_leak_password_hash():
    resp = client.post('/api/auth/signup', json={'email': 'safe@example.com', 'password': 'secret123'})
    body = resp.json()
    assert 'password_hash' not in body
    assert 'password' not in body


def test_healthcheck_returns_app_name():
    resp = client.get('/api/health')
    body = resp.json()
    assert body['status'] == 'ok'
    assert 'name' in body
    assert 'Unstuckinator' in body['name']


def test_multiple_checkins_latest_wins():
    token, uid = signup_and_login()
    client.post('/api/checkins', json={'energy': 'low', 'mood': 'anxious', 'clarity': 'foggy', 'resistance': 'high'}, headers=auth_header(token))
    client.post('/api/checkins', json={'energy': 'high', 'mood': 'hopeful', 'clarity': 'clear', 'resistance': 'low'}, headers=auth_header(token))
    today = client.get('/api/today', headers=auth_header(token)).json()
    assert today['energy'] == 'high'
    assert today['latest_checkin']['mood'] == 'hopeful'
