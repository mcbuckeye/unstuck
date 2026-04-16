import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import './styles.css'

const API = '/api'

function App() {
  const [today, setToday] = useState({ tasks: [], wins: [] })
  const [taskTitle, setTaskTitle] = useState('')
  const [stuckForm, setStuckForm] = useState({ avoiding: '', blocker: 'overwhelm', feeling: 'anxious' })
  const [unstuckResult, setUnstuckResult] = useState(null)

  async function loadToday() {
    const res = await fetch(`${API}/today`)
    setToday(await res.json())
  }

  useEffect(() => {
    loadToday()
  }, [])

  async function createTask(e) {
    e.preventDefault()
    if (!taskTitle.trim()) return
    await fetch(`${API}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: taskTitle, category: 'focus' }),
    })
    setTaskTitle('')
    loadToday()
  }

  async function submitUnstuck(e) {
    e.preventDefault()
    const res = await fetch(`${API}/unstuck`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(stuckForm),
    })
    const data = await res.json()
    setUnstuckResult(data)
  }

  async function startSprint(minutes) {
    await fetch(`${API}/sprints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ minutes, task_title: today.main_focus }),
    })
    loadToday()
  }

  return (
    <main className="app-shell">
      <header>
        <h1>Unstuck</h1>
        <p className="sub">A mobile-first focus coach for getting started.</p>
      </header>

      <section className="card primary">
        <h2>Today</h2>
        <p className="muted">Main focus</p>
        <p className="focus">{today.main_focus}</p>
        {today.active_sprint && <p className="pill">Active sprint: {today.active_sprint.minutes} min</p>}
      </section>

      <section className="card">
        <h2>Add a task</h2>
        <form onSubmit={createTask}>
          <input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="What needs to move today?" />
          <button type="submit">Add task</button>
        </form>
        <ul className="task-list">
          {today.tasks.map((task) => (
            <li key={task.id}>{task.title}</li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>I’m stuck</h2>
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
      </section>

      <section className="card">
        <h2>Quick sprint</h2>
        <div className="sprints">
          <button onClick={() => startSprint(5)}>5 min</button>
          <button onClick={() => startSprint(10)}>10 min</button>
          <button onClick={() => startSprint(25)}>25 min</button>
        </div>
      </section>
    </main>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
