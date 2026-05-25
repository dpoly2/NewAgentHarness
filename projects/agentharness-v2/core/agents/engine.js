/**
 * Agent Execution Engine
 * Manages the task queue and executes agents via LLM
 */
const { getDb, generateId } = require('../db/database')
const { loadAgentProfile } = require('../roster/parser')
const { callLLM, streamLLM } = require('./llm')

let io = null  // socket.io instance, set by server

function setIO(socketIO) { io = socketIO }

function emit(event, data) {
  if (io) io.emit(event, data)
}

// In-memory queue tracking for running tasks
const runningTasks = new Map()

async function enqueueTask({ title, description, agentId, projectSlug = 'global', spawnedBy = null }) {
  const db = getDb()
  const id = generateId()
  db.prepare(`
    INSERT INTO agent_tasks (id, title, description, agent_id, project_slug, status, spawned_by)
    VALUES (?, ?, ?, ?, ?, 'queued', ?)
  `).run(id, title, description || title, agentId, projectSlug, spawnedBy)

  const task = db.prepare('SELECT * FROM agent_tasks WHERE id = ?').get(id)
  emit('task:queued', task)
  createNotification(`Task queued: ${title}`, 'task', projectSlug, 'low')

  // Execute async
  executeTask(id).catch(e => console.error('[engine] task execution error:', e))
  return task
}

async function executeTask(taskId) {
  const db = getDb()
  const task = db.prepare('SELECT * FROM agent_tasks WHERE id = ?').get(taskId)
  if (!task) return

  db.prepare(`UPDATE agent_tasks SET status='running', updated_at=datetime('now') WHERE id=?`).run(taskId)
  emit('task:started', { ...task, status: 'running' })

  const start = Date.now()
  try {
    const agentProfile = loadAgentProfile(task.agent_id)
    const systemPrompt = agentProfile
      ? `${agentProfile}\n\nYou are executing a task. Be thorough, specific, and actionable. Return results in clear markdown.`
      : `You are ${task.agent_id}, a specialized AI agent. Complete the assigned task thoroughly and return results in clear markdown.`

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: `## Task Assignment\n\n**Title:** ${task.title}\n\n**Description:**\n${task.description}` }
    ]

    const result = await callLLM(messages, { maxTokens: 2000 })
    const duration = Date.now() - start

    // Parse any todos or sub-tasks from the result
    const { cleanResult, todos: newTodos, subTasks } = parseAgentOutput(result, task)

    db.prepare(`
      UPDATE agent_tasks SET status='completed', result=?, tokens=?, duration_ms=?, updated_at=datetime('now') WHERE id=?
    `).run(cleanResult, result.tokens || 0, duration, taskId)

    const updated = db.prepare('SELECT * FROM agent_tasks WHERE id = ?').get(taskId)
    emit('task:completed', updated)
    createNotification(`${task.agent_id} completed: ${task.title}`, 'task', task.project_slug, 'medium')

    // Create any todos the agent found
    for (const todo of newTodos) {
      createTodo({ ...todo, source: 'agent', sourceAgent: task.agent_id, projectSlug: task.project_slug })
    }

    // Enqueue any sub-tasks
    for (const sub of subTasks) {
      enqueueTask({ ...sub, projectSlug: task.project_slug, spawnedBy: taskId })
    }

  } catch (e) {
    db.prepare(`
      UPDATE agent_tasks SET status='failed', result=?, updated_at=datetime('now') WHERE id=?
    `).run(`Error: ${e.message}`, taskId)
    const updated = db.prepare('SELECT * FROM agent_tasks WHERE id = ?').get(taskId)
    emit('task:failed', updated)
  }
}

function parseAgentOutput(text, task) {
  const todos = []
  const subTasks = []
  let cleanResult = text

  // Extract [TODO:{...}] markers
  const todoRe = /\[TODO:\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\]/g
  let m
  while ((m = todoRe.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(`{${m[1]}}`)
      if (parsed.title) todos.push(parsed)
    } catch (e) { /* ignore malformed */ }
  }

  // Extract [TASK:{...}] markers
  const taskRe = /\[TASK:\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\]/g
  while ((m = taskRe.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(`{${m[1]}}`)
      if (parsed.title && parsed.agentHint) {
        subTasks.push({ title: parsed.title, description: parsed.description || parsed.title, agentId: parsed.agentHint })
      }
    } catch (e) { /* ignore */ }
  }

  cleanResult = text.replace(/\[TODO:\{[^}]*\}\]/g, '').replace(/\[TASK:\{[^}]*\}\]/g, '').trim()
  return { cleanResult, todos, subTasks }
}

function createTodo({ title, description, priority = 'medium', dueDate, projectSlug = 'global', source = 'user', sourceAgent = null, tags = [] }) {
  const db = getDb()
  const id = generateId()
  db.prepare(`
    INSERT INTO todos (id, title, description, priority, project_slug, due_date, source, source_agent, tags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(id, title, description || '', priority, projectSlug, dueDate || null, source, sourceAgent, JSON.stringify(tags))
  const todo = db.prepare('SELECT * FROM todos WHERE id = ?').get(id)
  emit('todo:created', todo)
  return todo
}

function createNotification(message, type = 'info', projectSlug = null, priority = 'medium') {
  const db = getDb()
  const id = generateId()
  db.prepare(`INSERT INTO notifications (id, type, message, project_slug, priority) VALUES (?,?,?,?,?)`).run(id, type, message, projectSlug, priority)
  emit('notification:new', { id, type, message, project_slug: projectSlug, priority, read: 0 })
}

function getQueueStatus() {
  const db = getDb()
  return {
    running: db.prepare(`SELECT * FROM agent_tasks WHERE status='running' ORDER BY updated_at DESC`).all(),
    queued: db.prepare(`SELECT * FROM agent_tasks WHERE status='queued' ORDER BY created_at ASC`).all(),
    recent: db.prepare(`SELECT * FROM agent_tasks WHERE status IN ('completed','failed','cancelled') ORDER BY updated_at DESC LIMIT 20`).all()
  }
}

module.exports = { enqueueTask, createTodo, createNotification, getQueueStatus, setIO }
