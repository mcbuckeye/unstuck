import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Card, SectionTitle, StatsGrid } from './components'
import './styles.css'

const API = '/api'

function authHeaders(token) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

async function apiFetch(path, { token, method = 'GET', body } = {}) {
  const opts = { method, headers: authHeaders(token) }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(`${API}${path}`, opts)
  if (res.status === 401) {
    localStorage.removeItem('unstuckinator_token')
    localStorage.removeItem('unstuckinator_user')
    window.location.reload()
    return null
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

function AuthGate({ onReady }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('signup')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
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
        const loginRes = await fetch(`${API}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })
        const loginData = await loginRes.json()
        if (!loginRes.ok) {
          setError(loginData.detail || 'Login after signup failed')
          return
        }
        const user = { id: loginData.user_id, email, token: loginData.token }
        localStorage.setItem('unstuckinator_token', loginData.token)
        localStorage.setItem('unstuckinator_user', JSON.stringify({ id: loginData.user_id, email }))
        onReady(user)
      } else {
        const user = { id: data.user_id, email, token: data.token }
        localStorage.setItem('unstuckinator_token', data.token)
        localStorage.setItem('unstuckinator_user', JSON.stringify({ id: data.user_id, email }))
        onReady(user)
      }
    } catch {
      setError('Network error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <SectionTitle>{mode === 'signup' ? 'Create your account' : 'Log in'}</SectionTitle>
      <form onSubmit={submit} className="stack">
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" type="email" required />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" minLength={6} required />
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={loading}>
          {loading ? 'Working...' : mode === 'signup' ? 'Sign up' : 'Log in'}
        </button>
      </form>
      <button className="ghost" onClick={() => { setMode(mode === 'signup' ? 'login' : 'signup'); setError('') }}>
        Switch to {mode === 'signup' ? 'log in' : 'sign up'}
      </button>
    </Card>
  )
}

function App() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('unstuckinator_token')
    const stored = localStorage.getItem('unstuckinator_user')
    if (token && stored) {
      try {
        const parsed = JSON.parse(stored)
        return { ...parsed, token }
      } catch {
        return null
      }
    }
    return null
  })
  const [today, setToday] = useState({ tasks: [], wins: [], interventions: [] })
  const [taskTitle, setTaskTitle] = useState('')
  const [stuckForm, setStuckForm] = useState({ avoiding: '', blocker: 'overwhelm', feeling: 'anxious' })
  const [checkinForm, setCheckinForm] = useState({ energy: 'medium', mood: 'steady', clarity: 'clear', resistance: 'medium' })
  const [unstuckResult, setUnstuckResult] = useState(null)
  const [error, setError] = useState('')
  const errorTimer = useRef(null)

  const showError = useCallback((msg) => {
    setError(msg)
    clearTimeout(errorTimer.current)
    errorTimer.current = setTimeout(() => setError(''), 5000)
  }, [])

  function logout() {
    localStorage.removeItem('unstuckinator_token')
    localStorage.removeItem('unstuckinator_user')
    setUser(null)
    setToday({ tasks: [], wins: [], interventions: [] })
  }

  const loadToday = useCallback(async (activeUser = user) => {
    if (!activeUser) return
    try {
      const data = await apiFetch('/today', { token: activeUser.token })
      if (data) setToday(data)
    } catch {
      showError('Failed to load data')
    }
  }, [user, showError])

  useEffect(() => {
    loadToday()
  }, [loadToday])

  async function createTask(e) {
    e.preventDefault()
    if (!taskTitle.trim()) return
    try {
      await apiFetch('/tasks', { token: user.token, method: 'POST', body: { title: taskTitle, category: 'focus' } })
      setTaskTitle('')
      loadToday()
    } catch {
      showError('Failed to create task')
    }
  }

  async function completeTask(taskId) {
    try {
      await apiFetch(`/tasks/${taskId}/complete`, { token: user.token, method: 'POST' })
      loadToday()
    } catch {
      showError('Failed to complete task')
    }
  }

  async function submitUnstuck(e) {
    e.preventDefault()
    try {
      const data = await apiFetch('/unstuck', { token: user.token, method: 'POST', body: stuckForm })
      setUnstuckResult(data)
      loadToday()
    } catch {
      showError('Failed to process')
    }
  }

  async function startSprint(minutes) {
    try {
      await apiFetch('/sprints', { token: user.token, method: 'POST', body: { minutes, task_title: today.main_focus } })
      loadToday()
    } catch {
      showError('Failed to start sprint')
    }
  }

  async function completeSprint() {
    if (!today.active_sprint) return
    try {
      await apiFetch(`/sprints/${today.active_sprint.id}/complete`, { token: user.token, method: 'POST' })
      loadToday()
    } catch {
      showError('Failed to complete sprint')
    }
  }

  async function submitCheckin(e) {
    e.preventDefault()
    try {
      await apiFetch('/checkins', { token: user.token, method: 'POST', body: checkinForm })
      loadToday()
    } catch {
      showError('Failed to save check-in')
    }
  }

  const stats = useMemo(() => ({
    tasksDone: today.wins?.length || 0,
    interventions: today.interventions?.length || 0,
  }), [today])

  if (!user) {
    return (
      <main className="app-shell">
        <header>
          <h1>Unstuckinator</h1>
          <p className="sub">A mobile-first focus coach for getting unstuck and started.</p>
        </header>
        <AuthGate onReady={setUser} />
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header>
        <h1>Unstuckinator</h1>
        <div className="header-row">
          <p className="sub">Welcome back, {user.email}</p>
          <button className="ghost small" onClick={logout}>Log out</button>
        </div>
      </header>

      {error && (
        <Card className="error-card">
          <p className="error">{error}</p>
          <button className="ghost small" onClick={() => setError('')}>Dismiss</button>
        </Card>
      )}

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
        {today.tasks.length === 0 ? (
          <p className="muted">No open tasks yet. Add one above to get started.</p>
        ) : (
          <ul className="task-list">
            {today.tasks.map((task) => (
              <li key={task.id} className="task-row">
                <span>{task.title}</span>
                <button className="small" onClick={() => completeTask(task.id)}>Done</button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <SectionTitle>I'm stuck</SectionTitle>
        <form onSubmit={submitUnstuck} className="stack">
          <textarea
            value={stuckForm.avoiding}
            onChange={(e) => setStuckForm({ ...stuckForm, avoiding: e.target.value })}
            placeholder="What are you avoiding?"
            required
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
        {today.interventions.length === 0 ? (
          <p className="muted">No interventions yet. Use "I'm stuck" when you feel blocked.</p>
        ) : (
          <ul className="task-list">
            {today.interventions.map((item) => (
              <li key={item.id}>{item.avoiding} → {item.next_step}</li>
            ))}
          </ul>
        )}
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
