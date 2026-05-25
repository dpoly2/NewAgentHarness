/**
 * AgentMajesty — Chief of Staff
 * Handles streaming chat, memory, briefings, and task routing
 */
const { getDb, generateId } = require('../db/database')
const { callLLM, streamLLM, getConfig } = require('./llm')
const { enqueueTask, createTodo, createNotification } = require('./engine')
const { loadRoster } = require('../roster/parser')

const AGENTMAJESTY_ID = 'agentmajesty'

function buildSystemPrompt(profile = {}, roster = null) {
  const db = getDb()
  const pendingTodos = db.prepare(`SELECT * FROM todos WHERE status NOT IN ('done','cancelled') ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END LIMIT 10`).all()
  const runningTasks = db.prepare(`SELECT * FROM agent_tasks WHERE status IN ('running','queued') LIMIT 10`).all()
  const openNotifs = db.prepare(`SELECT * FROM notifications WHERE read=0 ORDER BY created_at DESC LIMIT 5`).all()

  let agentList = '- No agents loaded yet'
  if (roster?.projects?.length) {
    const lines = []
    for (const proj of roster.projects) {
      lines.push(`  [${proj.name}] Lead: ${proj.leadAgent}`)
      for (const s of (proj.specialists || []).slice(0, 3)) {
        lines.push(`    - ${s.name}: ${s.role}`)
      }
    }
    for (const s of (roster.sharedAgents || [])) {
      lines.push(`  [Shared] ${s.agentName}: ${s.specialty}`)
    }
    agentList = lines.join('\n')
  }

  const todoList = pendingTodos.length
    ? pendingTodos.map(t => `- [${t.priority}] ${t.title}${t.due_date ? ` (due ${t.due_date})` : ''} — ${t.project_slug}`).join('\n')
    : '- No pending todos'

  const taskStatus = runningTasks.length
    ? runningTasks.map(t => `- ${t.status}: ${t.agent_id} — "${t.title}"`).join('\n')
    : '- No active tasks'

  // Load memory
  const memory = db.prepare(`SELECT key, value FROM agent_memory WHERE agent_id='agentmajesty' ORDER BY updated_at DESC LIMIT 20`).all()
  const memoryLines = memory.map(m => `  - ${m.key}: ${m.value}`).join('\n')

  return `You are AgentMajesty, the AI Chief of Staff for ${profile.name || 'the operator'} (${profile.role || 'Founder & Director'}).

Personality: Confident, warm, and strategically sharp. You think like a trusted advisor — direct, never verbose, always useful. You are the hub that connects all 12 project teams and helps the operator stay on top of everything.

Your operator runs multiple businesses and initiatives simultaneously. You proactively surface what matters most and route work to specialized agents.

${roster?.projects?.length ? `PORTFOLIO — ${roster.projects.length} active projects:
${agentList}` : ''}

CURRENT STATUS:
Running/Queued Tasks:
${taskStatus}

Pending Todos (top 10):
${todoList}
${memoryLines ? `\nMemory:\n${memoryLines}` : ''}
${profile.priorities ? `\nOperator priorities: ${profile.priorities}` : ''}
${profile.communicationStyle ? `Communication style: ${profile.communicationStyle}` : 'Communication style: concise and direct'}

INSTRUCTIONS:
- Be conversational and concise. Lead with the most important thing.
- When operator asks you to do work requiring agent execution, append a TASK block at the END:
  [TASK:{"title":"Brief title","description":"Full task description","agentId":"agent-name","projectSlug":"slug"}]
- When you identify concrete action items, append TODO block(s) at the END:
  [TODO:{"title":"Short action","description":"Detail","priority":"high","dueDate":"YYYY-MM-DD","projectSlug":"slug","tags":["tag"]}]
- Priority: low | medium | high | urgent. dueDate and tags are optional.
- You can create multiple [TODO:] or [TASK:] blocks.
- NEVER put these markers mid-response. Only at the very end.
- Only create [TASK:] when operator explicitly requests agent execution.
- Proactively mention open items and approaching deadlines you notice.`
}

async function chat({ conversationId, userMessage, projectSlug = null, profile = {}, onChunk = null }) {
  const db = getDb()
  const roster = loadRoster()

  // Get or create conversation
  let conv = db.prepare('SELECT * FROM conversations WHERE id=?').get(conversationId)
  if (!conv) {
    db.prepare('INSERT INTO conversations (id, slug, title) VALUES (?,?,?)').run(
      conversationId, projectSlug || 'global', userMessage.slice(0, 60)
    )
    conv = db.prepare('SELECT * FROM conversations WHERE id=?').get(conversationId)
  }

  // Store user message
  const userMsgId = generateId()
  db.prepare('INSERT INTO messages (id, conversation_id, role, content) VALUES (?,?,?,?)').run(
    userMsgId, conversationId, 'user', userMessage
  )

  // Build context from recent messages
  const history = db.prepare(`SELECT role, content FROM messages WHERE conversation_id=? ORDER BY created_at ASC`).all(conversationId)
  const contextMessages = [
    { role: 'system', content: buildSystemPrompt(profile, roster) },
    ...history.slice(-20).map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }))
  ]
  // replace last user message (already added above)
  if (contextMessages[contextMessages.length - 1]?.role === 'user') {
    contextMessages[contextMessages.length - 1].content = userMessage
  } else {
    contextMessages.push({ role: 'user', content: userMessage })
  }

  let fullResponse = ''

  if (onChunk) {
    try {
      for await (const chunk of streamLLM(contextMessages, { maxTokens: 2000 })) {
        fullResponse += chunk
        onChunk(chunk)
      }
    } catch (e) {
      fullResponse = `I encountered an error: ${e.message}. Please check your AI configuration in Settings.`
      onChunk(fullResponse)
    }
  } else {
    try {
      fullResponse = await callLLM(contextMessages, { maxTokens: 2000 })
    } catch (e) {
      fullResponse = `I encountered an error: ${e.message}. Please check your AI configuration in Settings.`
    }
  }

  // Parse markers BEFORE storing
  const { cleanText, tasks, todos } = parseMajestyOutput(fullResponse, projectSlug)

  // Store assistant message (clean, without markers)
  const assistantMsgId = generateId()
  db.prepare('INSERT INTO messages (id, conversation_id, role, content, agent_id) VALUES (?,?,?,?,?)').run(
    assistantMsgId, conversationId, 'assistant', cleanText, AGENTMAJESTY_ID
  )

  // Update conversation timestamp
  db.prepare(`UPDATE conversations SET updated_at=datetime('now') WHERE id=?`).run(conversationId)

  // Execute tasks
  for (const task of tasks) {
    await enqueueTask({ ...task, spawnedBy: assistantMsgId })
  }

  // Create todos
  for (const todo of todos) {
    createTodo({ ...todo, source: 'agent', sourceAgent: AGENTMAJESTY_ID })
  }

  return { messageId: assistantMsgId, response: cleanText, tasks, todos }
}

function parseMajestyOutput(text, defaultSlug = 'global') {
  const tasks = []
  const todos = []

  const taskRe = /\[TASK:\{([\s\S]*?)\}\]/g
  let m
  while ((m = taskRe.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(`{${m[1]}}`)
      if (parsed.title) tasks.push({ title: parsed.title, description: parsed.description || parsed.title, agentId: parsed.agentId || parsed.agentHint || 'agentmajesty', projectSlug: parsed.projectSlug || defaultSlug || 'global' })
    } catch (e) { /* skip */ }
  }

  const todoRe = /\[TODO:\{([\s\S]*?)\}\]/g
  while ((m = todoRe.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(`{${m[1]}}`)
      if (parsed.title) todos.push({ title: parsed.title, description: parsed.description || '', priority: parsed.priority || 'medium', dueDate: parsed.dueDate, projectSlug: parsed.projectSlug || defaultSlug || 'global', tags: parsed.tags || [] })
    } catch (e) { /* skip */ }
  }

  const cleanText = text.replace(/\[TASK:\{[\s\S]*?\}\]/g, '').replace(/\[TODO:\{[\s\S]*?\}\]/g, '').trim()
  return { cleanText, tasks, todos }
}

async function generateMorningBrief(profile = {}) {
  const db = getDb()
  const roster = loadRoster()

  const urgentTodos = db.prepare(`SELECT * FROM todos WHERE priority IN ('urgent','high') AND status NOT IN ('done','cancelled') ORDER BY priority, due_date LIMIT 15`).all()
  const runningTasks = db.prepare(`SELECT * FROM agent_tasks WHERE status IN ('running','queued')`).all()
  const completedYesterday = db.prepare(`SELECT * FROM agent_tasks WHERE status='completed' AND date(updated_at) >= date('now','-1 day')`).all()
  const recentTodos = db.prepare(`SELECT * FROM todos WHERE date(created_at) >= date('now','-1 day') ORDER BY created_at DESC LIMIT 10`).all()
  const openItems = roster?.openItems || []

  const urgentForPrompt = urgentTodos.map(t => `- [${t.priority}] ${t.title} (${t.project_slug})`).join('\n') || '- None'
  const openItemsStr = openItems.slice(0, 8).map(o => `- ${o.priority} ${o.item} — ${o.project} (${o.deadline})`).join('\n') || '- None'
  const tasksStr = runningTasks.map(t => `- ${t.agent_id}: ${t.title}`).join('\n') || '- None running'
  const doneStr = completedYesterday.map(t => `- ${t.agent_id}: ${t.title}`).join('\n') || '- None'

  const briefPrompt = `Generate a concise morning briefing for ${profile.name || 'David'}.
Format as markdown. Be direct and specific. Structure:
1. One sentence executive summary of the day
2. What needs David's immediate attention (max 3 items)
3. What agents are working on
4. Key items this week

Data:
HIGH PRIORITY TODOS:
${urgentForPrompt}

OPEN ITEMS FROM ROSTER:
${openItemsStr}

ACTIVE TASKS:
${tasksStr}

COMPLETED YESTERDAY:
${doneStr}`

  let content = ''
  try {
    content = await callLLM([
      { role: 'system', content: buildSystemPrompt(profile, roster) },
      { role: 'user', content: briefPrompt }
    ], { maxTokens: 1000 })
  } catch (e) {
    content = `# Morning Briefing — ${new Date().toLocaleDateString()}\n\n*AI not configured. Check Settings → AI Provider.*\n\n**Open Items (from roster):**\n${openItemsStr}`
  }

  const id = generateId()
  db.prepare('INSERT INTO daily_briefs (id, content) VALUES (?,?)').run(id, content)
  createNotification('Morning briefing is ready', 'briefing', null, 'high')
  return { id, content }
}

function saveMemory(key, value) {
  const db = getDb()
  db.prepare(`INSERT INTO agent_memory (id, agent_id, key, value) VALUES (?,?,?,?)
    ON CONFLICT(agent_id, key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')`)
    .run(generateId(), AGENTMAJESTY_ID, key, typeof value === 'string' ? value : JSON.stringify(value))
}

function getConversations() {
  const db = getDb()
  return db.prepare('SELECT * FROM conversations ORDER BY updated_at DESC').all()
}

function getMessages(conversationId) {
  const db = getDb()
  return db.prepare('SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at ASC').all(conversationId)
}

function deleteConversation(conversationId) {
  const db = getDb()
  db.prepare('DELETE FROM messages WHERE conversation_id=?').run(conversationId)
  db.prepare('DELETE FROM conversations WHERE id=?').run(conversationId)
}

module.exports = { chat, generateMorningBrief, saveMemory, getConversations, getMessages, deleteConversation, buildSystemPrompt }
