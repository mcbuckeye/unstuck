from enum import Enum
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.db import Checkin, Intervention, Sprint, Task, User, drop_db, get_db, init_db

app = FastAPI(title='Unstuckinator API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'https://unstuckinator.com',
        'https://www.unstuckinator.com',
        'https://unstuckinator.machomelab.com',
        'http://localhost:3000',
        'http://localhost:3060',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

init_db()


def reset_state():
    drop_db()
    init_db()


# -- request schemas with validation --


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    category: str | None = None


class SprintCreate(BaseModel):
    minutes: int = Field(gt=0, le=120)
    task_title: str | None = None


class BlockerType(str, Enum):
    overwhelm = 'overwhelm'
    ambiguity = 'ambiguity'
    perfectionism = 'perfectionism'
    fear = 'fear'
    boredom = 'boredom'
    low_energy = 'low_energy'


class UnstuckRequest(BaseModel):
    avoiding: str = Field(min_length=1)
    blocker: BlockerType
    feeling: str = Field(min_length=1)


class CheckinCreate(BaseModel):
    energy: Literal['low', 'medium', 'high']
    mood: Literal['steady', 'anxious', 'frustrated', 'hopeful']
    clarity: Literal['clear', 'foggy']
    resistance: Literal['low', 'medium', 'high']


# -- public endpoints --


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok', 'name': 'Unstuckinator API'}


@app.post('/api/auth/signup', status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, session=Depends(get_db)):
    existing = session.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='User already exists')

    user = User(email=request.email, password_hash=hash_password(request.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {'id': user.id, 'email': user.email}


@app.post('/api/auth/login')
def login(request: LoginRequest, session=Depends(get_db)):
    user = session.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_access_token(user.id, user.email)
    return {'token': token, 'user_id': user.id}


# -- protected endpoints --


@app.get('/api/today')
def today(current_user: User = Depends(get_current_user), session=Depends(get_db)):
    uid = current_user.id
    open_tasks = session.query(Task).filter(Task.user_id == uid, Task.done.is_(False)).all()
    interventions = session.query(Intervention).filter(Intervention.user_id == uid).all()
    active_sprint = session.query(Sprint).filter(Sprint.user_id == uid, Sprint.status == 'active').order_by(Sprint.id.desc()).first()
    latest_checkin = session.query(Checkin).filter(Checkin.user_id == uid).order_by(Checkin.id.desc()).first()
    wins = session.query(Task).filter(Task.user_id == uid, Task.done.is_(True)).all()
    return {
        'main_focus': open_tasks[0].title if open_tasks else 'Start the most avoided meaningful task',
        'tasks': [{'id': t.id, 'title': t.title, 'category': t.category, 'done': t.done} for t in open_tasks],
        'energy': latest_checkin.energy if latest_checkin else 'unknown',
        'wins': [task.title for task in wins],
        'active_sprint': None if not active_sprint else {'id': active_sprint.id, 'minutes': active_sprint.minutes, 'task_title': active_sprint.task_title, 'status': active_sprint.status},
        'interventions': [{'id': i.id, 'avoiding': i.avoiding, 'blocker': i.blocker, 'feeling': i.feeling, 'next_step': i.next_step} for i in interventions],
        'latest_checkin': None if not latest_checkin else {'id': latest_checkin.id, 'energy': latest_checkin.energy, 'mood': latest_checkin.mood, 'clarity': latest_checkin.clarity, 'resistance': latest_checkin.resistance},
    }


@app.post('/api/tasks', status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    row = Task(user_id=current_user.id, title=task.title, category=task.category, done=False)
    session.add(row)
    session.commit()
    session.refresh(row)
    return {'id': row.id, 'user_id': row.user_id, 'title': row.title, 'category': row.category, 'done': row.done}


@app.post('/api/tasks/{task_id}/complete')
def complete_task(task_id: int, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    task = session.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    task.done = True
    session.commit()
    return {'id': task.id, 'user_id': task.user_id, 'title': task.title, 'category': task.category, 'done': task.done}


@app.post('/api/sprints', status_code=status.HTTP_201_CREATED)
def create_sprint(sprint: SprintCreate, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    row = Sprint(user_id=current_user.id, minutes=sprint.minutes, task_title=sprint.task_title, status='active')
    session.add(row)
    session.commit()
    session.refresh(row)
    return {'id': row.id, 'user_id': row.user_id, 'minutes': row.minutes, 'task_title': row.task_title, 'status': row.status}


@app.post('/api/sprints/{sprint_id}/complete')
def complete_sprint(sprint_id: int, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    sprint = session.query(Sprint).filter(Sprint.id == sprint_id, Sprint.user_id == current_user.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail='Sprint not found')
    sprint.status = 'completed'
    session.commit()
    return {'id': sprint.id, 'user_id': sprint.user_id, 'minutes': sprint.minutes, 'task_title': sprint.task_title, 'status': sprint.status}


@app.post('/api/checkins', status_code=status.HTTP_201_CREATED)
def create_checkin(checkin: CheckinCreate, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    row = Checkin(user_id=current_user.id, energy=checkin.energy, mood=checkin.mood, clarity=checkin.clarity, resistance=checkin.resistance)
    session.add(row)
    session.commit()
    session.refresh(row)
    return {'id': row.id, 'user_id': row.user_id, 'energy': row.energy, 'mood': row.mood, 'clarity': row.clarity, 'resistance': row.resistance}


@app.post('/api/unstuck')
def unstuck_flow(request: UnstuckRequest, current_user: User = Depends(get_current_user), session=Depends(get_db)):
    next_step_map = {
        'overwhelm': 'Reduce the task to a 5 minute visible action',
        'ambiguity': 'Write down the first concrete action',
        'perfectionism': 'Create a messy first version',
        'fear': 'Do the smallest safe move',
        'boredom': 'Start with the easiest meaningful fragment',
        'low_energy': 'Choose a lighter version of the task',
    }
    next_step = next_step_map.get(request.blocker.value, 'Do the smallest next step you can do now')
    record = Intervention(user_id=current_user.id, avoiding=request.avoiding, blocker=request.blocker.value, feeling=request.feeling, next_step=next_step)
    session.add(record)
    session.commit()
    return {
        'next_step': next_step,
        'suggested_sprint_minutes': 5,
        'reframe': f"You are feeling {request.feeling}. You do not need to finish, only begin.",
    }
