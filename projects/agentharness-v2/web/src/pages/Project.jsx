import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { marked } from 'marked'
import { api } from '../hooks/useSocket'

const ICONS = { xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️', ministry:'⛪', finance:'💰', personal:'🗓️', global:'✨' }

export default function ProjectPage({ roster }) {
  const { slug } = useParams()
  const [activeTab, setActiveTab] = useState('overview')
  const [docs, setDocs] = useState([])
  const [activeDoc, setActiveDoc] = useState(null)
  const [docContent, setDocContent] = useState('')
  const [tasks, setTasks] = useState([])
  const [todos, setTodos] = useState([])
  const [summary, setSummary] = useState(null)
  const [agentModal, setAgentModal] = useState(null)

  const project = roster?.projects?.find(p => p.slug === slug)

  useEffect(() => {
    if (!slug) return
    api(`/projects/${slug}/docs`).then(setDocs).catch(console.error)
    api(`/tasks?project_slug=${slug}`).then(setTasks).catch(console.error)
    api(`/todos?project_slug=${slug}`).then(setTodos).catch(console.error)
    api(`/projects/${slug}/summary`).then(setSummary).catch(console.error)
  }, [slug])

  async function loadDoc(name) {
    setActiveDoc(name)
    const data = await api(`/projects/${slug}/docs/${name}`)
    setDocContent(data.content)
    setActiveTab('docs')
  }

  async function openAgent(agentId) {
    try {
      const data = await api(`/settings/agents/${agentId}/profile`)
      setAgentModal(data)
    } catch (e) { setAgentModal({ id: agentId, content: null }) }
  }

  if (!project) return (
    <div className="flex items-center justify-center h-full text-gray-500">
      <div className="text-center">
        <div className="text-4xl mb-3">📂</div>
        <div>Project "{slug}" not found in roster</div>
      </div>
    </div>
  )

  const specialists = project.specialists || []
  const helpers = project.helpers || []
  const TABS = ['overview', 'agents', 'tasks', 'docs', 'todos']

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Project header */}
      <div className="flex items-center gap-4 px-6 py-4 border-b border-surface-border bg-surface-light flex-shrink-0">
        <span className="text-3xl">{ICONS[slug] || '📁'}</span>
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-bold text-white truncate">{project.name}</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={project.status === 'active' ? 'badge-green' : 'badge-yellow'}>{project.statusLabel || project.status}</span>
            <span className="text-xs text-gray-500">Lead: {project.leadAgent}</span>
          </div>
        </div>
        <div className="flex gap-3 text-xs text-gray-500 flex-shrink-0">
          <span className="text-blue-400">⚡ {tasks.filter(t => ['running','queued'].includes(t.status)).length} active</span>
          <span className="text-yellow-400">✅ {todos.filter(t => t.status !== 'done').length} todos</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3 border-b border-surface-border flex-shrink-0 bg-surface">
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm rounded-t-lg font-medium transition-colors capitalize ${activeTab === t ? 'bg-brand/15 text-brand-light border-b-2 border-brand' : 'text-gray-500 hover:text-gray-300'}`}>
            {t}
            {t === 'tasks' && tasks.filter(x => x.status === 'running').length > 0 && <span className="ml-1.5 badge-blue text-xs">{tasks.filter(x => x.status === 'running').length}</span>}
            {t === 'todos' && todos.filter(x => x.status !== 'done').length > 0 && <span className="ml-1.5 badge-yellow text-xs">{todos.filter(x => x.status !== 'done').length}</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left col */}
            <div className="space-y-4">
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Lead Agent</h3>
                <button onClick={() => openAgent(project.leadAgent)} className="flex items-center gap-3 w-full text-left hover:bg-surface-lighter rounded-lg p-2 transition-colors">
                  <div className="w-9 h-9 rounded-xl bg-brand/20 flex items-center justify-center text-brand font-bold text-sm">{project.leadAgent?.slice(0,2).toUpperCase()}</div>
                  <div>
                    <div className="text-sm font-medium text-white">{project.leadAgent}</div>
                    <div className="text-xs text-gray-500 truncate">{project.leadRole || 'Project Lead'}</div>
                  </div>
                </button>
              </div>
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Specialist Agents ({specialists.length})</h3>
                <div className="space-y-2">
                  {specialists.map((s, i) => (
                    <button key={i} onClick={() => openAgent(s.name)} className="flex items-start gap-3 w-full text-left hover:bg-surface-lighter rounded-lg p-2 transition-colors">
                      <div className="w-7 h-7 rounded-lg bg-surface-lighter flex items-center justify-center text-xs text-gray-400 flex-shrink-0">{s.name?.slice(0,1).toUpperCase()}</div>
                      <div className="min-w-0">
                        <div className="text-sm text-white leading-tight">{s.name}</div>
                        <div className="text-xs text-gray-500 truncate">{s.role || s.responsibilities}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              {helpers.length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-300 mb-2">Helper Agents ({helpers.length})</h3>
                  <div className="flex flex-wrap gap-2">
                    {helpers.map((h, i) => (
                      <button key={i} onClick={() => openAgent(h.name)} className="text-xs px-2.5 py-1 rounded-full border border-surface-border text-gray-400 hover:text-white hover:border-brand/50 transition-colors">{h.name}</button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right col */}
            <div className="space-y-4">
              {/* Open todos */}
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-300">Open Todos</h3>
                  <button onClick={() => setActiveTab('todos')} className="text-xs text-brand-light hover:underline">View all</button>
                </div>
                {todos.filter(t => t.status !== 'done').slice(0, 5).map(t => (
                  <div key={t.id} className="flex items-start gap-2 py-1.5 border-b border-surface-border last:border-0">
                    <span className={`priority-${t.priority} flex-shrink-0 mt-0.5`}>{t.priority}</span>
                    <span className="text-sm text-gray-200">{t.title}</span>
                  </div>
                ))}
                {todos.filter(t => t.status !== 'done').length === 0 && <div className="text-sm text-gray-500">No open todos 🎉</div>}
              </div>

              {/* Recent tasks */}
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-300">Recent Tasks</h3>
                  <button onClick={() => setActiveTab('tasks')} className="text-xs text-brand-light hover:underline">View all</button>
                </div>
                {tasks.slice(0, 5).map(t => (
                  <div key={t.id} className="flex items-center gap-2 py-1.5 border-b border-surface-border last:border-0">
                    <span className={`status-${t.status} flex-shrink-0`}>{t.status}</span>
                    <span className="text-sm text-gray-200 truncate flex-1">{t.title}</span>
                  </div>
                ))}
                {tasks.length === 0 && <div className="text-sm text-gray-500">No tasks yet</div>}
              </div>

              {/* Project docs */}
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-300">Project Docs</h3>
                  <button onClick={() => setActiveTab('docs')} className="text-xs text-brand-light hover:underline">View all</button>
                </div>
                {docs.slice(0, 5).map((d, i) => (
                  <button key={i} onClick={() => loadDoc(d.name)} className="flex items-center gap-2 py-1.5 text-sm text-gray-400 hover:text-white w-full text-left border-b border-surface-border last:border-0 transition-colors">
                    <span>📄</span> <span className="truncate">{d.name}</span>
                  </button>
                ))}
                {docs.length === 0 && <div className="text-sm text-gray-500">No docs found</div>}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="flex gap-4 h-full">
            <div className="w-56 flex-shrink-0 space-y-1">
              {docs.map((d, i) => (
                <button key={i} onClick={() => loadDoc(d.name)}
                  className={`w-full text-left text-sm px-3 py-2 rounded-lg transition-colors ${activeDoc === d.name ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}>
                  📄 {d.name.replace('.md', '')}
                </button>
              ))}
              {docs.length === 0 && <div className="text-sm text-gray-500 px-3">No docs found for this project</div>}
            </div>
            <div className="flex-1 card overflow-y-auto">
              {docContent ? (
                <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: marked(docContent) }} />
              ) : (
                <div className="text-gray-500 text-sm">Select a document to view</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="space-y-3">
            {tasks.length === 0 && <div className="text-gray-500 text-sm">No tasks for this project yet</div>}
            {tasks.map(t => (
              <div key={t.id} className="card">
                <div className="flex items-start gap-3">
                  <span className={`status-${t.status} flex-shrink-0 mt-0.5`}>{t.status}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white text-sm">{t.title}</div>
                    <div className="text-xs text-gray-500 mt-0.5">Agent: {t.agent_id} · {new Date(t.created_at).toLocaleString()}</div>
                    {t.result && (
                      <details className="mt-2">
                        <summary className="text-xs text-brand-light cursor-pointer">View result</summary>
                        <div className="mt-2 prose-dark text-xs" dangerouslySetInnerHTML={{ __html: marked(t.result) }} />
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'todos' && (
          <div className="space-y-2">
            {todos.filter(t => t.status !== 'done').length === 0 && <div className="text-gray-500 text-sm">No open todos for this project 🎉</div>}
            {todos.filter(t => t.status !== 'done').map(todo => (
              <div key={todo.id} className="card-sm flex items-start gap-3">
                <span className={`priority-${todo.priority} flex-shrink-0 mt-0.5`}>{todo.priority}</span>
                <div className="flex-1">
                  <div className="text-sm text-white">{todo.title}</div>
                  {todo.description && <div className="text-xs text-gray-500 mt-0.5">{todo.description}</div>}
                  {todo.due_date && <div className="text-xs text-gray-600 mt-0.5">Due: {todo.due_date}</div>}
                </div>
                <span className="text-xs text-gray-600">{todo.source}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Lead</h3>
              <button onClick={() => openAgent(project.leadAgent)} className="card w-full text-left hover:border-brand/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-brand/20 flex items-center justify-center text-brand font-bold">{project.leadAgent?.slice(0,2).toUpperCase()}</div>
                  <div>
                    <div className="font-medium text-white">{project.leadAgent}</div>
                    <div className="text-xs text-gray-500">{project.leadRole || 'Project Lead'}</div>
                  </div>
                  <span className="ml-auto badge-green">● Active</span>
                </div>
              </button>
            </div>
            {specialists.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Specialists</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {specialists.map((s, i) => (
                    <button key={i} onClick={() => openAgent(s.name)} className="card-sm text-left hover:border-brand/30 transition-colors">
                      <div className="font-medium text-white text-sm">{s.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{s.role}</div>
                      {s.responsibilities && <div className="text-xs text-gray-600 mt-1 truncate">{s.responsibilities}</div>}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {helpers.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Helpers</h3>
                <div className="flex flex-wrap gap-2">
                  {helpers.map((h, i) => (
                    <button key={i} onClick={() => openAgent(h.name)} className="text-sm px-3 py-1.5 rounded-lg border border-surface-border text-gray-400 hover:text-white hover:border-brand/50 transition-colors">{h.name}</button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Agent profile modal */}
      {agentModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setAgentModal(null)}>
          <div className="bg-surface-light border border-surface-border rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
              <div>
                <h2 className="font-bold text-white">{agentModal.id}</h2>
                <div className="text-xs text-gray-500 mt-0.5">Agent Profile</div>
              </div>
              <button onClick={() => setAgentModal(null)} className="btn-ghost text-xs">✕</button>
            </div>
            <div className="flex-1 overflow-y-auto p-5">
              {agentModal.content
                ? <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: marked(agentModal.content) }} />
                : <div className="text-gray-500 text-sm">No profile file found for this agent yet.</div>
              }
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
