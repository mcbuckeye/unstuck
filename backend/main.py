from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel

app = FastAPI(title='Unstuck API')

USERS = []
TASKS = []
SPRINTS = []
INTERVENTIONS = []
CHECKINS = []


def reset_state():
    USERS.clear()
    TASKS.clear()
    SPRINTS.clear()
    INTERVENTIONS.clear()
    CHECKINS.clear()


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TaskCreate(BaseModel):
    user_id: int
    title: str
    category: str | None = None


class UserRef(BaseModel):
    user_id: int


class SprintCreate(BaseModel):
    user_id: int
    minutes: int
    task_title: str | None = None


class UnstuckRequest(BaseModel):
    user_id: int
    avoiding: str
    blocker: str
    feeling: str


class CheckinCreate(BaseModel):
    user_id: int
    energy: str
    mood: str
    clarity: str
    resistance: str


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.post('/api/auth/signup', status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest):
    if any(user['email'] == request.email for user in USERS):
        raise HTTPException(status_code=400, detail='User already exists')

    user = {
        'id': len(USERS) + 1,
        'email': request.email,
        'password': request.password,
    }
    USERS.append(user)
    return {'id': user['id'], 'email': user['email']}


@app.post('/api/auth/login')
def login(request: LoginRequest):
    user = next((user for user in USERS if user['email'] == request.email and user['password'] == request.password), None)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return {'token': f"demo-token-{user['id']}", 'user_id': user['id']}


@app.get('/api/today')
def today(user_id: int = Query(...)):
    open_tasks = [task for task in TASKS if task['user_id'] == user_id and not task['done']]
    interventions = [item for item in INTERVENTIONS if item['user_id'] == user_id]
    active_sprint = next((s for s in reversed(SPRINTS) if s['user_id'] == user_id and s['status'] == 'active'), None)
    latest_checkin = next((c for c in reversed(CHECKINS) if c['user_id'] == user_id), None)
    return {
        'main_focus': open_tasks[0]['title'] if open_tasks else 'Start the most avoided meaningful task',
        'tasks': open_tasks,
        'energy': latest_checkin['energy'] if latest_checkin else 'unknown',
        'wins': [task['title'] for task in TASKS if task['user_id'] == user_id and task['done']],
        'active_sprint': active_sprint,
        'interventions': interventions,
        'latest_checkin': latest_checkin,
    }


@app.post('/api/tasks', status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    payload = {
        'id': len(TASKS) + 1,
        'user_id': task.user_id,
        'title': task.title,
        'category': task.category,
        'done': False,
    }
    TASKS.append(payload)
    return payload


@app.post('/api/tasks/{task_id}/complete')
def complete_task(task_id: int, request: UserRef):
    task = next((task for task in TASKS if task['id'] == task_id and task['user_id'] == request.user_id), None)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    task['done'] = True
    return task


@app.post('/api/sprints', status_code=status.HTTP_201_CREATED)
def create_sprint(sprint: SprintCreate):
    payload = {
        'id': len(SPRINTS) + 1,
        'user_id': sprint.user_id,
        'minutes': sprint.minutes,
        'task_title': sprint.task_title,
        'status': 'active',
    }
    SPRINTS.append(payload)
    return payload


@app.post('/api/sprints/{sprint_id}/complete')
def complete_sprint(sprint_id: int, request: UserRef):
    sprint = next((s for s in SPRINTS if s['id'] == sprint_id and s['user_id'] == request.user_id), None)
    if not sprint:
        raise HTTPException(status_code=404, detail='Sprint not found')
    sprint['status'] = 'completed'
    return sprint


@app.post('/api/checkins', status_code=status.HTTP_201_CREATED)
def create_checkin(checkin: CheckinCreate):
    payload = {
        'id': len(CHECKINS) + 1,
        'user_id': checkin.user_id,
        'energy': checkin.energy,
        'mood': checkin.mood,
        'clarity': checkin.clarity,
        'resistance': checkin.resistance,
    }
    CHECKINS.append(payload)
    return payload


@app.post('/api/unstuck')
def unstuck_flow(request: UnstuckRequest):
    next_step_map = {
        'overwhelm': 'Reduce the task to a 5 minute visible action',
        'ambiguity': 'Write down the first concrete action',
        'perfectionism': 'Create a messy first version',
        'fear': 'Do the smallest safe move',
        'boredom': 'Start with the easiest meaningful fragment',
        'low_energy': 'Choose a lighter version of the task',
    }
    next_step = next_step_map.get(request.blocker, 'Do the smallest next step you can do now')
    record = {
        'id': len(INTERVENTIONS) + 1,
        'user_id': request.user_id,
        'avoiding': request.avoiding,
        'blocker': request.blocker,
        'feeling': request.feeling,
        'next_step': next_step,
    }
    INTERVENTIONS.append(record)
    return {
        'next_step': next_step,
        'suggested_sprint_minutes': 5,
        'reframe': f"You are feeling {request.feeling}. You do not need to finish, only begin.",
    }
