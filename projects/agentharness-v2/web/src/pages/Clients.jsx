import { useState, useEffect } from 'react'
import { marked } from 'marked'
import { api } from '../hooks/useSocket'

const CLIENT_ICONS = { xftc: '🌐', pbs: '🏛️', lebc: '⛪' }
const STATUS_COLORS = {
  active:  { badge: 'bg-success/10 text-success border-success/20',  dot: 'bg-success' },
  pending: { badge: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20', dot: 'bg-yellow-400' },
  complete:{ badge: 'bg-blue-400/10 text-blue-400 border-blue-400/20', dot: 'bg-blue-400' },
}

export default function Clients() {
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [docContent, setDocContent] = useState('')
  const [activeDoc, setActiveDoc] = useState(null)

  useEffect(() => {
    api('/clients').then(data => { setClients(data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  async function selectClient(client) {
    setSelected(client)
    setActiveTab('overview')
    setDocContent('')
    setActiveDoc(null)
  }

  async function loadDoc(slug, doc) {
    setActiveDoc(doc)
    setActiveTab('docs')
    try {
      const data = await api(`/clients/${slug}/docs/${doc}`)
      setDocContent(data.content)
    } catch { setDocContent('Error loading document.') }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="w-6 h-6 border-2 border-brand/30 border-t-brand rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="flex h-full overflow-hidden">
      {/* Client sidebar */}
      <div className="w-64 flex-shrink-0 bg-surface border-r border-surface-border flex flex-col">
        <div className="px-4 py-4 border-b border-surface-border">
          <h2 className="font-bold text-white text-sm">S2T Designs</h2>
          <p className="text-xs text-gray-500 mt-0.5">Web Agency Clients</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {clients.length === 0 && <div className="text-xs text-gray-600 px-3 py-2">No clients found</div>}
          {clients.map(c => {
            const sc = STATUS_COLORS[c.status] || STATUS_COLORS.pending
            return (
              <button
                key={c.slug}
                onClick={() => selectClient(c)}
                className={`w-full text-left px-3 py-3 rounded-lg transition-all ${selected?.slug === c.slug ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg flex-shrink-0">{CLIENT_ICONS[c.slug] || '🏢'}</span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">{c.name}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${sc.dot}`} />
                      <span className="text-xs text-gray-500 capitalize">{c.status}</span>
                      {c.blockers?.length > 0 && <span className="text-xs text-red-400">· {c.blockers.length} blocker{c.blockers.length > 1 ? 's' : ''}</span>}
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
        <div className="p-3 border-t border-surface-border">
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('open-command', { detail: 'add new client ' }))}
            className="btn-primary w-full justify-center text-sm"
          >
            ＋ Add New Client
          </button>
        </div>
      </div>

      {/* Main content */}
      {!selected ? (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <div className="text-center space-y-3">
            <div className="text-5xl">🎨</div>
            <div className="text-lg font-semibold text-gray-300">S2T Designs Clients</div>
            <div className="text-sm">{clients.length} active client{clients.length !== 1 ? 's' : ''} — select one to view details</div>
            <div className="flex gap-3 justify-center mt-4 flex-wrap">
              {clients.map(c => (
                <button key={c.slug} onClick={() => selectClient(c)}
                  className="text-xs px-3 py-1.5 rounded-full border border-surface-border hover:border-brand/50 hover:text-brand-light text-gray-400 transition-colors">
                  {CLIENT_ICONS[c.slug] || '🏢'} {c.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <ClientDetail
          client={selected}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          docContent={docContent}
          activeDoc={activeDoc}
          onLoadDoc={loadDoc}
        />
      )}
    </div>
  )
}

function ClientDetail({ client, activeTab, setActiveTab, docContent, activeDoc, onLoadDoc }) {
  const sc = STATUS_COLORS[client.status] || STATUS_COLORS.pending
  const TABS = ['overview', 'phases', 'docs']
  if (client.blockers?.length > 0) TABS.push('blockers')

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-4 px-6 py-4 border-b border-surface-border bg-surface-light flex-shrink-0">
        <span className="text-3xl">{CLIENT_ICONS[client.slug] || '🏢'}</span>
        <div className="flex-1 min-w-0">
          <h1 className="text-lg font-bold text-white truncate">{client.name}</h1>
          <div className="flex items-center gap-3 mt-0.5 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${sc.badge}`}>
              <span className={`inline-block w-1.5 h-1.5 rounded-full ${sc.dot} mr-1`} />
              {client.status}
            </span>
            {client.platform && <span className="text-xs text-gray-500">📦 {client.platform}</span>}
            {client.url && (
              <a href={`https://${client.url.replace(/^https?:\/\//, '')}`} target="_blank" rel="noreferrer"
                className="text-xs text-brand-light hover:underline" onClick={e => e.stopPropagation()}>
                🌐 {client.url.replace(/^https?:\/\//, '')}
              </a>
            )}
          </div>
        </div>
        {client.blockers?.length > 0 && (
          <div className="text-xs px-2.5 py-1 rounded-full border border-red-500/30 bg-red-500/10 text-red-400 flex-shrink-0">
            🚨 {client.blockers.length} blocker{client.blockers.length > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3 border-b border-surface-border flex-shrink-0 bg-surface">
        {TABS.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm rounded-t-lg font-medium transition-colors capitalize ${activeTab === t ? 'bg-brand/15 text-brand-light border-b-2 border-brand' : 'text-gray-500 hover:text-gray-300'}`}>
            {t}
            {t === 'blockers' && <span className="ml-1.5 text-red-400">({client.blockers.length})</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              {/* Key info */}
              <div className="card space-y-3">
                <h3 className="text-sm font-semibold text-gray-300">Client Details</h3>
                {[
                  ['Slug', client.slug],
                  ['Platform', client.platform],
                  ['Contact', client.contact],
                  ['Engagement', client.engagement],
                  ['Lead Agent', client.lead],
                ].filter(([,v]) => v).map(([label, value]) => (
                  <div key={label} className="flex gap-3 text-sm">
                    <span className="text-gray-500 w-24 flex-shrink-0">{label}</span>
                    <span className="text-gray-200">{value}</span>
                  </div>
                ))}
                {client.url && (
                  <div className="flex gap-3 text-sm">
                    <span className="text-gray-500 w-24 flex-shrink-0">Site URL</span>
                    <a href={`https://${client.url.replace(/^https?:\/\//, '')}`} target="_blank" rel="noreferrer"
                      className="text-brand-light hover:underline">{client.url}</a>
                  </div>
                )}
              </div>

              {/* Blockers summary */}
              {client.blockers?.length > 0 && (
                <div className="card border-red-500/20">
                  <h3 className="text-sm font-semibold text-red-400 mb-2">🚨 Open Blockers</h3>
                  <div className="space-y-1.5">
                    {client.blockers.map((b, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-red-400 flex-shrink-0 mt-0.5">☐</span>
                        <span className="text-gray-300">{b}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right col — docs + phases summary */}
            <div className="space-y-4">
              {/* Progress */}
              {client.phases?.length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">Project Progress</h3>
                  <div className="space-y-2">
                    {client.phases.slice(0, 6).map((p, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="w-4 flex-shrink-0 text-center">
                          {p.status.includes('✅') ? '✅' : p.status.includes('🟡') ? '🟡' : '⬜'}
                        </span>
                        <span className={`flex-1 ${p.status.includes('✅') ? 'text-gray-500 line-through' : 'text-gray-200'}`}>{p.phase}</span>
                      </div>
                    ))}
                    {client.phases.length > 6 && <div className="text-xs text-gray-500 pl-7">+{client.phases.length - 6} more phases</div>}
                  </div>
                </div>
              )}

              {/* Docs */}
              {client.docs?.length > 0 && (
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-300 mb-3">Project Docs</h3>
                  <div className="space-y-1">
                    {client.docs.map((d, i) => (
                      <button key={i} onClick={() => onLoadDoc(client.slug, d)}
                        className="flex items-center gap-2 w-full text-left py-1.5 text-sm text-gray-400 hover:text-white transition-colors border-b border-surface-border last:border-0">
                        <span>📄</span><span className="truncate">{d.replace(/-/g, ' ')}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'phases' && (
          <div className="space-y-2 max-w-xl">
            {client.phases?.length === 0 && <div className="text-gray-500 text-sm">No phase data found in PROJECT.md</div>}
            {client.phases?.map((p, i) => (
              <div key={i} className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${
                p.status.includes('✅') ? 'bg-success/5 border-success/15' :
                p.status.includes('🟡') ? 'bg-yellow-400/5 border-yellow-400/15' :
                'bg-surface-lighter border-surface-border'
              }`}>
                <span className="text-lg flex-shrink-0 mt-0.5">
                  {p.status.includes('✅') ? '✅' : p.status.includes('🟡') ? '🟡' : '⬜'}
                </span>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${p.status.includes('✅') ? 'text-gray-500 line-through' : 'text-white'}`}>{p.phase}</div>
                  {p.notes && p.notes !== '|' && <div className="text-xs text-gray-500 mt-0.5">{p.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'blockers' && (
          <div className="space-y-3 max-w-xl">
            {client.blockers?.length === 0 && <div className="text-gray-500 text-sm">No open blockers 🎉</div>}
            {client.blockers?.map((b, i) => (
              <div key={i} className="flex items-start gap-3 px-4 py-3 rounded-lg border border-red-500/20 bg-red-500/5">
                <span className="text-red-400 flex-shrink-0 mt-0.5">☐</span>
                <span className="text-sm text-gray-200">{b}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="flex gap-4 h-full">
            <div className="w-52 flex-shrink-0 space-y-1">
              {client.docs?.map((d, i) => (
                <button key={i} onClick={() => onLoadDoc(client.slug, d)}
                  className={`w-full text-left text-sm px-3 py-2 rounded-lg transition-colors ${activeDoc === d ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}>
                  📄 {d.replace(/-/g, ' ')}
                </button>
              ))}
            </div>
            <div className="flex-1 card overflow-y-auto">
              {docContent
                ? <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: marked(docContent) }} />
                : <div className="text-gray-500 text-sm">Select a document to view</div>
              }
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
