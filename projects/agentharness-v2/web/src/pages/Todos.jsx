import { useState, useEffect } from 'react'
import { api, useSocket } from '../hooks/useSocket'

export default function Todos({ roster }) {
  const [todos, setTodos] = useState([])
  const [filter, setFilter] = useState({ status: 'pending', project: '', priority: '' })
  const [newTodo, setNewTodo] = useState({ title: '', description: '', priority: 'medium', projectSlug: 'global', dueDate: '' })
  const [showAdd, setShowAdd] = useState(false)

  useSocket({
    'todo:created': t => setTodos(prev => [t, ...prev]),
  })

  const projects = roster?.projects || []

  async function loadTodos() {
    try {
      const params = new URLSearchParams()
      if (filter.status !== 'all') params.set('status', filter.status)
      if (filter.project) params.set('project_slug', filter.project)
      if (filter.priority) params.set('priority', filter.priority)
      const data = await api(`/todos?${params}`)
      setTodos(data)
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadTodos() }, [filter])

  async function updateTodo(id, updates) {
    await api(`/todos/${id}`, { method: 'PATCH', body: updates })
    setTodos(prev => prev.map(t => t.id === id ? { ...t, ...updates } : t))
  }

  async function deleteTodo(id) {
    await api(`/todos/${id}`, { method: 'DELETE' })
    setTodos(prev => prev.filter(t => t.id !== id))
  }

  async function addTodo() {
    if (!newTodo.title.trim()) return
    const todo = await api('/todos', { method: 'POST', body: newTodo })
    setTodos(prev => [todo, ...prev])
    setNewTodo({ title: '', description: '', priority: 'medium', projectSlug: 'global', dueDate: '' })
    setShowAdd(false)
  }

  const ICONS = { xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️', ministry:'⛪', finance:'💰', personal:'🗓️', global:'✨' }
  const PRIORITY_COLORS = { urgent: 'text-red-400', high: 'text-yellow-400', medium: 'text-blue-400', low: 'text-gray-400' }

  return (
    <div className="p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-white">Todos</h1>
          <p className="text-sm text-gray-500 mt-1">{todos.length} items · populated by AgentMajesty and agents</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary">＋ Add Todo</button>
      </div>

      {/* Add todo form */}
      {showAdd && (
        <div className="card mb-5 space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">New Todo</h3>
          <input value={newTodo.title} onChange={e => setNewTodo(p => ({ ...p, title: e.target.value }))}
            className="input w-full" placeholder="Todo title..." />
          <textarea value={newTodo.description} onChange={e => setNewTodo(p => ({ ...p, description: e.target.value }))}
            className="input w-full resize-none" rows={2} placeholder="Description (optional)..." />
          <div className="flex gap-2 flex-wrap">
            <select value={newTodo.priority} onChange={e => setNewTodo(p => ({ ...p, priority: e.target.value }))} className="input text-sm">
              {['urgent','high','medium','low'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select value={newTodo.projectSlug} onChange={e => setNewTodo(p => ({ ...p, projectSlug: e.target.value }))} className="input text-sm">
              <option value="global">Global</option>
              {projects.map(p => <option key={p.slug} value={p.slug}>{p.name}</option>)}
            </select>
            <input type="date" value={newTodo.dueDate} onChange={e => setNewTodo(p => ({ ...p, dueDate: e.target.value }))} className="input text-sm" />
          </div>
          <div className="flex gap-2">
            <button onClick={addTodo} className="btn-primary text-sm">Add</button>
            <button onClick={() => setShowAdd(false)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {[['pending','Pending'], ['in_progress','In Progress'], ['done','Done'], ['all','All']].map(([v, l]) => (
          <button key={v} onClick={() => setFilter(f => ({ ...f, status: v }))}
            className={`text-sm px-3 py-1.5 rounded-full transition-colors ${filter.status === v ? 'bg-brand/15 text-brand-light border border-brand/30' : 'border border-surface-border text-gray-500 hover:text-gray-300'}`}>
            {l}
          </button>
        ))}
        <select value={filter.project} onChange={e => setFilter(f => ({ ...f, project: e.target.value }))} className="input text-sm py-1.5">
          <option value="">All Projects</option>
          {projects.map(p => <option key={p.slug} value={p.slug}>{p.name}</option>)}
        </select>
        <select value={filter.priority} onChange={e => setFilter(f => ({ ...f, priority: e.target.value }))} className="input text-sm py-1.5">
          <option value="">All Priorities</option>
          {['urgent','high','medium','low'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {/* Todo list */}
      <div className="space-y-2">
        {todos.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <div className="text-3xl mb-2">✅</div>
            <div className="text-sm">No todos found. Chat with AgentMajesty to generate action items.</div>
          </div>
        )}
        {todos.map(todo => (
          <div key={todo.id} className={`card-sm flex items-start gap-3 transition-opacity ${todo.status === 'done' ? 'opacity-50' : ''}`}>
            {/* Check button */}
            <button
              onClick={() => updateTodo(todo.id, { status: todo.status === 'done' ? 'pending' : 'done' })}
              className={`w-5 h-5 rounded border flex-shrink-0 mt-0.5 flex items-center justify-center transition-colors ${todo.status === 'done' ? 'bg-success border-success text-white' : 'border-surface-border hover:border-success'}`}>
              {todo.status === 'done' && '✓'}
            </button>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className={`text-sm font-medium ${todo.status === 'done' ? 'line-through text-gray-500' : 'text-white'}`}>{todo.title}</div>
              {todo.description && <div className="text-xs text-gray-500 mt-0.5">{todo.description}</div>}
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <span className={`text-xs font-medium ${PRIORITY_COLORS[todo.priority] || ''}`}>● {todo.priority}</span>
                <span className="text-xs text-gray-600">{ICONS[todo.project_slug] || '📁'} {todo.project_slug}</span>
                {todo.due_date && <span className={`text-xs ${new Date(todo.due_date) < new Date() ? 'text-red-400' : 'text-gray-600'}`}>📅 {todo.due_date}</span>}
                {todo.source_agent && <span className="text-xs text-gray-600">from {todo.source_agent}</span>}
              </div>
            </div>

            {/* Delete */}
            <button onClick={() => deleteTodo(todo.id)} className="text-gray-600 hover:text-red-400 transition-colors text-sm flex-shrink-0">✕</button>
          </div>
        ))}
      </div>
    </div>
  )
}
