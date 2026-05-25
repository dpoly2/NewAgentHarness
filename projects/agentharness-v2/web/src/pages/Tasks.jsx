import { useState, useEffect } from 'react'
import { marked } from 'marked'
import { api, useSocket } from '../hooks/useSocket'

export default function Tasks({ roster }) {
  const [queue, setQueue] = useState({ running: [], queued: [], recent: [] })
  const [selectedTask, setSelectedTask] = useState(null)
  const [newTask, setNewTask] = useState({ title: '', description: '', agentId: '', projectSlug: 'global' })
  const [showAdd, setShowAdd] = useState(false)
  const [agentInput, setAgentInput] = useState('')

  useSocket({
    'task:queued': t => setQueue(p => ({ ...p, queued: [t, ...p.queued] })),
    'task:started': t => setQueue(p => ({ ...p, running: [t, ...p.running.filter(x => x.id !== t.id)], queued: p.queued.filter(x => x.id !== t.id) })),
    'task:completed': t => setQueue(p => ({ ...p, running: p.running.filter(x => x.id !== t.id), recent: [t, ...p.recent].slice(0, 20) })),
    'task:failed': t => setQueue(p => ({ ...p, running: p.running.filter(x => x.id !== t.id), recent: [t, ...p.recent].slice(0, 20) })),
  })

  useEffect(() => {
    api('/tasks/queue').then(setQueue).catch(console.error)
  }, [])

  async function submitTask() {
    if (!newTask.title || !newTask.agentId) return
    await api('/tasks', { method: 'POST', body: newTask })
    setNewTask({ title: '', description: '', agentId: '', projectSlug: 'global' })
    setShowAdd(false)
  }

  async function cancelTask(id) {
    await api(`/tasks/${id}`, { method: 'DELETE' })
    setQueue(p => ({ ...p, queued: p.queued.filter(t => t.id !== id) }))
  }

  const allAgents = roster?.projects?.flatMap(p => [p.leadAgent, ...(p.specialists || []).map(s => s.name)]) || []
  const projects = roster?.projects || []

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-white">Task Queue</h1>
          <p className="text-sm text-gray-500 mt-1">Agent work — {queue.running.length} running, {queue.queued.length} queued</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary">⚡ New Task</button>
      </div>

      {/* New task form */}
      {showAdd && (
        <div className="card mb-5 space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">Assign Task to Agent</h3>
          <input value={newTask.title} onChange={e => setNewTask(p => ({ ...p, title: e.target.value }))} className="input w-full" placeholder="Task title..." />
          <textarea value={newTask.description} onChange={e => setNewTask(p => ({ ...p, description: e.target.value }))} className="input w-full resize-none" rows={3} placeholder="Detailed description for the agent..." />
          <div className="flex gap-2">
            <input value={newTask.agentId} onChange={e => setNewTask(p => ({ ...p, agentId: e.target.value }))} className="input flex-1" placeholder="Agent ID (e.g. yepc-grant-writer-agent)" list="agent-list" />
            <datalist id="agent-list">{allAgents.map(a => <option key={a} value={a} />)}</datalist>
            <select value={newTask.projectSlug} onChange={e => setNewTask(p => ({ ...p, projectSlug: e.target.value }))} className="input">
              <option value="global">Global</option>
              {projects.map(p => <option key={p.slug} value={p.slug}>{p.slug}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={submitTask} className="btn-primary text-sm">Queue Task</button>
            <button onClick={() => setShowAdd(false)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </div>
      )}

      {/* Running */}
      {queue.running.length > 0 && (
        <Section title="Running" color="blue" icon="⚡">
          {queue.running.map(t => <TaskCard key={t.id} task={t} onSelect={setSelectedTask} />)}
        </Section>
      )}

      {/* Queued */}
      {queue.queued.length > 0 && (
        <Section title="Queued" color="gray" icon="📋">
          {queue.queued.map(t => <TaskCard key={t.id} task={t} onSelect={setSelectedTask} onCancel={cancelTask} />)}
        </Section>
      )}

      {/* Recent */}
      <Section title="Completed" color="green" icon="✅">
        {queue.recent.length === 0 && <div className="text-sm text-gray-500 px-1">No completed tasks yet</div>}
        {queue.recent.map(t => <TaskCard key={t.id} task={t} onSelect={setSelectedTask} />)}
      </Section>

      {/* Task detail modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setSelectedTask(null)}>
          <div className="bg-surface-light border border-surface-border rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
              <div>
                <h2 className="font-bold text-white">{selectedTask.title}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`status-${selectedTask.status}`}>{selectedTask.status}</span>
                  <span className="text-xs text-gray-500">{selectedTask.agent_id}</span>
                  {selectedTask.duration_ms > 0 && <span className="text-xs text-gray-600">{(selectedTask.duration_ms/1000).toFixed(1)}s</span>}
                </div>
              </div>
              <button onClick={() => setSelectedTask(null)} className="btn-ghost text-xs">✕ Close</button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div>
                <div className="text-xs font-semibold text-gray-400 uppercase mb-1.5">Description</div>
                <div className="text-sm text-gray-300">{selectedTask.description}</div>
              </div>
              {selectedTask.result && (
                <div>
                  <div className="text-xs font-semibold text-gray-400 uppercase mb-1.5">Result</div>
                  <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: marked(selectedTask.result) }} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Section({ title, icon, color, children }) {
  const colors = { blue: 'text-blue-400', gray: 'text-gray-400', green: 'text-green-400' }
  return (
    <div className="mb-6">
      <h2 className={`text-sm font-semibold mb-3 flex items-center gap-2 ${colors[color]}`}>
        <span>{icon}</span> {title}
      </h2>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function TaskCard({ task, onSelect, onCancel }) {
  return (
    <div className="card-sm flex items-start gap-3 cursor-pointer hover:border-brand/30 transition-colors" onClick={() => onSelect(task)}>
      <span className={`status-${task.status} flex-shrink-0 mt-0.5`}>{task.status}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white truncate">{task.title}</div>
        <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
          <span>{task.agent_id}</span>
          <span className="text-gray-700">·</span>
          <span>{task.project_slug}</span>
          {task.duration_ms > 0 && <span className="text-gray-700">· {(task.duration_ms/1000).toFixed(1)}s</span>}
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {task.result && <span className="text-xs text-brand-light">View →</span>}
        {onCancel && task.status === 'queued' && (
          <button onClick={e => { e.stopPropagation(); onCancel(task.id) }} className="text-xs text-gray-600 hover:text-red-400 transition-colors px-2 py-1">Cancel</button>
        )}
      </div>
    </div>
  )
}
