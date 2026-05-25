import { useState, useEffect } from 'react'
import { api } from '../hooks/useSocket'

const PROVIDERS = [
  { id: 'ollama', label: 'Ollama (Local)', baseUrl: 'http://localhost:11434/v1', model: 'llama3.2', note: 'Free, runs on your machine. Install Ollama + pull a model.' },
  { id: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini', note: 'Best performance. Requires API key from platform.openai.com' },
  { id: 'anthropic', label: 'Anthropic Claude', baseUrl: 'https://api.anthropic.com/v1', model: 'claude-3-haiku-20240307', note: 'Excellent reasoning. Requires API key from console.anthropic.com' },
  { id: 'github', label: 'GitHub Models', baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini', note: 'Free with GitHub account. Uses GitHub personal access token.' }
]

export default function Settings() {
  const [aiConfig, setAiConfig] = useState({ provider: 'ollama', baseUrl: '', apiKey: '', model: '', enabled: false })
  const [profile, setProfile] = useState({ name: '', role: '', priorities: '', communicationStyle: '' })
  const [saved, setSaved] = useState('')
  const [generating, setGenerating] = useState(false)
  const [briefs, setBriefs] = useState([])
  const [selectedBrief, setSelectedBrief] = useState(null)

  useEffect(() => {
    api('/settings/ai').then(setAiConfig).catch(console.error)
    api('/settings/profile').then(setProfile).catch(console.error)
    api('/settings/briefings').then(setBriefs).catch(console.error)
  }, [])

  function applyPreset(providerId) {
    const preset = PROVIDERS.find(p => p.id === providerId)
    if (preset) setAiConfig(c => ({ ...c, provider: providerId, baseUrl: preset.baseUrl, model: preset.model }))
  }

  async function saveAI() {
    await api('/settings/ai', { method: 'POST', body: aiConfig })
    flash('AI settings saved')
  }

  async function saveProfile() {
    await api('/settings/profile', { method: 'POST', body: profile })
    flash('Profile saved')
  }

  async function generateBrief() {
    setGenerating(true)
    try {
      const b = await api('/settings/briefings/generate', { method: 'POST', body: {} })
      setBriefs(prev => [b, ...prev])
      setSelectedBrief(b)
      flash('Morning briefing generated')
    } catch (e) { flash(`Error: ${e.message}`) }
    finally { setGenerating(false) }
  }

  function flash(msg) { setSaved(msg); setTimeout(() => setSaved(''), 3000) }

  const activeProvider = PROVIDERS.find(p => p.id === aiConfig.provider)

  return (
    <div className="p-6 h-full overflow-y-auto max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {saved && (
        <div className="mb-4 px-4 py-2.5 bg-success/10 border border-success/30 text-success text-sm rounded-lg flex items-center gap-2">
          ✓ {saved}
        </div>
      )}

      {/* AI Provider */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">🤖 AI Provider</h2>

        <div className="grid grid-cols-2 gap-2 mb-4">
          {PROVIDERS.map(p => (
            <button key={p.id} onClick={() => applyPreset(p.id)}
              className={`text-left p-3 rounded-xl border transition-all ${aiConfig.provider === p.id ? 'border-brand/50 bg-brand/10' : 'border-surface-border hover:border-surface-lighter'}`}>
              <div className="text-sm font-medium text-white">{p.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{p.note}</div>
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Base URL</label>
            <input value={aiConfig.baseUrl} onChange={e => setAiConfig(c => ({ ...c, baseUrl: e.target.value }))} className="input w-full" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Model</label>
            <input value={aiConfig.model} onChange={e => setAiConfig(c => ({ ...c, model: e.target.value }))} className="input w-full" placeholder="e.g. llama3.2, gpt-4o-mini" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">API Key {aiConfig.provider === 'ollama' ? '(not required for Ollama)' : '(required)'}</label>
            <input type="password" value={aiConfig.apiKey === '***' ? '' : aiConfig.apiKey} onChange={e => setAiConfig(c => ({ ...c, apiKey: e.target.value }))} className="input w-full" placeholder={aiConfig.provider === 'ollama' ? 'Leave empty for local Ollama' : 'Enter API key...'} />
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setAiConfig(c => ({ ...c, enabled: !c.enabled }))}
              className={`relative w-12 h-6 rounded-full transition-colors ${aiConfig.enabled ? 'bg-brand' : 'bg-surface-border'}`}>
              <span className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-transform ${aiConfig.enabled ? 'translate-x-7' : 'translate-x-1'}`} />
            </button>
            <span className="text-sm text-gray-300">{aiConfig.enabled ? 'AI enabled' : 'AI disabled'}</span>
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <button onClick={saveAI} className="btn-primary text-sm">Save AI Settings</button>
        </div>
      </section>

      {/* Profile */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">👤 Operator Profile</h2>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Your Name</label>
              <input value={profile.name || ''} onChange={e => setProfile(p => ({ ...p, name: e.target.value }))} className="input w-full" placeholder="David" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Your Role</label>
              <input value={profile.role || ''} onChange={e => setProfile(p => ({ ...p, role: e.target.value }))} className="input w-full" placeholder="Founder & Director" />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Current Priorities (AgentMajesty uses this)</label>
            <textarea value={profile.priorities || ''} onChange={e => setProfile(p => ({ ...p, priorities: e.target.value }))} className="input w-full resize-none" rows={2} placeholder="XFTC Sprint 3, YEPC OZ nomination, Elevation LLC formation..." />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Communication Style</label>
            <input value={profile.communicationStyle || ''} onChange={e => setProfile(p => ({ ...p, communicationStyle: e.target.value }))} className="input w-full" placeholder="Concise and direct" />
          </div>
        </div>
        <button onClick={saveProfile} className="btn-primary text-sm mt-4">Save Profile</button>
      </section>

      {/* Morning Briefings */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">📋 Morning Briefings</h2>
        <p className="text-sm text-gray-500 mb-4">Auto-generated daily at 7:00 AM CT. Shows portfolio status, urgent items, and agent activity.</p>
        <button onClick={generateBrief} disabled={generating} className="btn-primary text-sm mb-4 disabled:opacity-50">
          {generating ? 'Generating...' : '📋 Generate Now'}
        </button>
        <div className="space-y-2">
          {briefs.slice(0, 5).map(b => (
            <button key={b.id} onClick={() => setSelectedBrief(selectedBrief?.id === b.id ? null : b)}
              className="w-full text-left px-3 py-2 rounded-lg border border-surface-border hover:border-brand/30 transition-colors">
              <div className="text-sm text-gray-300">{new Date(b.generated_at).toLocaleString()}</div>
              <div className="text-xs text-gray-500 truncate mt-0.5">{b.content?.slice(0, 80)}...</div>
            </button>
          ))}
        </div>
        {selectedBrief && (
          <div className="mt-4 p-4 bg-surface rounded-xl border border-surface-border">
            <div className="text-xs text-gray-500 mb-2">{new Date(selectedBrief.generated_at).toLocaleString()}</div>
            <div className="text-sm text-gray-200 whitespace-pre-wrap">{selectedBrief.content}</div>
          </div>
        )}
      </section>

      {/* Remote Access info */}
      <section className="card">
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">🌐 Remote Access</h2>
        <p className="text-sm text-gray-400 mb-4">Use Cloudflare Tunnel to access AgentHarness from any browser or phone without port forwarding.</p>
        <div className="bg-surface rounded-xl p-4 font-mono text-sm text-gray-300 space-y-2">
          <div className="text-xs text-gray-500 mb-2"># Install cloudflared (one-time)</div>
          <div>npm install -g cloudflared</div>
          <div className="text-xs text-gray-500 mt-2"># Login and create tunnel</div>
          <div>cloudflared tunnel login</div>
          <div>cloudflared tunnel create agentharness</div>
          <div className="text-xs text-gray-500 mt-2"># Route your domain</div>
          <div>cloudflared tunnel route dns agentharness yourname.com</div>
          <div className="text-xs text-gray-500 mt-2"># Start the tunnel (auto-HTTPS)</div>
          <div>cloudflared tunnel run --url http://localhost:4000 agentharness</div>
        </div>
        <p className="text-xs text-gray-500 mt-3">The web app can be deployed separately to Cloudflare Pages with <code className="bg-surface-lighter px-1 rounded">VITE_API_URL</code> set to your tunnel URL.</p>
      </section>
    </div>
  )
}
