import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const API = (path, opts) => {
  const token = localStorage.getItem('agentharness_token')
  return fetch(path, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(opts?.headers || {}) }
  }).then(r => r.json())
}

const NODE_COLORS = {
  '[ActNode]':       '#8b5cf6',
  '[EvaluateNode]':  '#f59e0b',
  '[MemoryNode]':    '#0ea5e9',
  '[ResearchGraph]': '#3b82f6',
  '[WPGraph]':       '#06b6d4',
  'REVISE':          '#ef4444',
  'SAVE':            '#22c55e',
  'REFLEXION RUN':   '#5b5ff5',
  'COMPLETE':        '#22c55e',
  'ERROR':           '#ef4444',
  'Score:':          '#22c55e',
}

function getLineColor(text) {
  for (const [key, color] of Object.entries(NODE_COLORS)) {
    if (text.includes(key)) return color
  }
  return null
}

const GRAPHS = ['reflexion', 'research', 'wordpress']
const PROJECTS = [
  'xftc','yepc','pbs-foundation','s2tdesigns','smithcap','smithcap-finance',
  'ministry','social-media','solar-repair','sigma-signal','nutrue','elevation','travel'
]

export default function AgentRunner() {
  const [agents, setAgents]         = useState([])
  const [runs, setRuns]             = useState([])
  const [selectedAgent, setAgent]   = useState('')
  const [selectedProject, setProj]  = useState('xftc')
  const [graph, setGraph]           = useState('reflexion')
  const [task, setTask]             = useState('')
  const [maxRev, setMaxRev]         = useState(3)
  const [activeTab, setTab]         = useState('log')
  const [logs, setLogs]             = useState([])
  const [output, setOutput]         = useState('')
  const [runStatus, setRunStatus]   = useState(null)   // null | 'running' | 'complete' | 'error' | 'stopped'
  const [lastScore, setLastScore]   = useState(null)
  const [lastRevisions, setRevisions] = useState(null)
  const [currentRunId, setRunId]    = useState(null)
  const [skillContent, setSkill]    = useState('')
  const [skillAgent, setSkillAgent] = useState('')
  const [apiKeyOk, setApiKeyOk]     = useState(null)
  const logEndRef = useRef(null)
  const sseRef    = useRef(null)
  const navigate  = useNavigate()

  useEffect(() => {
    API('/api/agent-runner/agents').then(data => {
      if (Array.isArray(data)) {
        setAgents(data)
        if (data.length > 0) setAgent(data[0].id)
      }
    })
    API('/api/agent-runner/runs').then(data => {
      if (Array.isArray(data)) setRuns(data)
    })
    // Check OpenAI key by seeing if a quick env check works
    fetch('/api/agent-runner/agents').then(r => setApiKeyOk(r.ok)).catch(() => setApiKeyOk(false))
  }, [])

  useEffect(() => {
    if (logEndRef.current) logEndRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const startRun = async () => {
    if (!task.trim()) return
    setLogs([{ text: `Starting run: ${graph} | ${selectedAgent} | ${selectedProject}`, type: 'info', color: '#5b5ff5' }])
    setOutput('')
    setRunStatus('running')
    setLastScore(null)
    setRevisions(null)
    setTab('log')

    const result = await API('/api/agent-runner/run', {
      method: 'POST',
      body: JSON.stringify({ agent: selectedAgent, project: selectedProject, task, graph, maxRevisions: maxRev })
    })

    if (result.error) {
      setLogs(prev => [...prev, { text: result.error, type: 'error', color: '#ef4444' }])
      setRunStatus('error')
      return
    }

    const runId = result.runId
    setRunId(runId)

    // SSE stream
    const token = localStorage.getItem('agentharness_token')
    const url   = `/api/agent-runner/stream/${runId}`
    const es    = new EventSource(url + (token ? `?token=${token}` : ''))
    sseRef.current = es

    es.onmessage = (e) => {
      const item = JSON.parse(e.data)
      if (item.type === 'done') {
        setRunStatus(item.status)
        if (item.score !== null && item.score !== undefined) setLastScore(item.score)
        if (item.revisions !== null && item.revisions !== undefined) setRevisions(item.revisions)
        API('/api/agent-runner/runs').then(data => { if (Array.isArray(data)) setRuns(data) })
        es.close()
      } else {
        const color = getLineColor(item.text) || (item.type === 'stderr' ? '#94a3b8' : null)
        setLogs(prev => [...prev, { ...item, color }])
        setOutput(prev => prev + item.text + '\n')
      }
    }
    es.onerror = () => {
      setRunStatus(prev => prev === 'running' ? 'error' : prev)
      es.close()
    }
  }

  const stopRun = async () => {
    if (currentRunId) {
      await API(`/api/agent-runner/run/${currentRunId}/stop`, { method: 'POST' })
      if (sseRef.current) sseRef.current.close()
      setRunStatus('stopped')
    }
  }

  const loadSkill = async (agentId) => {
    setSkillAgent(agentId)
    setTab('skill')
    const result = await API(`/api/agent-runner/skill/${encodeURIComponent(agentId)}`)
    setSkill(result.content || result.error || 'Not found')
  }

  const scoreColor = (s) => s >= 0.75 ? '#22c55e' : s >= 0.5 ? '#f59e0b' : '#ef4444'

  // Group agents by project
  const agentsByProject = {}
  for (const a of agents) {
    if (!agentsByProject[a.project]) agentsByProject[a.project] = []
    agentsByProject[a.project].push(a)
  }

  return (
    <div className="flex flex-col h-full bg-background text-white overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-surface-border bg-surface flex-shrink-0">
        <div>
          <h1 className="text-lg font-bold">🧠 Agent Runner</h1>
          <p className="text-xs text-gray-500">LangGraph + Reflexion Engine — powered by OpenAI</p>
        </div>
        <div className="flex items-center gap-3">
          {apiKeyOk === false && (
            <span className="text-xs text-red-400 bg-red-900/30 px-2 py-1 rounded">⚠ API unreachable</span>
          )}
          <div className="text-xs text-gray-500 text-right">
            <div className="font-medium text-gray-300">{runs.length} runs total</div>
            <div>{agents.length} agents loaded</div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left panel: controls ── */}
        <div className="w-72 flex-shrink-0 bg-surface border-r border-surface-border flex flex-col overflow-y-auto">
          <div className="p-4 space-y-4">

            {/* Graph type */}
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Graph Type</div>
              <div className="flex gap-2">
                {GRAPHS.map(g => (
                  <button key={g} onClick={() => setGraph(g)}
                    className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${graph === g ? 'bg-brand text-white' : 'bg-surface-lighter text-gray-400 hover:text-white'}`}>
                    {g}
                  </button>
                ))}
              </div>
            </div>

            {/* Agent */}
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Agent</div>
              <select value={selectedAgent} onChange={e => setAgent(e.target.value)}
                className="w-full bg-surface-lighter border border-surface-border text-white text-sm rounded px-3 py-2 focus:outline-none focus:border-brand">
                {Object.entries(agentsByProject).map(([proj, agts]) => (
                  <optgroup key={proj} label={proj.toUpperCase()}>
                    {agts.map(a => <option key={a.id} value={a.id}>{a.id}</option>)}
                  </optgroup>
                ))}
              </select>
              {selectedAgent && (
                <button onClick={() => loadSkill(selectedAgent)}
                  className="mt-1 text-xs text-brand hover:underline">
                  View skill file →
                </button>
              )}
            </div>

            {/* Project */}
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Project</div>
              <select value={selectedProject} onChange={e => setProj(e.target.value)}
                className="w-full bg-surface-lighter border border-surface-border text-white text-sm rounded px-3 py-2 focus:outline-none focus:border-brand">
                {PROJECTS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            {/* Task */}
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Task</div>
              <textarea value={task} onChange={e => setTask(e.target.value)}
                rows={5} placeholder="Describe the task for this agent..."
                className="w-full bg-surface-lighter border border-surface-border text-white text-sm rounded px-3 py-2 focus:outline-none focus:border-brand resize-none font-mono" />
            </div>

            {/* Max revisions */}
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Max Revisions</div>
              <div className="flex gap-2">
                {[1,2,3].map(n => (
                  <button key={n} onClick={() => setMaxRev(n)}
                    className={`w-9 h-9 rounded text-sm font-bold transition-all ${maxRev === n ? 'bg-brand text-white' : 'bg-surface-lighter text-gray-400 hover:text-white'}`}>
                    {n}
                  </button>
                ))}
              </div>
            </div>

            {/* Run / Stop */}
            <button onClick={runStatus === 'running' ? stopRun : startRun}
              disabled={!task.trim() || !selectedAgent}
              className={`w-full py-3 rounded font-bold text-sm transition-all ${
                runStatus === 'running'
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-brand hover:bg-brand/80 text-white disabled:opacity-40 disabled:cursor-not-allowed'
              }`}>
              {runStatus === 'running' ? '■ STOP' : '▶ RUN AGENT'}
            </button>

            {/* Score card */}
            {lastScore !== null && (
              <div className="bg-surface-lighter rounded-lg p-4 border border-surface-border">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Last Run Score</div>
                <div className="flex items-baseline gap-3">
                  <span className="text-4xl font-bold" style={{ color: scoreColor(lastScore) }}>
                    {(lastScore * 100).toFixed(0)}
                  </span>
                  <div className="text-xs text-gray-500">
                    <div>/ 100</div>
                    {lastRevisions !== null && <div>{lastRevisions} revision{lastRevisions !== 1 ? 's' : ''}</div>}
                  </div>
                </div>
                <div className={`text-xs mt-1 font-medium ${lastScore >= 0.75 ? 'text-green-400' : lastScore >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {lastScore >= 0.75 ? '✓ Passed' : lastScore >= 0.5 ? '~ Marginal' : '✗ Below threshold'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Right panel: tabs ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-surface-border bg-surface flex-shrink-0">
            {[
              { id: 'log',     label: 'Execution Log' },
              { id: 'output',  label: 'Output' },
              { id: 'history', label: `History (${runs.length})` },
              { id: 'skill',   label: `Skill File${skillAgent ? `: ${skillAgent}` : ''}` },
            ].map(tab => (
              <button key={tab.id} onClick={() => setTab(tab.id)}
                className={`px-5 py-3 text-sm transition-all border-b-2 ${activeTab === tab.id ? 'text-white border-brand' : 'text-gray-500 border-transparent hover:text-gray-300'}`}>
                {tab.label}
              </button>
            ))}
            {runStatus && (
              <div className={`ml-auto mr-4 self-center text-xs px-3 py-1 rounded-full font-medium ${
                runStatus === 'running' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' :
                runStatus === 'complete' ? 'bg-green-500/20 text-green-400' :
                runStatus === 'error' || runStatus === 'stopped' ? 'bg-red-500/20 text-red-400' : ''
              }`}>
                {runStatus === 'running' ? '⟳ Running...' : runStatus === 'complete' ? '✓ Complete' : runStatus === 'stopped' ? '■ Stopped' : '✗ Error'}
              </div>
            )}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden relative">

            {/* Execution Log */}
            {activeTab === 'log' && (
              <div className="h-full overflow-y-auto p-4 font-mono text-xs bg-background">
                {logs.length === 0 && (
                  <div className="text-gray-600 mt-8 text-center">
                    Configure an agent and click ▶ RUN AGENT to start
                  </div>
                )}
                {logs.map((item, i) => (
                  <div key={i} className="flex gap-3 leading-relaxed hover:bg-surface-lighter/30 px-1 rounded">
                    <span className="text-gray-600 flex-shrink-0 select-none">
                      {new Date().toTimeString().slice(0, 8)}
                    </span>
                    <span style={item.color ? { color: item.color } : {}} className={item.color ? '' : 'text-gray-300'}>
                      {item.text}
                    </span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            )}

            {/* Output */}
            {activeTab === 'output' && (
              <div className="h-full overflow-y-auto p-4 bg-background">
                {!output ? (
                  <div className="text-gray-600 mt-8 text-center text-sm">Output will appear here after a run completes</div>
                ) : (
                  <>
                    <div className="flex justify-end mb-3">
                      <button onClick={() => navigator.clipboard.writeText(output)}
                        className="text-xs text-gray-500 hover:text-white px-3 py-1 bg-surface-lighter rounded">
                        Copy
                      </button>
                    </div>
                    <pre className="text-sm text-gray-200 whitespace-pre-wrap font-mono leading-relaxed">{output}</pre>
                  </>
                )}
              </div>
            )}

            {/* History */}
            {activeTab === 'history' && (
              <div className="h-full overflow-y-auto">
                {runs.length === 0 ? (
                  <div className="text-gray-600 mt-8 text-center text-sm">No runs yet</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-surface border-b border-surface-border">
                      <tr>
                        {['Agent','Project','Graph','Score','Revisions','Status','Time'].map(h => (
                          <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {runs.map(run => (
                        <tr key={run.id} className="border-b border-surface-border hover:bg-surface-lighter/50 cursor-pointer"
                          onClick={() => { setLogs([{ text: run.output || '(no output)', type: 'log' }]); setOutput(run.output || ''); setTab('output') }}>
                          <td className="px-4 py-3 font-mono text-xs text-gray-300">{run.agent}</td>
                          <td className="px-4 py-3 text-gray-400">{run.project}</td>
                          <td className="px-4 py-3 text-gray-400">{run.graph}</td>
                          <td className="px-4 py-3 font-bold" style={run.score !== null ? { color: scoreColor(run.score) } : {}}>
                            {run.score !== null ? `${(run.score * 100).toFixed(0)}` : '—'}
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-center">{run.revisions ?? '—'}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              run.status === 'complete' ? 'bg-green-500/20 text-green-400' :
                              run.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-red-500/20 text-red-400'
                            }`}>{run.status}</span>
                          </td>
                          <td className="px-4 py-3 text-gray-500 text-xs">{new Date(run.startedAt).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* Skill File */}
            {activeTab === 'skill' && (
              <div className="h-full overflow-y-auto p-4 bg-background">
                {!skillContent ? (
                  <div className="text-gray-600 mt-8 text-center text-sm">
                    Select an agent and click "View skill file" to load it here
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm font-medium text-gray-300">📄 {skillAgent}</div>
                      <button onClick={() => navigator.clipboard.writeText(skillContent)}
                        className="text-xs text-gray-500 hover:text-white px-3 py-1 bg-surface-lighter rounded">
                        Copy
                      </button>
                    </div>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed bg-surface rounded p-4">{skillContent}</pre>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
