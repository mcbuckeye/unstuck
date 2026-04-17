import os
import time

from fastapi.testclient import TestClient
from jose import jwt

os.environ['DATABASE_URL'] = 'sqlite:///./unstuck_test.db'

from backend.auth import ALGORITHM, SECRET_KEY  # noqa: E402
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


# -- end-to-end user journey --

def test_full_user_journey():
    """Complete happy-path: signup → checkin → add tasks → get stuck → sprint → complete → verify dashboard."""
    # 1. Sign up and log in
    signup = client.post('/api/auth/signup', json={'email': 'journey@example.com', 'password': 'pass1234'})
    assert signup.status_code == 201
    login = client.post('/api/auth/login', json={'email': 'journey@example.com', 'password': 'pass1234'})
    assert login.status_code == 200
    token = login.json()['token']
    headers = auth_header(token)

    # 2. Daily check-in
    checkin = client.post('/api/checkins', json={'energy': 'low', 'mood': 'anxious', 'clarity': 'foggy', 'resistance': 'high'}, headers=headers)
    assert checkin.status_code == 201

    # 3. Add two tasks
    t1 = client.post('/api/tasks', json={'title': 'Write landing page', 'category': 'build'}, headers=headers)
    assert t1.status_code == 201
    t2 = client.post('/api/tasks', json={'title': 'Set up analytics', 'category': 'ops'}, headers=headers)
    assert t2.status_code == 201

    # 4. Get stuck on first task, use intervention
    unstuck = client.post('/api/unstuck', json={'avoiding': 'Write landing page', 'blocker': 'overwhelm', 'feeling': 'anxious'}, headers=headers)
    assert unstuck.status_code == 200
    assert unstuck.json()['suggested_sprint_minutes'] == 5

    # 5. Start and complete a sprint
    sprint = client.post('/api/sprints', json={'minutes': 5, 'task_title': 'Write landing page'}, headers=headers)
    assert sprint.status_code == 201
    sprint_id = sprint.json()['id']
    done_sprint = client.post(f'/api/sprints/{sprint_id}/complete', headers=headers)
    assert done_sprint.status_code == 200
    assert done_sprint.json()['status'] == 'completed'

    # 6. Complete first task
    task_id = t1.json()['id']
    client.post(f'/api/tasks/{task_id}/complete', headers=headers)

    # 7. Verify dashboard state
    today = client.get('/api/today', headers=headers).json()
    assert today['energy'] == 'low'
    assert 'Write landing page' in today['wins']
    assert len(today['interventions']) == 1
    assert today['active_sprint'] is None  # sprint is completed
    assert any(t['title'] == 'Set up analytics' for t in today['tasks'])
    assert all(t['title'] != 'Write landing page' for t in today['tasks'])


def test_multi_user_isolation():
    """Two users should never see each other's data."""
    token_a, _ = signup_and_login('alice@example.com', 'pass1234')
    token_b, _ = signup_and_login('bob@example.com', 'pass1234')

    client.post('/api/tasks', json={'title': 'Alice task'}, headers=auth_header(token_a))
    client.post('/api/tasks', json={'title': 'Bob task'}, headers=auth_header(token_b))
    client.post('/api/unstuck', json={'avoiding': 'Alice stuck', 'blocker': 'fear', 'feeling': 'anxious'}, headers=auth_header(token_a))
    client.post('/api/checkins', json={'energy': 'high', 'mood': 'hopeful', 'clarity': 'clear', 'resistance': 'low'}, headers=auth_header(token_b))

    today_a = client.get('/api/today', headers=auth_header(token_a)).json()
    today_b = client.get('/api/today', headers=auth_header(token_b)).json()

    assert any(t['title'] == 'Alice task' for t in today_a['tasks'])
    assert all(t['title'] != 'Bob task' for t in today_a['tasks'])
    assert any(t['title'] == 'Bob task' for t in today_b['tasks'])
    assert all(t['title'] != 'Alice task' for t in today_b['tasks'])
    assert len(today_a['interventions']) == 1
    assert len(today_b['interventions']) == 0
    assert today_a['energy'] == 'unknown'
    assert today_b['energy'] == 'high'


# -- auth: expired and tampered tokens --

def test_expired_token_returns_401():
    """An expired JWT should be rejected."""
    expired_payload = {'sub': '999', 'email': 'x@example.com', 'exp': time.time() - 60}
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    resp = client.get('/api/today', headers={'Authorization': f'Bearer {expired_token}'})
    assert resp.status_code == 401


def test_token_with_wrong_secret_returns_401():
    """A JWT signed with a different secret should be rejected."""
    bad_token = jwt.encode({'sub': '1', 'email': 'x@example.com', 'exp': time.time() + 3600}, 'wrong-secret', algorithm=ALGORITHM)
    resp = client.get('/api/today', headers={'Authorization': f'Bearer {bad_token}'})
    assert resp.status_code == 401


# -- auth required on all protected endpoints --

def test_sprints_require_auth():
    resp = client.post('/api/sprints', json={'minutes': 10})
    assert resp.status_code == 401


def test_sprint_complete_requires_auth():
    resp = client.post('/api/sprints/1/complete')
    assert resp.status_code == 401


def test_checkins_require_auth():
    resp = client.post('/api/checkins', json={'energy': 'low', 'mood': 'steady', 'clarity': 'clear', 'resistance': 'low'})
    assert resp.status_code == 401


def test_unstuck_requires_auth():
    resp = client.post('/api/unstuck', json={'avoiding': 'thing', 'blocker': 'fear', 'feeling': 'anxious'})
    assert resp.status_code == 401


# -- additional validation --

def test_checkin_rejects_invalid_mood():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/checkins',
        json={'energy': 'low', 'mood': 'ecstatic', 'clarity': 'clear', 'resistance': 'low'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_checkin_rejects_invalid_clarity():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/checkins',
        json={'energy': 'low', 'mood': 'steady', 'clarity': 'blurry', 'resistance': 'low'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_checkin_rejects_invalid_resistance():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/checkins',
        json={'energy': 'low', 'mood': 'steady', 'clarity': 'clear', 'resistance': 'extreme'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_unstuck_rejects_blank_avoiding():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/unstuck',
        json={'avoiding': '', 'blocker': 'fear', 'feeling': 'anxious'},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_unstuck_rejects_blank_feeling():
    token, uid = signup_and_login()
    resp = client.post(
        '/api/unstuck',
        json={'avoiding': 'thing', 'blocker': 'fear', 'feeling': ''},
        headers=auth_header(token),
    )
    assert resp.status_code == 422


# -- blocker-specific next_step values --

def test_each_blocker_returns_correct_next_step():
    """Each blocker type should map to a specific intervention."""
    token, uid = signup_and_login()
    expected = {
        'overwhelm': 'Reduce the task to a 5 minute visible action',
        'ambiguity': 'Write down the first concrete action',
        'perfectionism': 'Create a messy first version',
        'fear': 'Do the smallest safe move',
        'boredom': 'Start with the easiest meaningful fragment',
        'low_energy': 'Choose a lighter version of the task',
    }
    for blocker, expected_step in expected.items():
        resp = client.post(
            '/api/unstuck',
            json={'avoiding': f'Task for {blocker}', 'blocker': blocker, 'feeling': 'anxious'},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()['next_step'] == expected_step, f'Wrong next_step for {blocker}'


# -- optional fields --

def test_create_task_without_category():
    token, uid = signup_and_login()
    resp = client.post('/api/tasks', json={'title': 'No category task'}, headers=auth_header(token))
    assert resp.status_code == 201
    assert resp.json()['category'] is None


def test_create_sprint_without_task_title():
    token, uid = signup_and_login()
    resp = client.post('/api/sprints', json={'minutes': 15}, headers=auth_header(token))
    assert resp.status_code == 201
    assert resp.json()['task_title'] is None


# -- login response structure --

def test_login_response_includes_token_and_user_id():
    client.post('/api/auth/signup', json={'email': 'struct@example.com', 'password': 'secret123'})
    resp = client.post('/api/auth/login', json={'email': 'struct@example.com', 'password': 'secret123'})
    assert resp.status_code == 200
    body = resp.json()
    assert 'token' in body
    assert 'user_id' in body
    assert isinstance(body['user_id'], int)
    assert body['token'].count('.') == 2  # valid JWT structure
    assert 'password' not in body
    assert 'password_hash' not in body


# -- session safety: operations succeed even after prior errors --

def test_404_does_not_break_subsequent_requests():
    """After a 404, subsequent requests should still work (no leaked sessions)."""
    token, uid = signup_and_login()
    # trigger a 404
    resp = client.post('/api/tasks/99999/complete', headers=auth_header(token))
    assert resp.status_code == 404
    # subsequent request should succeed
    resp = client.post('/api/tasks', json={'title': 'After 404'}, headers=auth_header(token))
    assert resp.status_code == 201


# -- migration consistency --

def test_alembic_models_match_migration():
    """Verify all ORM tables are present in the database after init_db."""
    from backend.db import Base, engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables.keys())
    assert model_tables.issubset(db_tables), f'Missing tables: {model_tables - db_tables}'


# -- deployment config validation --

def test_cors_includes_deploy_hostname():
    """CORS origins must include the production deploy hostname."""
    from backend.main import app
    cors_mw = next(
        (m for m in app.user_middleware if m.cls.__name__ == 'CORSMiddleware'),
        None,
    )
    assert cors_mw is not None, 'CORSMiddleware not found'
    origins = cors_mw.kwargs.get('allow_origins', [])
    assert 'https://unstuckinator.machomelab.com' in origins, (
        f'Deploy host missing from CORS origins: {origins}'
    )


def test_compose_has_traefik_labels():
    """docker-compose.yml must define Traefik routing labels for both services."""
    import yaml
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    for svc_name in ('unstuckinator-backend', 'unstuckinator-frontend'):
        svc = compose['services'][svc_name]
        labels = svc.get('labels', [])
        joined = '\n'.join(labels) if isinstance(labels, list) else str(labels)
        assert 'traefik.enable=true' in joined, f'{svc_name} missing traefik.enable label'
        assert 'traefik.http.routers.' in joined, f'{svc_name} missing traefik router label'
        assert 'loadbalancer.server.port' in joined, f'{svc_name} missing loadbalancer port label'


def test_compose_services_on_dokploy_network():
    """Both services must be attached to the external dokploy-network."""
    import yaml
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    assert compose['networks']['dokploy-network']['external'] is True
    for svc_name in ('unstuckinator-backend', 'unstuckinator-frontend'):
        nets = compose['services'][svc_name].get('networks', [])
        assert 'dokploy-network' in nets, f'{svc_name} not on dokploy-network'
