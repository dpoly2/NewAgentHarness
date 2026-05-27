import { useState } from 'react'
import { marked } from 'marked'
import { api } from '../hooks/useSocket'

const PROJECT_ICONS = {
  xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕',
  smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️',
  ministry:'⛪', finance:'💰', personal:'🗓️', 'sigma-signal':'📰', travel:'✈️', global:'✨'
}

const STATUS_COLORS = {
  active: 'bg-success/10 text-success border-success/20',
  running: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  pending: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
}

export default function Agents({ roster }) {
  const [search, setSearch] = useState('')
  const [filterProject, setFilterProject] = useState('all')
  const [agentModal, setAgentModal] = useState(null)
  const [loadingAgent, setLoadingAgent] = useState(null)

  const projects = roster?.projects || []
  const sharedAgents = roster?.sharedAgents || []

  async function openAgent(agentId) {
    setLoadingAgent(agentId)
    try {
      const data = await api(`/settings/agents/${agentId}/profile`)
      setAgentModal(data)
    } catch {
      setAgentModal({ id: agentId, content: null })
    } finally {
      setLoadingAgent(null)
    }
  }

  // Build flat agent list for search
  const allAgents = []
  for (const proj of projects) {
    allAgents.push({ id: proj.leadAgent, role: proj.leadRole || 'Project Lead', type: 'lead', project: proj.slug, projectName: proj.name })
    for (const s of (proj.specialists || [])) allAgents.push({ id: s.name, role: s.role || s.responsibilities, type: 'specialist', project: proj.slug, projectName: proj.name })
    for (const h of (proj.helpers || [])) allAgents.push({ id: h.name, role: h.role || 'Helper', type: 'helper', project: proj.slug, projectName: proj.name })
  }
  for (const s of sharedAgents) allAgents.push({ id: s.agentName, role: s.specialty, type: 'shared', project: 'shared', projectName: 'Shared' })

  const filtered = allAgents.filter(a => {
    const matchSearch = !search || a.id?.toLowerCase().includes(search.toLowerCase()) || a.role?.toLowerCase().includes(search.toLowerCase())
    const matchProject = filterProject === 'all' || a.project === filterProject
    return matchSearch && matchProject
  })

  // Total counts
  const totalLeads = allAgents.filter(a => a.type === 'lead').length
  const totalSpecialists = allAgents.filter(a => a.type === 'specialist').length
  const totalHelpers = allAgents.filter(a => a.type === 'helper').length

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-surface-border bg-surface-light flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white">Agent Directory</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {allAgents.length} agents · {totalLeads} leads · {totalSpecialists} specialists · {totalHelpers} helpers
            </p>
          </div>
          <div className="flex items-center gap-2">
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search agents…"
              className="input text-sm py-1.5 w-48"
            />
            <select value={filterProject} onChange={e => setFilterProject(e.target.value)} className="input text-sm py-1.5">
              <option value="all">All Projects</option>
              {projects.map(p => <option key={p.slug} value={p.slug}>{p.name}</option>)}
              <option value="shared">Shared</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* If searching, show flat results */}
        {(search || filterProject !== 'all') ? (
          <div>
            <div className="text-xs text-gray-500 mb-3">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filtered.map((a, i) => (
                <AgentCard key={i} agent={a} loading={loadingAgent === a.id} onOpen={openAgent} />
              ))}
            </div>
            {filtered.length === 0 && <div className="text-gray-500 text-sm">No agents match your search.</div>}
          </div>
        ) : (
          /* Default: show grouped by project */
          <>
            {projects.map(proj => {
              const specs = proj.specialists || []
              const helpers = proj.helpers || []
              return (
                <div key={proj.slug}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{PROJECT_ICONS[proj.slug] || '📁'}</span>
                    <div>
                      <h2 className="font-semibold text-white text-sm">{proj.name}</h2>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[proj.status] || STATUS_COLORS.pending}`}>{proj.statusLabel || proj.status}</span>
                        <span className="text-xs text-gray-500">{1 + specs.length + helpers.length} agents</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 pl-0">
                    {/* Lead */}
                    <AgentCard agent={{ id: proj.leadAgent, role: proj.leadRole || 'Project Lead', type: 'lead', project: proj.slug, projectName: proj.name }} loading={loadingAgent === proj.leadAgent} onOpen={openAgent} />
                    {/* Specialists */}
                    {specs.map((s, i) => (
                      <AgentCard key={i} agent={{ id: s.name, role: s.role || s.responsibilities, type: 'specialist', project: proj.slug, projectName: proj.name }} loading={loadingAgent === s.name} onOpen={openAgent} />
                    ))}
                    {/* Helpers */}
                    {helpers.map((h, i) => (
                      <AgentCard key={i} agent={{ id: h.name, role: h.role || 'Helper', type: 'helper', project: proj.slug, projectName: proj.name }} loading={loadingAgent === h.name} onOpen={openAgent} />
                    ))}
                  </div>

                  <div className="border-b border-surface-border mt-6" />
                </div>
              )
            })}

            {/* Shared agents */}
            {sharedAgents.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-2xl">🔗</span>
                  <div>
                    <h2 className="font-semibold text-white text-sm">Shared Agents</h2>
                    <p className="text-xs text-gray-500 mt-0.5">Available across all projects</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {sharedAgents.map((s, i) => (
                    <AgentCard key={i} agent={{ id: s.agentName, role: s.specialty, type: 'shared', project: 'shared', projectName: 'Shared' }} loading={loadingAgent === s.agentName} onOpen={openAgent} />
                  ))}
                </div>
              </div>
            )}
          </>
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

function AgentCard({ agent, loading, onOpen }) {
  const typeBadge = {
    lead: 'bg-brand/15 text-brand-light border-brand/20',
    specialist: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
    helper: 'bg-surface-lighter text-gray-400 border-surface-border',
    shared: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  }
  const initials = agent.id?.split('-').map(w => w[0]).join('').slice(0, 3).toUpperCase() || '?'

  return (
    <button
      onClick={() => onOpen(agent.id)}
      disabled={loading}
      className="card-sm text-left hover:border-brand/30 hover:bg-surface-lighter transition-all group disabled:opacity-50"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-brand/10 flex items-center justify-center text-xs font-bold text-brand-light flex-shrink-0 group-hover:bg-brand/20 transition-colors">
          {loading ? <span className="animate-spin text-base">⏳</span> : initials}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-white leading-tight truncate">{agent.id}</div>
          <div className="text-xs text-gray-500 mt-0.5 truncate">{agent.role}</div>
          <div className="mt-1.5">
            <span className={`text-xs px-1.5 py-0.5 rounded border ${typeBadge[agent.type]}`}>{agent.type}</span>
          </div>
        </div>
      </div>
    </button>
  )
}
