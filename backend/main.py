from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI(title='Unstuck API')

TASKS = []
SPRINTS = []


class UnstuckRequest(BaseModel):
    avoiding: str
    blocker: str
    feeling: str


class TaskCreate(BaseModel):
    title: str
    category: str | None = None


class SprintCreate(BaseModel):
    minutes: int
    task_title: str | None = None


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.get('/api/today')
def today():
    open_tasks = [task for task in TASKS if not task['done']]
    return {
        'main_focus': open_tasks[0]['title'] if open_tasks else 'Start the most avoided meaningful task',
        'tasks': TASKS,
        'energy': 'unknown',
        'wins': [],
        'active_sprint': next((s for s in reversed(SPRINTS) if s['status'] == 'active'), None),
    }


@app.post('/api/tasks', status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    payload = {
        'id': len(TASKS) + 1,
        'title': task.title,
        'category': task.category,
        'done': False,
    }
    TASKS.append(payload)
    return payload


@app.post('/api/sprints', status_code=status.HTTP_201_CREATED)
def create_sprint(sprint: SprintCreate):
    payload = {
        'id': len(SPRINTS) + 1,
        'minutes': sprint.minutes,
        'task_title': sprint.task_title,
        'status': 'active',
    }
    SPRINTS.append(payload)
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
    return {
        'next_step': next_step,
        'suggested_sprint_minutes': 5,
        'reframe': f"You are feeling {request.feeling}. You do not need to finish, only begin.",
    }
