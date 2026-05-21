import React, { useState, useEffect } from 'react'

export default function App(){
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        if (window.electron && window.electron.getAgents) {
          const maybe = window.electron.getAgents()
          const data = (maybe && typeof maybe.then === 'function') ? await maybe : maybe
          console.log('Loaded agents', data)
          if (!mounted) return
          setAgents(data || [])
          if (!selected && data && data.length) setSelected(data[0].id)
        }
      } catch (e) {
        console.error('Failed to load agents', e)
      }
    }
    load()
    const t = setInterval(load, 3000)
    // Listen for real-time updates
    if (window.electron && window.electron.on) {
      window.electron.on('agents-updated', (data) => { if (mounted) setAgents(data || []) })
    }
    return () => { mounted = false; clearInterval(t) }
  }, [])

  const selAgent = (Array.isArray(agents) ? agents.find(a => a.id === selected) : null) || (Array.isArray(agents) ? agents[0] : null)

  async function commandAgent(id, action) {
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      await window.electron.invoke('agent-command', { id, action })
      // Refresh local copy
      const maybe = window.electron.getAgents()
      const data = (maybe && typeof maybe.then === 'function') ? await maybe : maybe
      setAgents(data || [])
    } catch (e) {
      console.error('agent command failed', e)
    } finally {
      setBusy(false)
    }
  }

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
        <button onClick={() => { if (window.electron && window.electron.getAgents) { const m = window.electron.getAgents(); if (m && typeof m.then === 'function') { m.then(d => setAgents(d||[])) } else { setAgents(m||[]) } } }}>Refresh</button>
      </aside>

      <main className="main">
        <header className="timeline">Human-speed progress timeline</header>
        <section className="chat">
          <h3>{selAgent ? selAgent.name : 'No agent selected'}</h3>
          <p>Status: {selAgent ? selAgent.status : '—'}</p>

          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button disabled={!selAgent || busy || (selAgent && selAgent.status === 'running')} onClick={() => commandAgent(selAgent.id, 'start')}>
              {busy ? 'Working...' : 'Start'}
            </button>
            <button disabled={!selAgent || busy || (selAgent && selAgent.status !== 'running')} onClick={() => commandAgent(selAgent.id, 'stop')}>
              {busy ? 'Working...' : 'Stop'}
            </button>
            <button disabled={!selAgent || busy} onClick={() => commandAgent(selAgent.id, 'ping')}>
              {busy ? 'Working...' : 'Ping'}
            </button>
          </div>

          <div className="progress-outer" aria-hidden={!selAgent}>
            <div className="progress-inner" style={{ width: `${selAgent ? Math.max(0, Math.min(100, selAgent.progress || 0)) : 0}%` }} />
          </div>
          {selAgent && <div><small>{selAgent.progress ?? 0}% complete</small></div> }
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
