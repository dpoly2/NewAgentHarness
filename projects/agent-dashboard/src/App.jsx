import React, { useState, useEffect } from 'react'

export default function App(){
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    function load() {
      if (window.electron && window.electron.getAgents) {
        const data = window.electron.getAgents()
        setAgents(data)
        if (!selected && data.length) setSelected(data[0].id)
      }
    }
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [])

  const selAgent = agents.find(a => a.id === selected) || agents[0]

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Agents</h2>
        <ul>
          {agents.map(a => (
            <li key={a.id} onClick={() => setSelected(a.id)} style={{ cursor: 'pointer', padding: 6, background: a.id === selected ? '#374151' : 'transparent' }}>
              <strong>{a.name}</strong>
              <br />
              <small>{a.status} — {a.progress}%</small>
            </li>
          ))}
        </ul>
        <button onClick={() => { if (window.electron && window.electron.getAgents) setAgents(window.electron.getAgents()) }}>Refresh</button>
      </aside>

      <main className="main">
        <header className="timeline">Human-speed progress timeline</header>
        <section className="chat">
          <h3>{selAgent ? selAgent.name : 'No agent selected'}</h3>
          <p>Status: {selAgent ? selAgent.status : '—'}</p>
          <div style={{ height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden', marginBottom: 8 }}>
            <div style={{ width: `${selAgent ? selAgent.progress : 0}%`, height: 8, background: '#10b981' }} />
          </div>
          <h4>Recent logs</h4>
          <div style={{ maxHeight: 200, overflow: 'auto', background: '#0f172a', color: '#fff', padding: 8 }}>
            {(selAgent && selAgent.logs) ? selAgent.logs.slice(-10).map((l, i) => (<div key={i}><small>{l}</small></div>)) : <small>No logs</small>}
          </div>
        </section>

        <section className="logs">
          <h4>All agents (raw)</h4>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(agents, null, 2)}</pre>
        </section>
      </main>
    </div>
  )
}
