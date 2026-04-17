import React from 'react'

export function Card({ children, className = '' }) {
  return <section className={`card ${className}`.trim()}>{children}</section>
}

export function SectionTitle({ children }) {
  return <h2>{children}</h2>
}

export function StatsGrid({ tasksDone, interventions }) {
  return (
    <section className="card stats-grid">
      <div>
        <p className="muted">Completed tasks</p>
        <strong>{tasksDone}</strong>
      </div>
      <div>
        <p className="muted">Recovered stuck moments</p>
        <strong>{interventions}</strong>
      </div>
    </section>
  )
}
