import { useState, useEffect } from 'react'
import { api, getStoredToken, setStoredToken } from '../hooks/useSocket'

const PROVIDERS = [
  { id: 'ollama', label: 'Ollama (Local)', baseUrl: 'http://localhost:11434/v1', model: 'llama3.2', note: 'Free, runs on your machine. Install Ollama + pull a model.' },
  { id: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini', note: 'Best performance. Requires API key from platform.openai.com' },
  { id: 'anthropic', label: 'Anthropic Claude', baseUrl: 'https://api.anthropic.com/v1', model: 'claude-3-haiku-20240307', note: 'Excellent reasoning. Requires API key from console.anthropic.com' },
  { id: 'github', label: 'GitHub Models', baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini', note: 'Free with GitHub account. Uses GitHub personal access token.' }
]

const PUSH_PROVIDERS = [
  { id: 'ntfy', label: '📡 ntfy.sh', note: 'Free & open-source. Best for Apple Watch.' },
  { id: 'pushover', label: '🔔 Pushover', note: '$5 one-time iOS app. Best Watch complication.' },
  { id: 'pushcut', label: '🍎 Pushcut', note: 'Apple Shortcuts webhook. Native Watch support.' }
]

const PRIORITY_LABELS = [
  { id: 'urgent', label: 'Urgent only' },
  { id: 'high', label: 'High + Urgent' },
  { id: 'medium', label: 'Medium and above' },
  { id: 'low', label: 'All notifications' }
]

export default function Settings() {
  const [aiConfig, setAiConfig] = useState({ provider: 'ollama', baseUrl: '', apiKey: '', model: '', enabled: false })
  const [profile, setProfile] = useState({ name: '', role: '', priorities: '', communicationStyle: '' })
  const [pushConfig, setPushConfig] = useState({ enabled: false, provider: 'ntfy', minPriority: 'high', ntfyTopic: '', ntfyServer: 'https://ntfy.sh', pushoverToken: '', pushoverUser: '', pushcutWebhook: '' })
  const [security, setSecurity] = useState({ authEnabled: false, mode: 'open' })
  const [clientToken, setClientToken] = useState(getStoredToken())
  const [ddnsConfig, setDdnsConfig] = useState({ enabled: false, method: 'dynamic-url', dynamicUrl: '', authId: '', authPassword: '', domain: '', host: '@', ttl: 300, updateIntervalMin: 5 })
  const [ddnsStatus, setDdnsStatus] = useState(null)
  const [ddnsUpdating, setDdnsUpdating] = useState(false)
  const [publicIp, setPublicIp] = useState('')
  const [saved, setSaved] = useState('')
  const [generating, setGenerating] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testingAI, setTestingAI] = useState(false)
  const [aiTestResult, setAiTestResult] = useState(null)
  const [briefs, setBriefs] = useState([])
  const [selectedBrief, setSelectedBrief] = useState(null)
  const [pwForm, setPwForm] = useState({ currentPassword: '', newPassword: '', confirm: '' })
  const [pwMsg, setPwMsg] = useState(null) // {ok, text}

  useEffect(() => {
    api('/settings/ai').then(setAiConfig).catch(console.error)
    api('/settings/profile').then(setProfile).catch(console.error)
    api('/settings/briefings').then(setBriefs).catch(console.error)
    api('/settings/push').then(setPushConfig).catch(console.error)
    api('/settings/security').then(setSecurity).catch(console.error)
    api('/settings/ddns').then(setDdnsConfig).catch(console.error)
    api('/settings/ddns/ip').then(d => setPublicIp(d.ip)).catch(() => {})
  }, [])

  function applyPreset(providerId) {
    const preset = PROVIDERS.find(p => p.id === providerId)
    if (preset) setAiConfig(c => ({ ...c, provider: providerId, baseUrl: preset.baseUrl, model: preset.model }))
    setAiTestResult(null)
  }

  async function saveAI() {
    await api('/settings/ai', { method: 'POST', body: aiConfig })
    flash('AI settings saved')
    setAiTestResult(null)
  }

  async function testAI() {
    setTestingAI(true)
    setAiTestResult(null)
    try {
      // Save first so test uses latest config
      await api('/settings/ai', { method: 'POST', body: aiConfig })
      const result = await api('/settings/ai/test', { method: 'POST', body: {} })
      setAiTestResult(result)
    } catch (e) {
      setAiTestResult({ ok: false, error: e.message })
    } finally {
      setTestingAI(false)
    }
  }

  async function saveProfile() {
    await api('/settings/profile', { method: 'POST', body: profile })
    flash('Profile saved')
  }

  async function savePush() {
    await api('/settings/push', { method: 'POST', body: pushConfig })
    flash('Push notification settings saved')
  }

  async function testPush() {
    setTesting(true)
    try {
      await api('/settings/push/test', { method: 'POST', body: {} })
      flash('Test notification sent — check your iPhone & Apple Watch!')
    } catch (e) { flash(`Error: ${e.message}`) }
    finally { setTesting(false) }
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

  async function generateToken() {
    try {
      const result = await api('/settings/security/token', { method: 'POST', body: {} })
      setSecurity({ authEnabled: true, mode: 'protected' })
      flash(`Access token generated — copy it now and add to .env: ACCESS_TOKEN=${result.token}`)
    } catch (e) { flash(`Error: ${e.message}`) }
  }

  async function disableAuth() {
    try {
      await api('/settings/security/token', { method: 'DELETE' })
      setSecurity({ authEnabled: false, mode: 'open' })
      flash('Authentication disabled — server is now in open LAN mode')
    } catch (e) { flash(`Error: ${e.message}`) }
  }

  async function saveDdns() {
    try {
      const saved = await api('/settings/ddns', { method: 'POST', body: ddnsConfig })
      setDdnsConfig(saved)
      flash('ClouDNS DDNS settings saved')
    } catch (e) { flash(`Error: ${e.message}`) }
  }

  async function testDdns() {
    setDdnsUpdating(true)
    setDdnsStatus(null)
    try {
      const result = await api('/settings/ddns/update', { method: 'POST', body: {} })
      setDdnsStatus(result)
      if (result.ip) setPublicIp(result.ip)
    } catch (e) {
      setDdnsStatus({ ok: false, error: e.message })
    } finally { setDdnsUpdating(false) }
  }

  function flash(msg) { setSaved(msg); setTimeout(() => setSaved(''), 3500) }

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
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          🤖 AI Provider
          {aiConfig.enabled && (
            <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${
              aiTestResult?.ok === true ? 'bg-success/20 text-success' :
              aiTestResult?.ok === false ? 'bg-error/20 text-error' :
              'bg-brand/10 text-brand-light'
            }`}>
              {aiTestResult?.ok === true ? '✓ Connected' :
               aiTestResult?.ok === false ? '✗ Unreachable' :
               `Enabled — ${aiConfig.provider}`}
            </span>
          )}
        </h2>

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

        {aiTestResult && (
          <div className={`mt-3 p-3 rounded-xl text-sm ${aiTestResult.ok ? 'bg-success/10 border border-success/30 text-success' : 'bg-error/10 border border-error/30 text-error'}`}>
            {aiTestResult.ok
              ? `✓ Connected to ${aiTestResult.provider} — model: ${aiTestResult.model}`
              : `✗ ${aiTestResult.error}`}
          </div>
        )}

        <div className="flex gap-2 mt-4">
          <button onClick={saveAI} className="btn-primary text-sm">Save AI Settings</button>
          <button onClick={testAI} disabled={testingAI || !aiConfig.enabled} className="btn-secondary text-sm disabled:opacity-40">
            {testingAI ? 'Testing...' : '🔌 Test Connection'}
          </button>
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

      {/* Push Notifications — Apple Watch */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold text-white mb-1 flex items-center gap-2">⌚ Apple Watch Notifications</h2>
        <p className="text-xs text-gray-500 mb-4">Get agent task completions, urgent todos, and briefings on your iPhone and Apple Watch.</p>

        {/* Enable toggle */}
        <div className="flex items-center gap-3 mb-5">
          <button onClick={() => setPushConfig(c => ({ ...c, enabled: !c.enabled }))}
            className={`relative w-12 h-6 rounded-full transition-colors ${pushConfig.enabled ? 'bg-brand' : 'bg-surface-border'}`}>
            <span className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-transform ${pushConfig.enabled ? 'translate-x-7' : 'translate-x-1'}`} />
          </button>
          <span className="text-sm text-gray-300">{pushConfig.enabled ? 'Push notifications enabled' : 'Push notifications disabled'}</span>
        </div>

        {/* Provider picker */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {PUSH_PROVIDERS.map(p => (
            <button key={p.id} onClick={() => setPushConfig(c => ({ ...c, provider: p.id }))}
              className={`text-left p-3 rounded-xl border transition-all ${pushConfig.provider === p.id ? 'border-brand/50 bg-brand/10' : 'border-surface-border hover:border-surface-lighter'}`}>
              <div className="text-sm font-medium text-white">{p.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{p.note}</div>
            </button>
          ))}
        </div>

        {/* Priority filter */}
        <div className="mb-4">
          <label className="text-xs text-gray-400 mb-1 block">Minimum priority to push</label>
          <select value={pushConfig.minPriority} onChange={e => setPushConfig(c => ({ ...c, minPriority: e.target.value }))}
            className="input w-full">
            {PRIORITY_LABELS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
        </div>

        {/* Provider-specific fields */}
        {pushConfig.provider === 'ntfy' && (
          <div className="space-y-3 p-4 bg-surface rounded-xl border border-surface-border mb-4">
            <div className="text-xs text-gray-400 mb-1">
              1. Install <span className="text-brand">ntfy</span> from the App Store on your iPhone.<br />
              2. Subscribe to any topic name you choose (e.g. <code className="bg-surface-lighter px-1 rounded">agentharness-david</code>).<br />
              3. Notifications auto-mirror to your paired Apple Watch.
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Topic Name</label>
              <input value={pushConfig.ntfyTopic} onChange={e => setPushConfig(c => ({ ...c, ntfyTopic: e.target.value }))}
                className="input w-full" placeholder="agentharness-david" />
              <div className="text-xs text-gray-500 mt-1">Must match the topic subscribed in the ntfy iOS app.</div>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">ntfy Server (leave default for ntfy.sh)</label>
              <input value={pushConfig.ntfyServer} onChange={e => setPushConfig(c => ({ ...c, ntfyServer: e.target.value }))}
                className="input w-full" placeholder="https://ntfy.sh" />
            </div>
          </div>
        )}

        {pushConfig.provider === 'pushover' && (
          <div className="space-y-3 p-4 bg-surface rounded-xl border border-surface-border mb-4">
            <div className="text-xs text-gray-400 mb-1">
              1. Buy the Pushover app ($5 one-time) from the App Store.<br />
              2. Register at <span className="text-brand">pushover.net</span> → copy your User Key.<br />
              3. Create an Application → copy the API Token.
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">API Token</label>
              <input type="password" value={pushConfig.pushoverToken === '***' ? '' : pushConfig.pushoverToken}
                onChange={e => setPushConfig(c => ({ ...c, pushoverToken: e.target.value }))}
                className="input w-full" placeholder="App API token from pushover.net" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">User Key</label>
              <input value={pushConfig.pushoverUser} onChange={e => setPushConfig(c => ({ ...c, pushoverUser: e.target.value }))}
                className="input w-full" placeholder="User key from pushover.net" />
            </div>
          </div>
        )}

        {pushConfig.provider === 'pushcut' && (
          <div className="space-y-3 p-4 bg-surface rounded-xl border border-surface-border mb-4">
            <div className="text-xs text-gray-400 mb-1">
              1. Install <span className="text-brand">Pushcut</span> from the App Store.<br />
              2. Create a notification → enable "Webhook Trigger" → copy the URL.<br />
              3. Optional: add an Apple Watch complication in the Pushcut app.
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Pushcut Webhook URL</label>
              <input value={pushConfig.pushcutWebhook} onChange={e => setPushConfig(c => ({ ...c, pushcutWebhook: e.target.value }))}
                className="input w-full" placeholder="https://api.pushcut.io/..." />
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <button onClick={savePush} className="btn-primary text-sm">Save Push Settings</button>
          {pushConfig.enabled && (
            <button onClick={testPush} disabled={testing}
              className="btn-secondary text-sm disabled:opacity-50">
              {testing ? 'Sending...' : '⌚ Send Test to Watch'}
            </button>
          )}
        </div>
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

      {/* Security */}
      <section className="card mb-6">
        <h2 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
          🔒 Security
          <span className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${security.authEnabled ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'}`}>
            {security.authEnabled ? 'Protected' : 'Open (LAN only)'}
          </span>
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          {security.authEnabled
            ? 'Bearer token authentication is active. Remote access is safe.'
            : '⚠️ No access token set. Safe on local network only. Set a token before exposing to the internet.'}
        </p>
        <div className="flex gap-2">
          <button onClick={generateToken} className="btn-primary text-sm">
            {security.authEnabled ? '🔄 Rotate Token' : '🔑 Enable Auth (Generate Token)'}
          </button>
          {security.authEnabled && (
            <button onClick={disableAuth} className="btn-secondary text-sm text-error/80 border-error/20">
              Disable Auth
            </button>
          )}
        </div>
        {security.authEnabled && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-gray-400">If accessing from a remote browser, paste the token here to authenticate this client:</p>
            <div className="flex gap-2">
              <input type="password" value={clientToken} onChange={e => setClientToken(e.target.value)}
                className="input flex-1 text-sm" placeholder="Paste access token..." />
              <button onClick={() => { setStoredToken(clientToken); flash('Token saved — this browser is now authenticated') }}
                className="btn-primary text-sm px-3">Save</button>
              <button onClick={() => { setClientToken(''); setStoredToken(''); flash('Token cleared') }}
                className="btn-secondary text-sm px-3">Clear</button>
            </div>
          </div>
        )}
        {security.authEnabled && (
          <p className="text-xs text-gray-500 mt-3">
            Add your token to <code className="bg-surface-lighter px-1 rounded">.env</code> as <code className="bg-surface-lighter px-1 rounded">ACCESS_TOKEN=&lt;token&gt;</code> so it persists across restarts.
            Clients must send <code className="bg-surface-lighter px-1 rounded">Authorization: Bearer &lt;token&gt;</code> header.
          </p>
        )}

        {/* Change Password */}
        <div className="mt-5 pt-4 border-t border-surface-border">
          <h3 className="text-sm font-medium text-white mb-3">🔑 Change Password</h3>
          {pwMsg && (
            <div className={`text-xs mb-3 px-3 py-2 rounded-lg border ${pwMsg.ok ? 'bg-success/10 border-success/20 text-success' : 'bg-error/10 border-error/20 text-error'}`}>
              {pwMsg.text}
            </div>
          )}
          <div className="space-y-2">
            <input type="password" placeholder="Current password" value={pwForm.currentPassword}
              onChange={e => setPwForm(f => ({ ...f, currentPassword: e.target.value }))}
              className="input w-full text-sm" />
            <input type="password" placeholder="New password (min 8 chars)" value={pwForm.newPassword}
              onChange={e => setPwForm(f => ({ ...f, newPassword: e.target.value }))}
              className="input w-full text-sm" />
            <input type="password" placeholder="Confirm new password" value={pwForm.confirm}
              onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))}
              className="input w-full text-sm" />
            <button
              disabled={!pwForm.currentPassword || !pwForm.newPassword || pwForm.newPassword !== pwForm.confirm}
              onClick={async () => {
                if (pwForm.newPassword !== pwForm.confirm) { setPwMsg({ ok: false, text: 'Passwords do not match' }); return }
                try {
                  const res = await fetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getStoredToken()}` },
                    body: JSON.stringify({ currentPassword: pwForm.currentPassword, newPassword: pwForm.newPassword })
                  })
                  const data = await res.json()
                  if (res.ok) { setPwMsg({ ok: true, text: 'Password changed successfully!' }); setPwForm({ currentPassword: '', newPassword: '', confirm: '' }) }
                  else setPwMsg({ ok: false, text: data.error || 'Failed to change password' })
                } catch { setPwMsg({ ok: false, text: 'Server error' }) }
              }}
              className="btn-primary text-sm disabled:opacity-40">
              Update Password
            </button>
          </div>
        </div>
      </section>

      {/* ClouDNS DDNS + Remote Access */}
      <section className="card">
        <h2 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
          🌐 Remote Access — ClouDNS DDNS
          {ddnsConfig.enabled && (
            <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium bg-success/20 text-success">Active</span>
          )}
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          Keep your domain's DNS A record pointed at this server's public IP. Pair with Caddy for automatic HTTPS.
          {publicIp && <span className="ml-2 text-brand-light">Current public IP: <strong>{publicIp}</strong></span>}
        </p>

        {/* Enable toggle */}
        <div className="flex items-center gap-3 mb-5">
          <button onClick={() => setDdnsConfig(c => ({ ...c, enabled: !c.enabled }))}
            className={`relative w-12 h-6 rounded-full transition-colors ${ddnsConfig.enabled ? 'bg-brand' : 'bg-surface-border'}`}>
            <span className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-transform ${ddnsConfig.enabled ? 'translate-x-7' : 'translate-x-1'}`} />
          </button>
          <span className="text-sm text-gray-300">{ddnsConfig.enabled ? 'DDNS enabled' : 'DDNS disabled'}</span>
        </div>

        {/* Method picker */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          {[
            { id: 'dynamic-url', label: '🔗 Dynamic URL', note: 'Simplest. Paste the URL from ClouDNS panel.' },
            { id: 'api', label: '⚙️ API Credentials', note: 'Full control. Uses ClouDNS auth-id + password.' }
          ].map(m => (
            <button key={m.id} onClick={() => setDdnsConfig(c => ({ ...c, method: m.id }))}
              className={`text-left p-3 rounded-xl border transition-all ${ddnsConfig.method === m.id ? 'border-brand/50 bg-brand/10' : 'border-surface-border hover:border-surface-lighter'}`}>
              <div className="text-sm font-medium text-white">{m.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{m.note}</div>
            </button>
          ))}
        </div>

        {ddnsConfig.method === 'dynamic-url' ? (
          <div className="space-y-3 p-4 bg-surface rounded-xl border border-surface-border mb-4">
            <div className="text-xs text-gray-400">
              1. Log into <span className="text-brand">ClouDNS.net</span> → DNS Hosting → your domain → Dynamic DNS tab.<br />
              2. Add a dynamic record for your hostname (e.g. <code className="bg-surface-lighter px-1 rounded">home</code>).<br />
              3. Click <strong>Generate URL</strong> → copy the full Dynamic URL and paste below.
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">ClouDNS Dynamic URL</label>
              <input value={ddnsConfig.dynamicUrl} onChange={e => setDdnsConfig(c => ({ ...c, dynamicUrl: e.target.value }))}
                className="input w-full" placeholder="https://ipv4.cloudns.net/api/dynamicURL/?q=xxxxxxxx" />
            </div>
          </div>
        ) : (
          <div className="space-y-3 p-4 bg-surface rounded-xl border border-surface-border mb-4">
            <div className="text-xs text-gray-400">
              Get your auth-id from <span className="text-brand">ClouDNS.net</span> → API → Manage API credentials.
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Auth ID</label>
                <input value={ddnsConfig.authId} onChange={e => setDdnsConfig(c => ({ ...c, authId: e.target.value }))}
                  className="input w-full" placeholder="12345" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Auth Password</label>
                <input type="password" value={ddnsConfig.authPassword === '***' ? '' : ddnsConfig.authPassword}
                  onChange={e => setDdnsConfig(c => ({ ...c, authPassword: e.target.value }))}
                  className="input w-full" placeholder="your API password" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Domain Name</label>
                <input value={ddnsConfig.domain} onChange={e => setDdnsConfig(c => ({ ...c, domain: e.target.value }))}
                  className="input w-full" placeholder="yourdomain.com" />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Hostname</label>
                <input value={ddnsConfig.host} onChange={e => setDdnsConfig(c => ({ ...c, host: e.target.value }))}
                  className="input w-full" placeholder="@ or home or agent" />
                <div className="text-xs text-gray-600 mt-1">@ = root domain, or enter subdomain</div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">TTL (seconds)</label>
            <select value={ddnsConfig.ttl} onChange={e => setDdnsConfig(c => ({ ...c, ttl: parseInt(e.target.value) }))} className="input w-full">
              <option value={60}>60s (1 min)</option>
              <option value={300}>300s (5 min)</option>
              <option value={900}>900s (15 min)</option>
              <option value={3600}>3600s (1 hour)</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Update Interval</label>
            <select value={ddnsConfig.updateIntervalMin} onChange={e => setDdnsConfig(c => ({ ...c, updateIntervalMin: parseInt(e.target.value) }))} className="input w-full">
              <option value={2}>Every 2 min</option>
              <option value={5}>Every 5 min</option>
              <option value={10}>Every 10 min</option>
              <option value={30}>Every 30 min</option>
            </select>
          </div>
        </div>

        {ddnsStatus && (
          <div className={`mb-4 p-3 rounded-xl text-sm ${ddnsStatus.error ? 'bg-error/10 border border-error/30 text-error' : 'bg-success/10 border border-success/30 text-success'}`}>
            {ddnsStatus.error ? `✗ ${ddnsStatus.error}` : `✓ ${ddnsStatus.ip} — ${ddnsStatus.status}`}
          </div>
        )}

        <div className="flex gap-2 mb-6">
          <button onClick={saveDdns} className="btn-primary text-sm">Save DDNS Settings</button>
          <button onClick={testDdns} disabled={ddnsUpdating || !ddnsConfig.enabled} className="btn-secondary text-sm disabled:opacity-40">
            {ddnsUpdating ? 'Updating...' : '🔄 Update DNS Now'}
          </button>
          <button onClick={() => api('/settings/ddns/ip').then(d => setPublicIp(d.ip)).catch(() => {})}
            className="btn-secondary text-sm">
            Check IP
          </button>
        </div>

        {/* Caddy HTTPS setup */}
        <div className="border-t border-surface-border pt-5">
          <h3 className="text-sm font-semibold text-white mb-2">🔐 HTTPS with Caddy (Auto SSL)</h3>
          <p className="text-xs text-gray-500 mb-3">
            Caddy automatically gets a free Let's Encrypt certificate for your domain. 
            Requires port 80 and 443 forwarded on your router to this machine.
          </p>
          <div className="bg-surface rounded-xl p-4 font-mono text-sm text-gray-300 space-y-2 text-xs">
            <div className="text-gray-500"># 1. Install Caddy (Windows)</div>
            <div>winget install Caddy.Caddy</div>
            <div className="text-gray-500 mt-2"># 2. Create Caddyfile (in the same folder)</div>
            <div className="bg-surface-lighter rounded p-3 my-1">
              <div>{ddnsConfig.domain || 'yourdomain.com'} {'{'}</div>
              <div>&nbsp;&nbsp;reverse_proxy localhost:4000</div>
              <div>{'}'}</div>
            </div>
            <div className="text-gray-500"># 3. Run Caddy (auto-fetches SSL cert)</div>
            <div>caddy run</div>
            <div className="text-gray-500 mt-2"># 4. Optional: run Caddy as a Windows service</div>
            <div>caddy start</div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Once running: <strong>{ddnsConfig.host && ddnsConfig.host !== '@' ? `https://${ddnsConfig.host}.` : 'https://'}{ddnsConfig.domain || 'yourdomain.com'}</strong> will serve AgentHarness over HTTPS automatically.
          </p>
        </div>
      </section>
    </div>
  )
}