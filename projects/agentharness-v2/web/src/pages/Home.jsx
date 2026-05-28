import { useState, useEffect } from 'react'
import { api, useSocket } from '../hooks/useSocket'

const STATUS_DOT = { active: '🟢', 'in-progress': '🟡', blocked: '🔴' }
const ICONS = { xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️', ministry:'⛪', finance:'💰', personal:'🗓️', 'sigma-signal':'📰', global:'✨' }

export default function Home({ roster }) {
  const [tasks, setTasks] = useState({ running: [], queued: [], recent: [] })
  const [todos, setTodos] = useState([])
  const [notifs, setNotifs] = useState([])
  const [brief, setBrief] = useState(null)
  const [showBrief, setShowBrief] = useState(false)
  const [aiStatus, setAiStatus] = useState(null) // null=checking, {ok,provider,error}

  useSocket({
    'task:queued': t => setTasks(p => ({ ...p, queued: [t, ...p.queued] })),
    'task:started': t => setTasks(p => ({ ...p, running: [t, ...p.running.filter(x => x.id !== t.id)], queued: p.queued.filter(x => x.id !== t.id) })),
    'task:completed': t => setTasks(p => ({ ...p, running: p.running.filter(x => x.id !== t.id), recent: [t, ...p.recent].slice(0, 10) })),
    'todo:created': t => setTodos(p => [t, ...p].slice(0, 20)),
    'notification:new': n => setNotifs(p => [n, ...p].slice(0, 10)),
    'briefing:ready': b => setBrief(b)
  })

  useEffect(() => {
    api('/tasks/queue').then(setTasks).catch(console.error)
    api('/todos?status=pending').then(setTodos).catch(console.error)
    api('/settings/notifications').then(n => setNotifs(n.slice(0, 10))).catch(console.error)
    api('/settings/briefings').then(b => { if (b.length) setBrief(b[0]) }).catch(console.error)
    // Check AI connectivity silently
    api('/settings/ai/test', { method: 'POST', body: {} }).then(setAiStatus).catch(() => setAiStatus({ ok: false, error: 'AI not reachable' }))
  }, [])

  const projects = roster?.projects || []
  const openItems = roster?.openItems || []
  const urgentCount = openItems.filter(o => o.priority.includes('🔴')).length
  const highCount = openItems.filter(o => o.priority.includes('🟡')).length

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Portfolio Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div className="flex items-center gap-3">
          {aiStatus !== null && (
            <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${
              aiStatus.ok
                ? 'border-success/30 bg-success/10 text-success'
                : 'border-error/30 bg-error/10 text-error'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${aiStatus.ok ? 'bg-success' : 'bg-error'}`} />
              {aiStatus.ok ? `AI: ${aiStatus.provider}` : 'AI: offline'}
            </div>
          )}
          {brief && (
            <button onClick={() => setShowBrief(true)} className="btn-primary text-sm">
              📋 Morning Briefing
            </button>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Running Tasks" value={tasks.running.length + tasks.queued.length} sub={`${tasks.running.length} active, ${tasks.queued.length} queued`} color="blue" />
        <StatCard label="Open Items" value={urgentCount + highCount} sub={`${urgentCount} urgent, ${highCount} high`} color="red" />
        <StatCard label="Open Todos" value={todos.length} sub="across all projects" color="yellow" />
        <StatCard label="Projects" value={projects.length} sub="active portfolios" color="green" />
      </div>

      {/* Running tasks */}
      {(tasks.running.length > 0 || tasks.queued.length > 0) && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <span className="text-blue-400">⚡</span> Active Agent Tasks
          </h2>
          <div className="space-y-2">
            {[...tasks.running, ...tasks.queued].map(t => (
              <div key={t.id} className="flex items-center gap-3 px-3 py-2 bg-surface rounded-lg border border-surface-border">
                <span className={t.status === 'running' ? 'status-running' : 'status-queued'}>{t.status}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-white truncate">{t.title}</div>
                  <div className="text-xs text-gray-500 truncate">{t.agent_id}</div>
                </div>
                <span className="text-xs text-gray-600 flex-shrink-0">{t.project_slug}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Project health grid */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 mb-3">Project Health</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {projects.map(proj => (
            <ProjectHealthCard key={proj.slug} proj={proj} tasks={tasks} todos={todos} openItems={openItems} />
          ))}
        </div>
      </div>

      {/* Open items strip */}
      {openItems.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <span className="text-red-400">🚨</span> Open Items — Needs Attention
          </h2>
          <div className="space-y-2">
            {openItems.slice(0, 8).map((item, i) => (
              <div key={i} className="flex items-start gap-3 text-sm py-1.5 border-b border-surface-border last:border-0">
                <span className="flex-shrink-0 text-base leading-5">{item.priority.includes('🔴') ? '🔴' : item.priority.includes('🟡') ? '🟡' : '🟢'}</span>
                <span className="flex-1 text-gray-200">{item.item}</span>
                <span className="text-xs text-gray-500 flex-shrink-0 text-right">{item.project}<br/>{item.deadline}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Morning briefing modal */}
      {showBrief && brief && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowBrief(false)}>
          <div className="bg-surface-light border border-surface-border rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-white">Morning Briefing</h2>
              <button onClick={() => setShowBrief(false)} className="btn-ghost text-xs">✕ Close</button>
            </div>
            <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: brief.content?.replace(/\n/g, '<br>') || '' }} />
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, sub, color }) {
  const colors = { blue: 'text-blue-400 bg-blue-400/10', red: 'text-red-400 bg-red-400/10', yellow: 'text-yellow-400 bg-yellow-400/10', green: 'text-green-400 bg-green-400/10' }
  return (
    <div className="card-sm flex items-center gap-3">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl font-bold ${colors[color]}`}>{value}</div>
      <div>
        <div className="text-sm font-medium text-white">{label}</div>
        <div className="text-xs text-gray-500">{sub}</div>
      </div>
    </div>
  )
}

function ProjectHealthCard({ proj, tasks, todos, openItems }) {
  const ICONS = { xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️', ministry:'⛪', finance:'💰', personal:'🗓️', global:'✨' }
  const projTasks = [...(tasks.running || []), ...(tasks.queued || [])].filter(t => t.project_slug === proj.slug)
  const projTodos = todos.filter(t => t.project_slug === proj.slug)
  const projItems = openItems.filter(o => o.project?.toLowerCase().includes(proj.name?.split(' ')[0]?.toLowerCase()))
  return (
    <div className="card-sm hover:border-surface-border hover:bg-surface-lighter transition-colors cursor-pointer">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{ICONS[proj.slug] || '📁'}</span>
          <div>
            <div className="text-sm font-medium text-white leading-tight">{proj.name}</div>
            <div className="text-xs text-gray-500">{proj.statusLabel || proj.status}</div>
          </div>
        </div>
        <span className={proj.status === 'active' ? 'badge-green' : 'badge-yellow'}>{proj.status === 'active' ? '● Active' : '● Running'}</span>
      </div>
      <div className="flex gap-3 mt-2 text-xs text-gray-500">
        {projTasks.length > 0 && <span className="text-blue-400">⚡ {projTasks.length} tasks</span>}
        {projTodos.length > 0 && <span className="text-yellow-400">✅ {projTodos.length} todos</span>}
        {projItems.length > 0 && <span className="text-red-400">🚨 {projItems.length} items</span>}
        {projTasks.length === 0 && projTodos.length === 0 && projItems.length === 0 && <span>All clear</span>}
      </div>
    </div>
  )
}
