import React, { useEffect, useMemo, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Card, SectionTitle, StatsGrid } from './components'
import './styles.css'

const API = '/api'

function AuthGate({ onReady }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('signup')
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    const endpoint = mode === 'signup' ? '/auth/signup' : '/auth/login'
    const res = await fetch(`${API}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json()
    if (!res.ok) {
      setError(data.detail || 'Something went wrong')
      return
    }
    if (mode === 'signup') {
      onReady({ id: data.id, email })
    } else {
      onReady({ id: data.user_id, email })
    }
  }

  return (
    <Card>
      <SectionTitle>{mode === 'signup' ? 'Create your account' : 'Log in'}</SectionTitle>
      <form onSubmit={submit} className="stack">
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">{mode === 'signup' ? 'Sign up' : 'Log in'}</button>
      </form>
      <button className="ghost" onClick={() => setMode(mode === 'signup' ? 'login' : 'signup')}>
        Switch to {mode === 'signup' ? 'log in' : 'sign up'}
      </button>
    </Card>
  )
}

function App() {
  const [user, setUser] = useState(null)
  const [today, setToday] = useState({ tasks: [], wins: [], interventions: [] })
  const [taskTitle, setTaskTitle] = useState('')
  const [stuckForm, setStuckForm] = useState({ avoiding: '', blocker: 'overwhelm', feeling: 'anxious' })
  const [checkinForm, setCheckinForm] = useState({ energy: 'medium', mood: 'steady', clarity: 'clear', resistance: 'medium' })
  const [unstuckResult, setUnstuckResult] = useState(null)

  async function loadToday(activeUser = user) {
    if (!activeUser) return
    const res = await fetch(`${API}/today?user_id=${activeUser.id}`)
    setToday(await res.json())
  }

  useEffect(() => {
    loadToday()
  }, [user])

  async function createTask(e) {
    e.preventDefault()
    if (!taskTitle.trim()) return
    await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, title: taskTitle, category: 'focus' }),
    })
    setTaskTitle('')
    loadToday()
  }

  async function completeTask(taskId) {
    await fetch(`${API}/tasks/${taskId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id }),
    })
    loadToday()
  }

  async function submitUnstuck(e) {
    e.preventDefault()
    const res = await fetch(`${API}/unstuck`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...stuckForm, user_id: user.id }),
    })
    const data = await res.json()
    setUnstuckResult(data)
    loadToday()
  }

  async function startSprint(minutes) {
    await fetch(`${API}/sprints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, minutes, task_title: today.main_focus }),
    })
    loadToday()
  }

  async function completeSprint() {
    if (!today.active_sprint) return
    await fetch(`${API}/sprints/${today.active_sprint.id}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id }),
    })
    loadToday()
  }

  async function submitCheckin(e) {
    e.preventDefault()
    await fetch(`${API}/checkins`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...checkinForm, user_id: user.id }),
    })
    loadToday()
  }

  const stats = useMemo(() => ({
    tasksDone: today.wins?.length || 0,
    interventions: today.interventions?.length || 0,
  }), [today])

  if (!user) {
    return (
      <main className="app-shell">
        <header>
          <h1>Unstuck</h1>
          <p className="sub">A mobile-first focus coach for getting started.</p>
        </header>
        <AuthGate onReady={setUser} />
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header>
        <h1>Unstuck</h1>
        <p className="sub">Welcome back, {user.email}</p>
      </header>

      <Card className="primary">
        <SectionTitle>Today</SectionTitle>
        <p className="muted">Main focus</p>
        <p className="focus">{today.main_focus}</p>
        {today.active_sprint && (
          <>
            <p className="pill">Active sprint: {today.active_sprint.minutes} min</p>
            <button onClick={completeSprint}>Complete sprint</button>
          </>
        )}
      </Card>

      <Card>
        <SectionTitle>Daily check-in</SectionTitle>
        <form onSubmit={submitCheckin} className="stack compact">
          <select value={checkinForm.energy} onChange={(e) => setCheckinForm({ ...checkinForm, energy: e.target.value })}>
            <option value="low">Low energy</option>
            <option value="medium">Medium energy</option>
            <option value="high">High energy</option>
          </select>
          <select value={checkinForm.mood} onChange={(e) => setCheckinForm({ ...checkinForm, mood: e.target.value })}>
            <option value="steady">Steady</option>
            <option value="anxious">Anxious</option>
            <option value="frustrated">Frustrated</option>
            <option value="hopeful">Hopeful</option>
          </select>
          <select value={checkinForm.clarity} onChange={(e) => setCheckinForm({ ...checkinForm, clarity: e.target.value })}>
            <option value="clear">Clear</option>
            <option value="foggy">Foggy</option>
          </select>
          <select value={checkinForm.resistance} onChange={(e) => setCheckinForm({ ...checkinForm, resistance: e.target.value })}>
            <option value="low">Low resistance</option>
            <option value="medium">Medium resistance</option>
            <option value="high">High resistance</option>
          </select>
          <button type="submit">Save check-in</button>
        </form>
      </Card>

      <StatsGrid tasksDone={stats.tasksDone} interventions={stats.interventions} />

      <Card>
        <SectionTitle>Add a task</SectionTitle>
        <form onSubmit={createTask}>
          <input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="What needs to move today?" />
          <button type="submit">Add task</button>
        </form>
        <ul className="task-list">
          {today.tasks.map((task) => (
            <li key={task.id} className="task-row">
              <span>{task.title}</span>
              <button className="small" onClick={() => completeTask(task.id)}>Done</button>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>I’m stuck</SectionTitle>
        <form onSubmit={submitUnstuck} className="stack">
          <textarea
            value={stuckForm.avoiding}
            onChange={(e) => setStuckForm({ ...stuckForm, avoiding: e.target.value })}
            placeholder="What are you avoiding?"
          />
          <select value={stuckForm.blocker} onChange={(e) => setStuckForm({ ...stuckForm, blocker: e.target.value })}>
            <option value="overwhelm">Too big</option>
            <option value="ambiguity">Not clear</option>
            <option value="perfectionism">Want to do it perfectly</option>
            <option value="fear">Afraid or anxious</option>
            <option value="boredom">Boring</option>
            <option value="low_energy">Low energy</option>
          </select>
          <select value={stuckForm.feeling} onChange={(e) => setStuckForm({ ...stuckForm, feeling: e.target.value })}>
            <option value="anxious">Anxious</option>
            <option value="overwhelmed">Overwhelmed</option>
            <option value="frustrated">Frustrated</option>
            <option value="tired">Tired</option>
          </select>
          <button type="submit">Get unstuck</button>
        </form>
        {unstuckResult && (
          <div className="result">
            <p><strong>Reframe:</strong> {unstuckResult.reframe}</p>
            <p><strong>Next step:</strong> {unstuckResult.next_step}</p>
            <button onClick={() => startSprint(unstuckResult.suggested_sprint_minutes)}>
              Start {unstuckResult.suggested_sprint_minutes} minute sprint
            </button>
          </div>
        )}
      </Card>

      <Card>
        <SectionTitle>Recent interventions</SectionTitle>
        <ul className="task-list">
          {today.interventions.map((item) => (
            <li key={item.id}>{item.avoiding} → {item.next_step}</li>
          ))}
        </ul>
      </Card>

      <Card>
        <SectionTitle>Quick sprint</SectionTitle>
        <div className="sprints">
          <button onClick={() => startSprint(5)}>5 min</button>
          <button onClick={() => startSprint(10)}>10 min</button>
          <button onClick={() => startSprint(25)}>25 min</button>
        </div>
      </Card>
    </main>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
