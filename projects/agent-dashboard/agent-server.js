const http = require('http')
const fs = require('fs')
const os = require('os')
const path = require('path')

// Optional production deps: better-sqlite3 and winston
let Database = null
let logger = console
try {
  // lazy require to keep dev env simple
  Database = require('better-sqlite3')
} catch (e) {
  // ok if not installed; will fallback to file storage
}
let winston = null
let DailyRotateFile = null
try {
  winston = require('winston')
  DailyRotateFile = require('winston-daily-rotate-file')
} catch (e) {
  // no-op
}

const DATA_DIR = path.join(__dirname, 'data')
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true })

const agentsFile = path.join(DATA_DIR, 'agents.json')
const tasksFile = path.join(DATA_DIR, 'tasks.json')
const profileFile = path.join(DATA_DIR, 'profile.json')
const contactsFile = path.join(DATA_DIR, 'contacts.json')
const mobileBridgeFile = path.join(DATA_DIR, 'mobile_bridge.json')
let agents = []
let tasks = []
let profile = {}
let contacts = []
let mobileBridge = {}

// Logging setup (env-driven)
const LOG_DIR = process.env.LOG_DIR || path.join(__dirname, 'logs')
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true })
if (winston && DailyRotateFile) {
  logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.printf(({ timestamp, level, message }) => `${timestamp} ${level}: ${message}`)
    ),
    transports: [
      new winston.transports.Console(),
      new DailyRotateFile({ dirname: LOG_DIR, filename: 'agent-dashboard-%DATE%.log', datePattern: 'YYYY-MM-DD', maxFiles: '14d' })
    ]
  })
} else {
  logger = console
}

// SQLite persistence (optional)
const USE_SQLITE = String(process.env.USE_SQLITE || '').toLowerCase() === 'true'
let db = null
function initDb() {
  if (!USE_SQLITE || !Database) return false
  const dbPath = path.join(DATA_DIR, 'agents.db')
  try {
    db = new Database(dbPath)
    db.pragma('journal_mode = WAL')
    db.exec(`CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS profile (k TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS contacts (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS mobile_bridge (k TEXT PRIMARY KEY, data TEXT);`)

    // load existing rows
    const arows = db.prepare('SELECT data FROM agents').all()
    agents = arows.map(r => JSON.parse(r.data))
    const trows = db.prepare('SELECT data FROM tasks').all()
    tasks = trows.map(r => JSON.parse(r.data))
    const prow = db.prepare('SELECT data FROM profile WHERE k = ?').get('profile')
    profile = prow ? JSON.parse(prow.data) : {}
    const crows = db.prepare('SELECT data FROM contacts').all()
    contacts = crows.map(r => JSON.parse(r.data))
    const mrow = db.prepare('SELECT data FROM mobile_bridge WHERE k = ?').get('mobile_bridge')
    mobileBridge = mrow ? JSON.parse(mrow.data) : {}
    logger.info('SQLite persistence initialized at ' + dbPath)
    return true
  } catch (e) {
    logger.error('Failed to initialize SQLite persistence: ' + (e && e.message))
    db = null
    return false
  }
}

initDb()
function defaultMobileBridge() {
  return {
    enabled: true,
    channel: 'iPhone Shortcuts',
    trustedSender: '',
    messages: []
  }
}
function defaultProfile() {
  return {
    name: 'David',
    role: 'Director of Communications',
    priorities: 'Regional communications, The Sigma Signal, grants, real estate projects, and agent coordination',
    communicationStyle: 'Concise, direct, action-oriented',
    briefingCadence: 'Daily morning brief and task follow-up',
    approvalRules: 'Ask before sending email, deleting files, publishing, committing, pushing, or spending money',
    memory: []
  }
}
try {
  let raw = fs.readFileSync(agentsFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  agents = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load agents.json, starting with empty list', e)
  agents = []
}
try {
  if (!fs.existsSync(tasksFile)) fs.writeFileSync(tasksFile, '[]', 'utf8')
  let raw = fs.readFileSync(tasksFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  tasks = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load tasks.json, starting with empty list', e)
  tasks = []
}
try {
  if (!fs.existsSync(profileFile)) fs.writeFileSync(profileFile, JSON.stringify(defaultProfile(), null, 2), 'utf8')
  let raw = fs.readFileSync(profileFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  profile = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load profile.json, starting with default profile', e)
  profile = defaultProfile()
}
try {
  if (!fs.existsSync(contactsFile)) fs.writeFileSync(contactsFile, '[]', 'utf8')
  let raw = fs.readFileSync(contactsFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  contacts = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load contacts.json, starting with empty list', e)
  contacts = []
}
try {
  if (!fs.existsSync(mobileBridgeFile)) fs.writeFileSync(mobileBridgeFile, JSON.stringify(defaultMobileBridge(), null, 2), 'utf8')
  let raw = fs.readFileSync(mobileBridgeFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  mobileBridge = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load mobile_bridge.json, starting with default config', e)
  mobileBridge = defaultMobileBridge()
}

const clients = []
function sendEvent(data){
  const payload = `data: ${JSON.stringify(data)}\n\n`
  clients.forEach(res => res.write(payload))
}
function persist(){
  // Persist to SQLite if available and enabled
  if (db) {
    try {
      const delAgents = db.prepare('DELETE FROM agents')
      const delTasks = db.prepare('DELETE FROM tasks')
      const delContacts = db.prepare('DELETE FROM contacts')
      delAgents.run()
      delTasks.run()
      delContacts.run()
      const insertAgent = db.prepare('INSERT INTO agents (id, data) VALUES (?, ?)')
      const insertTask = db.prepare('INSERT INTO tasks (id, data) VALUES (?, ?)')
      const insertContact = db.prepare('INSERT INTO contacts (id, data) VALUES (?, ?)')
      const insertProfile = db.prepare('INSERT OR REPLACE INTO profile (k, data) VALUES (?, ?)')
      const insertMobile = db.prepare('INSERT OR REPLACE INTO mobile_bridge (k, data) VALUES (?, ?)')
      const tran = db.transaction(() => {
        for (const a of agents) insertAgent.run(a.id, JSON.stringify(a))
        for (const t of tasks) insertTask.run(t.id, JSON.stringify(t))
        for (const c of contacts) insertContact.run(c.id, JSON.stringify(c))
        insertProfile.run('profile', JSON.stringify(profile))
        insertMobile.run('mobile_bridge', JSON.stringify(mobileBridge))
      })
      tran()
      return
    } catch (e) {
      logger.error('Failed to persist to SQLite: ' + (e && e.message))
      // fallthrough to file-based persist
    }
  }

  try { fs.writeFileSync(agentsFile, JSON.stringify(agents, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist agents: ' + e) }
  try { fs.writeFileSync(tasksFile, JSON.stringify(tasks, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist tasks: ' + e) }
  try { fs.writeFileSync(profileFile, JSON.stringify(profile, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist profile: ' + e) }
  try { fs.writeFileSync(contactsFile, JSON.stringify(contacts, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist contacts: ' + e) }
  try { fs.writeFileSync(mobileBridgeFile, JSON.stringify(mobileBridge, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist mobile bridge: ' + e) }
}
function slugifyAgentName(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
function createAgentRecord(input) {
  const name = String(input.name || '').trim()
  if (!name) throw new Error('Agent name is required')
  const existing = agents.find(a => a.name.toLowerCase() === name.toLowerCase())
  if (existing) return existing
  const idBase = slugifyAgentName(name) || `agent-${agents.length + 1}`
  let id = idBase
  let suffix = 2
  while (agents.some(a => a.id === id)) {
    id = `${idBase}-${suffix}`
    suffix += 1
  }
  const agent = {
    id,
    name,
    status: 'idle',
    progress: 0,
    role: String(input.role || 'Specialized agent').trim(),
    logs: [`${new Date().toISOString()} - Agent added manually.`]
  }
  agents.push(agent)
  return agent
}
function createContactRecord(input) {
  const name = String(input.name || '').trim()
  const email = String(input.email || '').trim()
  if (!name || !email) throw new Error('Contact name and email are required')
  const existing = contacts.find(c => c.email.toLowerCase() === email.toLowerCase())
  if (existing) {
    Object.assign(existing, {
      name,
      group: String(input.group || existing.group || '').trim(),
      notes: String(input.notes || existing.notes || '').trim(),
      updatedAt: new Date().toISOString()
    })
    return existing
  }
  const now = new Date().toISOString()
  const contact = {
    id: `contact-${Date.now()}`,
    name,
    email,
    group: String(input.group || '').trim(),
    notes: String(input.notes || '').trim(),
    createdAt: now,
    updatedAt: now
  }
  contacts.push(contact)
  return contact
}
function getLanAddress() {
  const interfaces = os.networkInterfaces()
  for (const addresses of Object.values(interfaces)) {
    for (const address of addresses || []) {
      if (address.family === 'IPv4' && !address.internal) return address.address
    }
  }
  return '127.0.0.1'
}
function getMobileBridgeInfo() {
  const port = process.env.AGENT_SERVER_PORT || 4000
  const host = getLanAddress()
  return {
    localEndpoint: `http://127.0.0.1:${port}/mobile-message`,
    lanEndpoint: `http://${host}:${port}/mobile-message`,
    shortcutBody: JSON.stringify({ from: 'iPhone', text: 'Task for AgentMajesty' }, null, 2)
  }
}
function receiveMobileMessage(input) {
  const text = String(input.text || input.message || '').trim()
  if (!text) throw new Error('Message text is required')
  const from = String(input.from || 'iPhone').trim()
  const now = new Date().toISOString()
  const routed = routeTask(text)
  const task = createTaskRecord(text, routed)
  task.source = 'mobile'
  task.mobileFrom = from
  task.logs = (task.logs || []).concat([`${now} - Received from ${from} through ${mobileBridge.channel || 'mobile bridge'}.`])
  tasks.unshift(task)
  // start the task on the routed agent for live processing
  if (routed) {
    try { startTaskOnAgent(task, routed) } catch (e) { console.error('Failed to start mobile task on agent:', e) }
    routed.logs = (routed.logs || []).concat([`${now} - Mobile message routed as ${task.id}: ${text}`])
  }
  mobileBridge.messages = [{
    id: `mobile-${Date.now()}`,
    from,
    text,
    taskId: task.id,
    receivedAt: now
  }].concat(Array.isArray(mobileBridge.messages) ? mobileBridge.messages : []).slice(0, 50)
  return task
}
function routeTask(message) {
  const text = String(message || '').toLowerCase()
  const candidates = agents.filter(a => a.name !== 'AgentMajesty')
  const agentText = a => `${a.name || ''} ${a.role || ''}`
  const rules = [
    { terms: ['wordpress', 'plugin', 'website'], match: a => /wordpress|plugin|website/i.test(agentText(a)) },
    { terms: ['grant', 'funding', 'proposal'], match: a => /grant|research|funding|proposal/i.test(agentText(a)) },
    { terms: ['constant contact', 'newsletter', 'sigma signal', 'campaign', 'email'], match: a => /sigmasignal|constant|communication|email|newsletter|campaign/i.test(agentText(a)) },
    { terms: ['real estate', 'parcel', 'property'], match: a => /realestate|real estate|property|parcel/i.test(agentText(a)) },
    { terms: ['capital', 'fundraising', 'investor'], match: a => /capital|fundraising|investor/i.test(agentText(a)) },
    { terms: ['government', 'relations', 'permit'], match: a => /government|relations|permit/i.test(agentText(a)) },
    { terms: ['project', 'manage', 'timeline'], match: a => /projectmanager|project manager|manager|timeline/i.test(agentText(a)) }
  ]
  for (const rule of rules) {
    if (rule.terms.some(term => text.includes(term))) {
      const agent = candidates.find(rule.match)
      if (agent) return agent
    }
  }
  return candidates.find(a => a.status === 'idle') || candidates[0] || agents[0]
}
function createTaskRecord(message, routed) {
  const now = new Date().toISOString()
  const title = String(message || '').trim().slice(0, 80) || 'Untitled task'
  const task = {
    id: `task-${Date.now()}`,
    title,
    description: String(message || '').trim(),
    assignedAgentId: routed ? routed.id : null,
    assignedAgentName: routed ? routed.name : null,
    status: routed ? 'queued' : 'needs-agent',
    createdAt: now,
    updatedAt: now,
    logs: [
      `${now} - Created by AgentMajesty.`,
      routed ? `${now} - Assigned to ${routed.name}.` : `${now} - No matching specialized agent found.`
    ],
    result: null
  }
  // If routed to an agent, start the agent so offline mode processes the task
  if (routed) {
    if (!routed.progress || routed.progress >= 100) routed.progress = 0
    routed.status = 'running'
    routed.logs = (routed.logs || []).concat([`${now} - Assigned task ${task.id}: ${task.title}`])
  }
  return task
}
function executeTaskRecord(taskId) {
  const task = tasks.find(t => t.id === taskId)
  if (!task) throw new Error('Task not found')
  const agent = agents.find(a => a.id === task.assignedAgentId)
  const now = new Date().toISOString()
  if (!agent) {
    task.status = 'needs-agent'
    task.updatedAt = now
    task.logs = (task.logs || []).concat([`${now} - Execution blocked: assigned agent is missing.`])
    return task
  }
  task.status = 'completed'
  task.updatedAt = now
  task.logs = (task.logs || []).concat([
    `${now} - Execution started by ${agent.name}.`,
    `${now} - ${agent.name} acknowledged the task.`,
    `${now} - Execution completed.`
  ])
  task.result = `${agent.name} completed the routed task.`
  agent.status = 'idle'
  agent.progress = 100
  agent.logs = (agent.logs || []).concat([
    `${now} - Executed task ${task.id}: ${task.title}`,
    `${now} - completed`
  ])
  return task
}

// Task worker helpers for deterministic offline/production execution
const runningTasks = {}

function estimateTaskDurationSeconds(message) {
  const len = String(message || '').length
  return Math.min(120, Math.max(5, Math.floor(len / 20) + 5))
}

function startTaskOnAgent(task, agent) {
  const now = new Date().toISOString()
  agent.status = 'running'
  agent.progress = 0
  agent.logs = (agent.logs || []).concat([`${now} - started task ${task.id}`])
  task.status = 'running'
  task.updatedAt = now
  task.logs = (task.logs || []).concat([`${now} - Execution started by ${agent.name}.`])
  const total = estimateTaskDurationSeconds(task.description || task.title)
  runningTasks[agent.id] = { taskId: task.id, remaining: total, total }
}

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/agents'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(agents))
  }

  if (req.method === 'GET' && req.url === '/tasks'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(tasks))
  }

  if (req.method === 'GET' && req.url === '/profile'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(profile))
  }

  if (req.method === 'GET' && req.url === '/contacts'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(contacts))
  }

  if (req.method === 'GET' && req.url === '/mobile-bridge'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify({ config: mobileBridge, info: getMobileBridgeInfo() }))
  }

  if (req.method === 'GET' && req.url === '/events'){
    // SSE endpoint
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    })
    res.write('\n')
    clients.push(res)
    req.on('close', () => {
      const idx = clients.indexOf(res)
      if (idx !== -1) clients.splice(idx,1)
    })
    return
  }

  if (req.method === 'POST' && req.url === '/agent-command'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const { id, action } = JSON.parse(body)
        const idx = agents.findIndex(a => a.id === id)
        if (idx === -1) {
          res.writeHead(404, {'Content-Type':'application/json'})
          return res.end(JSON.stringify({ error: 'agent not found' }))
        }
        const agent = agents[idx]
        const ts = new Date().toISOString()
        if (action === 'start'){
          agent.status = 'running'
          if (!agent.progress || agent.progress >= 100) agent.progress = 0
          agent.logs = (agent.logs || []).concat([`${ts} - started`])
        } else if (action === 'stop'){
          agent.status = 'idle'
          agent.logs = (agent.logs || []).concat([`${ts} - stopped`])
        } else if (action === 'ping'){
          agent.logs = (agent.logs || []).concat([`${ts} - ping`])
        }
        agents[idx] = agent
        persist()
        // notify SSE clients
        sendEvent({ agents, tasks })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(agents))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url === '/agents'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        createAgentRecord(JSON.parse(body))
        persist()
        sendEvent({ agents, tasks })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(agents))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'PUT' && req.url === '/profile'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        profile = { ...profile, ...JSON.parse(body), updatedAt: new Date().toISOString() }
        persist()
        sendEvent({ profile, contacts })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(profile))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url === '/contacts'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        createContactRecord(JSON.parse(body))
        persist()
        sendEvent({ profile, contacts })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(contacts))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'PUT' && req.url === '/mobile-bridge'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        mobileBridge = { ...mobileBridge, ...JSON.parse(body), updatedAt: new Date().toISOString() }
        persist()
        sendEvent({ mobileBridge })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ config: mobileBridge, info: getMobileBridgeInfo() }))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url === '/mobile-message'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const task = receiveMobileMessage(JSON.parse(body || '{}'))
        persist()
        sendEvent({ agents, tasks, mobileBridge })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ ok: true, taskId: task.id, assignedAgentName: task.assignedAgentName }))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url === '/agent-chat'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const { message } = JSON.parse(body)
        const routed = routeTask(message)
        const task = createTaskRecord(message, routed)
        tasks.unshift(task)
        // start the task on the routed agent so offline/production mode processes it
        if (routed) {
          try { startTaskOnAgent(task, routed) } catch (e) { console.error('Failed to start task on agent:', e) }
          routed.logs = (routed.logs || []).concat([`${new Date().toISOString()} - AgentMajesty routed task ${task.id}: ${message}`])
        }
        persist()
        sendEvent({ agents, tasks })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({
          agents,
          tasks,
          task,
          reply: routed
            ? `AgentMajesty created ${task.id} and assigned it to ${routed.name}.`
            : 'AgentMajesty could not find a specialized agent yet. Add one from the sidebar.'
        }))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url.startsWith('/tasks/') && req.url.endsWith('/execute')){
    try {
      const id = decodeURIComponent(req.url.slice('/tasks/'.length, -'/execute'.length))
      const task = executeTaskRecord(id)
      persist()
      sendEvent({ agents, tasks })
      res.writeHead(200, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ agents, tasks, task }))
    } catch (e){
      res.writeHead(404, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ error: e.message || 'task not found' }))
    }
    return
  }

  // fallback
  res.writeHead(404, {'Content-Type':'text/plain'})
  res.end('Not found')
})

const PORT = process.env.AGENT_SERVER_PORT || 4000
const HOST = process.env.AGENT_SERVER_HOST || '0.0.0.0'
server.listen(PORT, HOST, () => {
  console.log(`Agent runtime listening on http://${HOST}:${PORT}`)
})

// Deterministic task worker for processing running tasks in production-like mode
setInterval(() => {
  let changed = false
  for (const [agentId, info] of Object.entries(runningTasks)) {
    const agent = agents.find(a => a.id === agentId)
    const task = tasks.find(t => t.id === info.taskId)
    if (!agent || !task) {
      delete runningTasks[agentId]
      continue
    }
    info.remaining = Math.max(0, info.remaining - 1)
    const progress = Math.min(100, Math.round(100 * (1 - info.remaining / info.total)))
    agent.progress = progress
    agent.logs = (agent.logs || []).concat([`${new Date().toISOString()} - progress ${agent.progress}%`])
    task.logs = (task.logs || []).concat([`${new Date().toISOString()} - progress ${agent.progress}%`])
    changed = true
    if (info.remaining <= 0) {
      try {
        executeTaskRecord(task.id)
      } catch (e) {
        console.error('Failed to execute task:', e)
        agent.status = 'idle'
      }
      delete runningTasks[agentId]
    }
  }
  if (changed) { persist(); sendEvent({ agents, tasks }) }
}, 1000)
