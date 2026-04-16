import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles.css'

function App() {
  return (
    <main className="app-shell">
      <header>
        <h1>Unstuck</h1>
        <p className="sub">A mobile-first focus coach for getting started.</p>
      </header>

      <section className="card primary">
        <h2>Today</h2>
        <p>Your main focus: Start the most avoided meaningful task.</p>
        <button>I’m Stuck</button>
      </section>

      <section className="card">
        <h2>Quick Sprint</h2>
        <div className="sprints">
          <button>5 min</button>
          <button>10 min</button>
          <button>25 min</button>
        </div>
      </section>
    </main>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
