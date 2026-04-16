from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='Unstuck API')


class UnstuckRequest(BaseModel):
    avoiding: str
    blocker: str
    feeling: str


@app.get('/api/health')
def healthcheck():
    return {'status': 'ok'}


@app.get('/api/today')
def today():
    return {
        'main_focus': 'Start the most avoided meaningful task',
        'tasks': [],
        'energy': 'unknown',
        'wins': [],
    }


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
