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
const issuesFile = path.join(DATA_DIR, 'issues.json')
const connectorsFile = path.join(DATA_DIR, 'connectors.json')
const projectsFile = path.join(DATA_DIR, 'projects.json')
const aiConfigFile = path.join(DATA_DIR, 'ai_config.json')
const todosFile = path.join(DATA_DIR, 'todos.json')

const AI_PROVIDER_PRESETS = {
  ollama: { baseUrl: 'http://localhost:11434/v1', model: 'llama3.2' },
  openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  github: { baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini' }
}
let aiConfig = { provider: 'ollama', baseUrl: 'http://localhost:11434/v1', apiKey: '', model: 'llama3.2', enabled: false }
try {
  if (fs.existsSync(aiConfigFile)) {
    aiConfig = { ...aiConfig, ...JSON.parse(fs.readFileSync(aiConfigFile, 'utf8').replace(/^\uFEFF/, '')) }
  }
} catch (e) { /* use defaults */ }

const AGENTS_PROFILES_DIR = path.join(__dirname, '..', '..', 'agents')

let agents = []
let tasks = []
let todos = []
let profile = {}
let contacts = []
let mobileBridge = {}
let issues = []
let connectors = []
let projects = []

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
             CREATE TABLE IF NOT EXISTS todos (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS profile (k TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS contacts (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS mobile_bridge (k TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS issues (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS connectors (id TEXT PRIMARY KEY, data TEXT);
             CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data TEXT);`)

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
    const irows = db.prepare('SELECT data FROM issues').all()
    issues = irows.map(r => JSON.parse(r.data))
    const connRows = db.prepare('SELECT data FROM connectors').all()
    connectors = connRows.map(r => JSON.parse(r.data))
    const projectRows = db.prepare('SELECT data FROM projects').all()
    projects = projectRows.map(r => JSON.parse(r.data))
    const todoRows = db.prepare('SELECT data FROM todos').all()
    todos = todoRows.map(r => JSON.parse(r.data))
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
try {
  if (!fs.existsSync(issuesFile)) fs.writeFileSync(issuesFile, '[]', 'utf8')
  let raw = fs.readFileSync(issuesFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  issues = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load issues.json, starting with empty list', e)
  issues = []
}
try {
  if (!fs.existsSync(connectorsFile)) fs.writeFileSync(connectorsFile, '[]', 'utf8')
  let raw = fs.readFileSync(connectorsFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  connectors = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load connectors.json, starting with empty list', e)
  connectors = []
}
try {
  if (!fs.existsSync(projectsFile)) fs.writeFileSync(projectsFile, '[]', 'utf8')
  let raw = fs.readFileSync(projectsFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  projects = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load projects.json, starting with empty list', e)
  projects = []
}
try {
  if (!fs.existsSync(todosFile)) fs.writeFileSync(todosFile, '[]', 'utf8')
  let raw = fs.readFileSync(todosFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  todos = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load todos.json, starting with empty list', e)
  todos = []
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
      const delIssues = db.prepare('DELETE FROM issues')
      const delConnectors = db.prepare('DELETE FROM connectors')
      const delProjects = db.prepare('DELETE FROM projects')
      const delTodos = db.prepare('DELETE FROM todos')
      delAgents.run()
      delTasks.run()
      delContacts.run()
      delIssues.run()
      delConnectors.run()
      delProjects.run()
      delTodos.run()
      const insertAgent = db.prepare('INSERT INTO agents (id, data) VALUES (?, ?)')
      const insertTask = db.prepare('INSERT INTO tasks (id, data) VALUES (?, ?)')
      const insertContact = db.prepare('INSERT INTO contacts (id, data) VALUES (?, ?)')
      const insertIssue = db.prepare('INSERT INTO issues (id, data) VALUES (?, ?)')
      const insertConnector = db.prepare('INSERT INTO connectors (id, data) VALUES (?, ?)')
      const insertProject = db.prepare('INSERT INTO projects (id, data) VALUES (?, ?)')
      const insertTodo = db.prepare('INSERT INTO todos (id, data) VALUES (?, ?)')
      const insertProfile = db.prepare('INSERT OR REPLACE INTO profile (k, data) VALUES (?, ?)')
      const insertMobile = db.prepare('INSERT OR REPLACE INTO mobile_bridge (k, data) VALUES (?, ?)')
      const tran = db.transaction(() => {
        for (const a of agents) insertAgent.run(a.id, JSON.stringify(a))
        for (const t of tasks) insertTask.run(t.id, JSON.stringify(t))
        for (const c of contacts) insertContact.run(c.id, JSON.stringify(c))
        for (const i of issues) insertIssue.run(i.id, JSON.stringify(i))
        for (const c of connectors) insertConnector.run(c.id, JSON.stringify(c))
        for (const p of projects) insertProject.run(p.id, JSON.stringify(p))
        for (const td of todos) insertTodo.run(td.id, JSON.stringify(td))
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
  try { fs.writeFileSync(issuesFile, JSON.stringify(issues, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist issues: ' + e) }
  try { fs.writeFileSync(connectorsFile, JSON.stringify(connectors, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist connectors: ' + e) }
  try { fs.writeFileSync(projectsFile, JSON.stringify(projects, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist projects: ' + e) }
  try { fs.writeFileSync(todosFile, JSON.stringify(todos, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist todos: ' + e) }
}
function persistAiConfig() {
  try { fs.writeFileSync(aiConfigFile, JSON.stringify(aiConfig, null, 2), 'utf8') } catch(e) { logger.error('Failed to persist ai_config: ' + e) }
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
function maskSecret(value) {
  const text = String(value || '')
  if (!text) return ''
  if (text.startsWith('****')) return text
  if (text.length <= 4) return '****'
  return `****${text.slice(-4)}`
}
function createTodoRecord(input) {
  const title = String(input.title || '').trim()
  if (!title) throw new Error('Todo title is required')
  const now = new Date().toISOString()
  const todo = {
    id: `todo-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    title,
    description: String(input.description || '').trim(),
    status: ['pending', 'in_progress', 'done', 'blocked'].includes(input.status) ? input.status : 'pending',
    priority: ['low', 'medium', 'high', 'urgent'].includes(input.priority) ? input.priority : 'medium',
    dueDate: String(input.dueDate || '').trim(),
    tags: Array.isArray(input.tags) ? input.tags.map(t => String(t).trim()).filter(Boolean) : [],
    createdAt: now,
    updatedAt: now
  }
  todos.push(todo)
  return todo
}
function sanitizeConnectorForClient(connector) {
  const safe = { ...connector, config: { ...(connector.config || {}) } }
  for (const key of ['password', 'apiKey', 'apiSecret', 'clientSecret', 'accessToken', 'refreshToken']) {
    if (safe.config[key]) safe.config[key] = maskSecret(safe.config[key])
  }
  return safe
}
function validateConnectorInput(input) {
  const type = String(input.type || '').trim()
  const allowed = ['gmail', 'outlook', 'smtp', 'constant-contact']
  if (!allowed.includes(type)) throw new Error('Connector type is required')
  const name = String(input.name || '').trim()
  if (!name) throw new Error('Connector name is required')
  return { type, name }
}
function normalizeConnectorConfig(input) {
  const config = { ...(input.config || {}) }
  const type = input.type
  if (type === 'smtp') {
    config.host = String(config.host || '').trim()
    config.port = String(config.port || '').trim() || '587'
    config.username = String(config.username || '').trim()
    config.fromEmail = String(config.fromEmail || '').trim()
    config.secure = Boolean(config.secure)
  }
  if (type === 'gmail' || type === 'outlook') {
    config.email = String(config.email || '').trim()
    config.authMode = config.authMode || 'oauth'
    config.scopes = config.scopes || 'mail.read, mail.send'
    config.accessToken = String(config.accessToken || '').trim()
    config.refreshToken = String(config.refreshToken || '').trim()
    config.expiresAt = String(config.expiresAt || '').trim()
  }
  if (type === 'constant-contact') {
    config.accountName = String(config.accountName || '').trim()
    config.clientId = String(config.clientId || '').trim()
  }
  return config
}
function createConnectorRecord(input) {
  const { type, name } = validateConnectorInput(input)
  const now = new Date().toISOString()
  const connector = {
    id: `connector-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
    name,
    type,
    status: 'needs-configuration',
    config: normalizeConnectorConfig({ ...input, type }),
    lastTest: null,
    logs: [`${now} - Connector created.`],
    createdAt: now,
    updatedAt: now
  }
  connectors.unshift(connector)
  return connector
}
function updateConnectorRecord(id, input) {
  const connector = connectors.find(item => item.id === id)
  if (!connector) throw new Error('Connector not found')
  const now = new Date().toISOString()
  if (input.name !== undefined) connector.name = String(input.name || '').trim() || connector.name
  if (input.config) connector.config = { ...(connector.config || {}), ...normalizeConnectorConfig({ ...input, type: connector.type }) }
  connector.updatedAt = now
  connector.logs = (connector.logs || []).concat([`${now} - Connector updated.`])
  return connector
}
function testConnectorRecord(id) {
  const connector = connectors.find(item => item.id === id)
  if (!connector) throw new Error('Connector not found')
  const now = new Date().toISOString()
  const config = connector.config || {}
  let ok = true
  let message = 'Configuration is ready for a live adapter.'
  if (connector.type === 'smtp') {
    ok = Boolean(config.host && config.port && config.username && (config.password || String(config.password || '').startsWith('****')))
    message = ok ? 'SMTP settings are complete. Live send/receive adapter can use this connector.' : 'SMTP needs host, port, username, and password.'
  } else if (connector.type === 'gmail' || connector.type === 'outlook') {
    ok = Boolean(config.email && (config.refreshToken || config.accessToken))
    message = ok ? 'OAuth tokens are present. Live mail adapter can use this connector.' : 'Add the email plus an OAuth access token or refresh token.'
  } else if (connector.type === 'constant-contact') {
    ok = Boolean(config.accountName && config.clientId)
    message = ok ? 'Constant Contact profile is ready. Add API token exchange next.' : 'Constant Contact needs account name and client ID.'
  }
  connector.status = ok ? 'ready' : 'needs-configuration'
  connector.lastTest = { ok, message, testedAt: now }
  connector.updatedAt = now
  connector.logs = (connector.logs || []).concat([`${now} - Test ${ok ? 'passed' : 'needs configuration'}: ${message}`])
  return connector
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
  if (routed) {
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
  const appliedLearning = routed && Array.isArray(routed.learning)
    ? routed.learning.slice(0, 3).map(item => item.text || item.summary || String(item))
    : []
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
      routed ? `${now} - Assigned to ${routed.name}.` : `${now} - No matching specialized agent found.`,
      appliedLearning.length ? `${now} - Applied prior learning: ${appliedLearning[0]}` : `${now} - No prior agent learning found for this route.`
    ],
    result: null,
    responseData: null,
    issueIds: [],
    appliedLearning
  }
  // Keep the agent selected but wait for explicit Execute before running.
  if (routed) {
    if (!routed.progress || routed.progress >= 100) routed.progress = 0
    routed.logs = (routed.logs || []).concat([`${now} - Queued task ${task.id}: ${task.title}`])
  }
  return task
}
function createIssueRecord(input) {
  const now = new Date().toISOString()
  const issue = {
    id: `issue-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
    taskId: input.taskId || null,
    agentId: input.agentId || null,
    agentName: input.agentName || null,
    severity: input.severity || 'medium',
    status: input.status || 'open',
    title: input.title || 'Agent issue',
    detail: input.detail || '',
    source: input.source || 'runtime',
    createdAt: now,
    updatedAt: now,
    resolution: null
  }
  issues.unshift(issue)
  return issue
}
function openIssuesForAgent(agentId) {
  return issues.filter(issue => issue.agentId === agentId && issue.status !== 'resolved')
}
function reloadRuntimeData() {
  try {
    if (fs.existsSync(projectsFile)) projects = JSON.parse(fs.readFileSync(projectsFile, 'utf8').replace(/^\uFEFF/, ''))
  } catch (e) {
    logger.error('Failed to reload projects: ' + e)
  }
  try {
    if (fs.existsSync(connectorsFile)) connectors = JSON.parse(fs.readFileSync(connectorsFile, 'utf8').replace(/^\uFEFF/, ''))
  } catch (e) {
    logger.error('Failed to reload connectors: ' + e)
  }
}
function scoreProjectForTask(project, task) {
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const haystack = `${project.name || ''} ${project.path || ''} ${(project.docs || []).map(doc => `${doc.path} ${doc.text}`).join(' ')}`.toLowerCase()
  return text.split(/\W+/).filter(word => word.length > 3 && haystack.includes(word)).length
}
function getTaskProject(task) {
  if (task.projectId) return projects.find(project => project.id === task.projectId) || null
  return projects
    .map(project => ({ project, score: scoreProjectForTask(project, task) }))
    .sort((a, b) => b.score - a.score)[0]?.project || projects[0] || null
}
function runProjectFileAdapter(task) {
  const project = getTaskProject(task)
  if (!project) {
    return {
      name: 'project-file-adapter',
      status: 'skipped',
      summary: 'No imported project is available for file analysis.',
      data: { projectsImported: 0 },
      nextActions: ['Import a project folder from the Projects tab.']
    }
  }
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const files = Array.isArray(project.files) ? project.files : []
  const docs = Array.isArray(project.docs) ? project.docs : []
  const matches = files
    .filter(file => text.split(/\W+/).some(word => word.length > 4 && file.path.toLowerCase().includes(word)))
    .slice(0, 12)
  const todoDocs = docs
    .map(doc => ({
      path: doc.path,
      lines: String(doc.text || '').split(/\r?\n/).filter(line => /todo|fixme|next|task|issue|bug/i.test(line)).slice(0, 8)
    }))
    .filter(doc => doc.lines.length)
  const recentTimeline = (project.timeline || []).slice(0, 8)
  return {
    name: 'project-file-adapter',
    status: 'completed',
    summary: `Analyzed imported project ${project.name}.`,
    data: {
      projectId: project.id,
      projectName: project.name,
      projectPath: project.path,
      filesConsidered: files.length,
      docsConsidered: docs.length,
      matchingFiles: matches,
      todoDocs,
      recentTimeline
    },
    nextActions: [
      matches.length ? 'Review matching files before making edits.' : 'Import deeper docs or mention a specific file for targeted work.',
      todoDocs.length ? 'Convert detected TODO/issue lines into queue tasks.' : 'Ask AgentMajesty to create a project plan from imported docs.',
      'Require approval before writing files.'
    ]
  }
}
function runConnectorAdapter(task) {
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const wantsMail = /email|gmail|outlook|smtp|newsletter|campaign|constant contact/.test(text)
  if (!wantsMail) {
    return {
      name: 'connector-adapter',
      status: 'skipped',
      summary: 'Task does not require an external connector.',
      data: {},
      nextActions: []
    }
  }
  const relevant = connectors.filter(connector => {
    if (/constant contact|newsletter|campaign/.test(text)) return connector.type === 'constant-contact'
    if (/gmail/.test(text)) return connector.type === 'gmail'
    if (/outlook/.test(text)) return connector.type === 'outlook'
    if (/smtp/.test(text)) return connector.type === 'smtp'
    return ['gmail', 'outlook', 'smtp', 'constant-contact'].includes(connector.type)
  })
  const connectorReady = connector => {
    const config = connector.config || {}
    if (connector.type === 'gmail' || connector.type === 'outlook') return Boolean(config.email && (config.refreshToken || config.accessToken))
    if (connector.type === 'smtp') return Boolean(config.host && config.port && config.username && config.password)
    if (connector.type === 'constant-contact') return Boolean(config.accountName && config.clientId)
    return connector.status === 'ready'
  }
  const ready = relevant.filter(connectorReady)
  return {
    name: 'connector-adapter',
    status: ready.length ? 'ready' : 'needs-configuration',
    summary: ready.length
      ? `Found ${ready.length} ready connector(s) for this task.`
      : `Found ${relevant.length} connector profile(s), but none are ready yet.`,
    data: {
      matchedConnectors: relevant.map(sanitizeConnectorForClient),
      readyConnectorIds: ready.map(connector => connector.id),
      preparedAction: ready.length ? {
        type: /constant contact|newsletter|campaign/.test(text) ? 'campaign-draft' : 'email-draft',
        approvalRequired: true,
        reason: 'External sends are blocked until an approval adapter is added.'
      } : null
    },
    nextActions: ready.length
      ? ['Review the prepared action data.', 'Add an approval gate before allowing live sends.']
      : ['Open the Connectors tab and complete/test the needed connector.']
  }
}
function shouldRunPublicResearchAdapter(task, agent) {
  const text = `${task.title || ''} ${task.description || ''} ${agent.name || ''} ${agent.role || ''}`.toLowerCase()
  return /research|public|web|grant|funding|news|market|government|policy|property|real estate|source|find|look up|lookup/.test(text)
}
function cleanResearchQuery(task) {
  return String(task.description || task.title || '')
    .replace(/\b(research|find|look up|lookup|public|web|sources?|please|need|task)\b/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 160) || String(task.title || 'public research').slice(0, 160)
}
async function fetchJson(url, timeoutMs = 8000) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { signal: controller.signal, headers: { 'User-Agent': 'AgentDashboardResearchAdapter/0.1' } })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(timeout)
  }
}
async function fetchText(url, timeoutMs = 8000) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { signal: controller.signal, headers: { 'User-Agent': 'Mozilla/5.0 AgentDashboardResearchAdapter/0.1' } })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.text()
  } finally {
    clearTimeout(timeout)
  }
}
function cleanHtml(text) {
  return String(text || '')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim()
}
function parseBingResults(html) {
  const results = []
  const blocks = String(html || '').match(/<li class="b_algo"[\s\S]*?<\/li>/gi) || []
  for (const block of blocks.slice(0, 8)) {
    const linkMatch = block.match(/<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/i)
    if (!linkMatch) continue
    const snippetMatch = block.match(/<p[^>]*>([\s\S]*?)<\/p>/i)
    results.push({
      title: cleanHtml(linkMatch[2]).slice(0, 120),
      url: linkMatch[1],
      snippet: cleanHtml(snippetMatch ? snippetMatch[1] : '').slice(0, 500),
      source: 'Bing public search'
    })
  }
  return results
}
async function runPublicResearchAdapter(task, agent) {
  if (!shouldRunPublicResearchAdapter(task, agent)) {
    return {
      name: 'public-research-adapter',
      status: 'skipped',
      summary: 'Task does not require public research.',
      data: {},
      nextActions: []
    }
  }
  const query = cleanResearchQuery(task)
  const sources = []
  const errors = []
  try {
    const bingHtml = await fetchText(`https://www.bing.com/search?q=${encodeURIComponent(query)}`)
    sources.push(...parseBingResults(bingHtml))
  } catch (e) {
    errors.push(`Bing public search failed: ${e.message}`)
  }
  try {
    const ddg = await fetchJson(`https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1&skip_disambig=1`)
    if (ddg.AbstractText && ddg.AbstractURL) {
      sources.push({ title: ddg.Heading || query, url: ddg.AbstractURL, snippet: ddg.AbstractText, source: 'DuckDuckGo Instant Answer' })
    }
    for (const topic of (ddg.RelatedTopics || []).flatMap(item => item.Topics || [item]).slice(0, 5)) {
      if (topic.FirstURL && topic.Text) sources.push({ title: topic.Text.split(' - ')[0].slice(0, 90), url: topic.FirstURL, snippet: topic.Text, source: 'DuckDuckGo Related Topic' })
    }
  } catch (e) {
    errors.push(`DuckDuckGo lookup failed: ${e.message}`)
  }
  try {
    const wiki = await fetchJson(`https://en.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=5&namespace=0&format=json&origin=*`)
    const titles = wiki[1] || []
    const descriptions = wiki[2] || []
    const urls = wiki[3] || []
    titles.forEach((title, index) => {
      sources.push({ title, url: urls[index], snippet: descriptions[index] || '', source: 'Wikipedia OpenSearch' })
    })
  } catch (e) {
    errors.push(`Wikipedia lookup failed: ${e.message}`)
  }
  const uniqueSources = sources.filter((source, index, list) => source.url && list.findIndex(item => item.url === source.url) === index).slice(0, 10)
  return {
    name: 'public-research-adapter',
    status: uniqueSources.length ? 'completed' : 'needs-review',
    summary: uniqueSources.length ? `Found ${uniqueSources.length} public source(s) for "${query}".` : `No public sources returned for "${query}".`,
    data: {
      query,
      sources: uniqueSources,
      errors,
      researchedAt: new Date().toISOString()
    },
    nextActions: uniqueSources.length
      ? ['Review source snippets and links before using them in final work.', 'Ask AgentMajesty to turn sources into a brief or task plan.']
      : ['Refine the research query with specific names, location, program, or date range.']
  }
}

function buildMajestySystemPrompt() {
  reloadRuntimeData()
  const agentList = agents.filter(a => a.name !== 'AgentMajesty').map(a => `- ${a.name}: ${a.role || 'Specialized agent'}`).join('\n') || '- No specialized agents configured yet'
  const queuedCount = tasks.filter(t => t.status === 'queued' || t.status === 'running').length
  const completedCount = tasks.filter(t => t.status === 'completed' || t.status === 'completed-with-issues').length
  const openIssueCount = issues.filter(i => i.status !== 'resolved').length
  const memoryLines = Array.isArray(profile.memory) ? profile.memory.slice(0, 5).map(m => `  - ${m.text}`).join('\n') : ''
  return `You are AgentMajesty, an intelligent chief of staff for ${profile.name || 'the operator'} (${profile.role || 'Director of Communications'}).

Personality: Confident, warm, and strategically sharp. You think like a trusted advisor - direct, never verbose, always useful. Like a brilliant EA who anticipates needs.

Available specialized agents:
${agentList}

Current status: ${queuedCount} queued tasks, ${completedCount} completed, ${openIssueCount} open issues.

Operator profile:
- Priorities: ${profile.priorities || 'not specified'}
- Communication style: ${profile.communicationStyle || 'concise and direct'}
- Approval rules: ${profile.approvalRules || 'ask before external actions'}
${memoryLines ? `- Memory:\n${memoryLines}` : ''}

Instructions:
- Respond conversationally and concisely. Avoid excessive bullet points.
- When you want to create and assign a task to an agent, append this JSON block on a new line at the very END of your response ONLY (not inline):
[TASK:{"title":"Brief title","description":"Full task description","agentHint":"agent name or specialty keyword"}]
- Only create a task when the operator explicitly asks you to do something that requires agent work. For questions, analysis, or conversation - do NOT include the JSON block.
- Never include [TASK:...] in the middle of a response, only at the very end if needed.`
}

function loadAgentProfiles() {
  const profiles = {}
  try {
    if (!fs.existsSync(AGENTS_PROFILES_DIR)) return profiles
    const files = fs.readdirSync(AGENTS_PROFILES_DIR).filter(f => f.endsWith('.md'))
    for (const file of files) {
      try {
        const text = fs.readFileSync(path.join(AGENTS_PROFILES_DIR, file), 'utf8')
        profiles[path.basename(file, '.md').toLowerCase()] = text
      } catch (e) { /* skip unreadable file */ }
    }
  } catch (e) { /* ignore */ }
  return profiles
}

function getAgentSystemPrompt(agent, agentProfiles) {
  const name = String(agent.name || '').toLowerCase().replace(/[^a-z0-9]/g, '')
  for (const [key, text] of Object.entries(agentProfiles)) {
    const cleanKey = key.replace(/[^a-z0-9]/g, '')
    if (cleanKey === name || name.includes(cleanKey) || cleanKey.includes(name)) return text
  }
  return null
}

async function runLlmAdapter(task, agent, contextAdapters) {
  if (!aiConfig.enabled || !aiConfig.baseUrl || !aiConfig.model) {
    return {
      name: 'llm-adapter',
      status: 'skipped',
      summary: 'AI backend not configured. Go to the AI Settings tab to enable it.',
      data: {},
      nextActions: ['Open the AI Settings tab and configure a provider (Ollama, OpenAI, or GitHub Models).']
    }
  }
  const agentProfiles = loadAgentProfiles()
  const profileMd = getAgentSystemPrompt(agent, agentProfiles)
  let systemPrompt = profileMd
    ? profileMd
    : `You are ${agent.name}, a specialized AI agent.\nRole: ${agent.role || 'Specialized agent'}.`
  systemPrompt += `\n\n---\nOperator context:\n`
  systemPrompt += `- Name: ${profile.name || 'David'}, ${profile.role || 'Director of Communications'}\n`
  systemPrompt += `- Priorities: ${profile.priorities || 'not set'}\n`
  systemPrompt += `- Communication style: ${profile.communicationStyle || 'Concise, direct, action-oriented'}\n`
  systemPrompt += `- Approval rules: ${profile.approvalRules || 'Ask before sending email, deleting files, publishing, committing, pushing, or spending money'}\n`
  const recentMemory = Array.isArray(profile.memory) ? profile.memory.slice(0, 5) : []
  if (recentMemory.length) systemPrompt += `- Recent memory: ${recentMemory.map(m => m.text).join('; ')}\n`
  systemPrompt += `\nBe concise and direct. Return structured, actionable output. Never act on external systems without explicit operator approval.`

  let userMessage = `Task: ${task.description || task.title}\n`
  for (const result of contextAdapters) {
    if (result.status === 'skipped' || result.status === 'needs-configuration') continue
    if (result.name === 'public-research-adapter' && result.data?.sources?.length) {
      userMessage += `\nResearch context (${result.data.sources.length} public sources for "${result.data.query}"):\n`
      for (const s of result.data.sources.slice(0, 5)) {
        userMessage += `- ${s.title}: ${String(s.snippet || '').slice(0, 200)}\n  Source: ${s.url}\n`
      }
    }
    if (result.name === 'project-file-adapter' && result.data?.projectName) {
      userMessage += `\nProject context: ${result.data.projectName} (${result.data.filesConsidered} files scanned)\n`
      if (result.data.todoDocs?.length) {
        userMessage += `Open TODOs in project:\n`
        for (const d of result.data.todoDocs.slice(0, 3)) {
          userMessage += d.lines.slice(0, 2).map(l => `  - ${l}`).join('\n') + '\n'
        }
      }
    }
  }
  userMessage += '\nPlease complete this task. Be direct and actionable.'

  try {
    const res = await fetch(`${aiConfig.baseUrl.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(aiConfig.apiKey ? { 'Authorization': `Bearer ${aiConfig.apiKey}` } : {})
      },
      body: JSON.stringify({
        model: aiConfig.model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMessage }
        ],
        max_tokens: 1500,
        temperature: 0.7
      }),
      signal: AbortSignal.timeout(60000)
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`AI API HTTP ${res.status}: ${String(text).slice(0, 200)}`)
    }
    const data = await res.json()
    const content = data.choices?.[0]?.message?.content || ''
    return {
      name: 'llm-adapter',
      status: 'completed',
      summary: `${agent.name} generated a response via ${aiConfig.provider || 'AI'} (${aiConfig.model}).`,
      data: {
        provider: aiConfig.provider,
        model: aiConfig.model,
        response: content,
        usedProfileMarkdown: Boolean(profileMd),
        tokensUsed: data.usage?.total_tokens || null
      },
      nextActions: ['Review the AI response. Approve any follow-up action before executing externally.']
    }
  } catch (e) {
    logger.error('LLM adapter error: ' + e.message)
    return {
      name: 'llm-adapter',
      status: 'error',
      summary: `AI request failed: ${e.message}`,
      data: { error: e.message },
      nextActions: ['Check AI Settings — verify the base URL, model name, and API key are correct.']
    }
  }
}

async function runAdaptersForTask(task, agent) {
  reloadRuntimeData()
  const adapterResults = []
  adapterResults.push(runProjectFileAdapter(task, agent))
  adapterResults.push(await runPublicResearchAdapter(task, agent))
  adapterResults.push(runConnectorAdapter(task, agent))
  adapterResults.push(await runLlmAdapter(task, agent, adapterResults))
  return adapterResults
}

function detectTaskIssues(task, agent) {
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const agentLogText = (agent.logs || []).slice(-20).join(' ').toLowerCase()
  const found = []
  if (/credential|login|oauth|api key|access token|password/.test(text) || agentLogText.includes('awaiting constant contact credentials')) {
    found.push(createIssueRecord({
      taskId: task.id,
      agentId: agent.id,
      agentName: agent.name,
      severity: 'high',
      title: 'Credential or access needed',
      detail: `${agent.name} may need credentials, API access, or login context before executing this task outside the local harness.`
    }))
  }
  if (/blocked|error|failed|not working|stuck/.test(text)) {
    found.push(createIssueRecord({
      taskId: task.id,
      agentId: agent.id,
      agentName: agent.name,
      severity: 'medium',
      title: 'Task includes a blocker signal',
      detail: 'The task language indicates a possible blocker. AgentMajesty should ask for the missing detail or escalate before external action.'
    }))
  }
  return found
}
function recordAgentLearning(agent, task, linkedIssues) {
  const now = new Date().toISOString()
  const blocker = linkedIssues.length
    ? `Check ${linkedIssues.map(issue => issue.title.toLowerCase()).join(', ')} before running similar work.`
    : `For "${task.title}", reuse the ${agent.name} route and return structured next actions.`
  const learning = {
    id: `learn-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
    taskId: task.id,
    text: blocker,
    createdAt: now
  }
  agent.learning = [learning].concat(Array.isArray(agent.learning) ? agent.learning : []).slice(0, 20)
  return learning
}
function buildTaskResponse(task, agent, linkedIssues, learning, adapterResults) {
  const openAgentIssues = openIssuesForAgent(agent.id)
  const adapterActions = adapterResults.flatMap(result => result.nextActions || [])
  const nextActions = adapterActions.length ? adapterActions : linkedIssues.length
    ? [
        'Resolve the logged issue before external production execution.',
        'Confirm credentials or missing context with David.',
        'Re-run the task after the issue is resolved.'
      ]
    : [
        'Review the response data for quality.',
        'Approve any external action before sending, publishing, committing, or spending.',
        'Use this task as a learning reference for the next similar request.'
      ]
  return {
    summary: `${agent.name} completed the local execution pass for "${task.title}".`,
    recommendation: linkedIssues.length
      ? 'Treat this as complete with production blockers logged.'
      : 'Ready for review and the next execution step.',
    nextActions,
    data: {
      assignedAgentId: agent.id,
      assignedAgentName: agent.name,
      completedAt: new Date().toISOString(),
      appliedLearning: task.appliedLearning || [],
      newLearning: learning ? learning.text : null,
      openAgentIssues: openAgentIssues.length,
      adaptersRun: adapterResults.map(result => ({ name: result.name, status: result.status })),
      confidence: linkedIssues.length ? 'needs-review' : 'local-runtime-complete'
    },
    adapters: adapterResults,
    issues: linkedIssues.map(issue => ({
      id: issue.id,
      severity: issue.severity,
      title: issue.title,
      status: issue.status
    })),
    artifacts: []
  }
}
async function executeTaskRecord(taskId) {
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
  const linkedIssues = detectTaskIssues(task, agent)
  task.issueIds = Array.from(new Set([...(task.issueIds || []), ...linkedIssues.map(issue => issue.id)]))
  const adapterResults = await runAdaptersForTask(task, agent)
  const learning = recordAgentLearning(agent, task, linkedIssues)
  task.status = linkedIssues.length ? 'completed-with-issues' : 'completed'
  task.updatedAt = now
  task.logs = (task.logs || []).concat([
    `${now} - Execution started by ${agent.name}.`,
    `${now} - ${agent.name} acknowledged the task.`,
    `${now} - Ran adapters: ${adapterResults.map(result => `${result.name}:${result.status}`).join(', ')}.`,
    linkedIssues.length ? `${now} - Logged ${linkedIssues.length} issue(s) for review.` : `${now} - No production blockers detected.`,
    `${now} - Execution completed.`
  ])
  task.responseData = buildTaskResponse(task, agent, linkedIssues, learning, adapterResults)
  const llmResult = adapterResults.find(r => r.name === 'llm-adapter')
  const aiResponse = llmResult && llmResult.status === 'completed' ? llmResult.data?.response : null
  task.result = aiResponse || task.responseData.summary
  agent.status = 'idle'
  agent.progress = 100
  agent.logs = (agent.logs || []).concat([
    `${now} - Executed task ${task.id}: ${task.title}`,
    `${now} - Learned: ${learning.text}`,
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

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && (req.url === '/' || req.url === '/status')){
    const info = getMobileBridgeInfo()
    res.writeHead(200, {'Content-Type':'text/html'})
    return res.end(`<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Agent Dashboard Runtime</title>
    <style>
      body{font-family:Segoe UI,Arial,sans-serif;margin:32px;line-height:1.45;color:#111827}
      code{background:#f3f4f6;padding:2px 5px;border-radius:4px}
      a{color:#2563eb}
    </style>
  </head>
  <body>
    <h1>Agent Dashboard Runtime</h1>
    <p>The runtime API is running. The full dashboard opens in the Electron app, not this browser page.</p>
    <ul>
      <li><a href="/agents">/agents</a></li>
      <li><a href="/tasks">/tasks</a></li>
      <li><a href="/issues">/issues</a></li>
      <li><a href="/connectors">/connectors</a></li>
      <li><a href="/mobile-bridge">/mobile-bridge</a></li>
    </ul>
    <p>iPhone Shortcut endpoint: <code>${info.lanEndpoint}</code></p>
  </body>
</html>`)
  }

  if (req.method === 'GET' && req.url === '/agents'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(agents))
  }

  if (req.method === 'GET' && req.url === '/tasks'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(tasks))
  }

  if (req.method === 'GET' && req.url === '/issues'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(issues))
  }

  if (req.method === 'GET' && req.url === '/profile'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(profile))
  }

  if (req.method === 'GET' && req.url === '/contacts'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(contacts))
  }

  if (req.method === 'GET' && req.url === '/connectors'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(connectors.map(sanitizeConnectorForClient)))
  }

  if (req.method === 'GET' && req.url === '/projects'){
    reloadRuntimeData()
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(projects))
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
        sendEvent({ agents, tasks, issues })
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
        sendEvent({ agents, tasks, issues })
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

  if (req.method === 'POST' && req.url === '/connectors'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        createConnectorRecord(JSON.parse(body || '{}'))
        persist()
        sendEvent({ connectors: connectors.map(sanitizeConnectorForClient) })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(connectors.map(sanitizeConnectorForClient)))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'PUT' && req.url.startsWith('/connectors/')){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const id = decodeURIComponent(req.url.slice('/connectors/'.length))
        updateConnectorRecord(id, JSON.parse(body || '{}'))
        persist()
        sendEvent({ connectors: connectors.map(sanitizeConnectorForClient) })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(connectors.map(sanitizeConnectorForClient)))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url.startsWith('/connectors/') && req.url.endsWith('/test')){
    try {
      const id = decodeURIComponent(req.url.slice('/connectors/'.length, -'/test'.length))
      const connector = testConnectorRecord(id)
      persist()
      sendEvent({ connectors: connectors.map(sanitizeConnectorForClient) })
      res.writeHead(200, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ connectors: connectors.map(sanitizeConnectorForClient), connector: sanitizeConnectorForClient(connector) }))
    } catch (e){
      res.writeHead(404, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ error: e.message || 'connector not found' }))
    }
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
        sendEvent({ agents, tasks, issues, mobileBridge })
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
        if (routed) {
          routed.logs = (routed.logs || []).concat([`${new Date().toISOString()} - AgentMajesty routed task ${task.id}: ${message}`])
        }
        persist()
        sendEvent({ agents, tasks, issues })
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
      const task = await executeTaskRecord(id)
      persist()
      sendEvent({ agents, tasks, issues })
      res.writeHead(200, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ agents, tasks, issues, task }))
    } catch (e){
      res.writeHead(404, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ error: e.message || 'task not found' }))
    }
    return
  }

  if (req.method === 'POST' && req.url === '/issues'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const issue = createIssueRecord(JSON.parse(body || '{}'))
        persist()
        sendEvent({ agents, tasks, issues })
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ issues, issue }))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url.startsWith('/issues/') && req.url.endsWith('/resolve')){
    try {
      const id = decodeURIComponent(req.url.slice('/issues/'.length, -'/resolve'.length))
      const issue = issues.find(i => i.id === id)
      if (!issue) throw new Error('Issue not found')
      issue.status = 'resolved'
      issue.resolution = 'Resolved from dashboard'
      issue.updatedAt = new Date().toISOString()
      persist()
      sendEvent({ agents, tasks, issues })
      res.writeHead(200, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ issues, issue }))
    } catch (e){
      res.writeHead(404, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ error: e.message || 'issue not found' }))
    }
    return
  }

  if (req.method === 'GET' && req.url === '/todos'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(todos))
  }

  if (req.method === 'POST' && req.url === '/todos'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const todo = createTodoRecord(JSON.parse(body || '{}'))
        persist()
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ todos, todo }))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'PATCH' && req.url.startsWith('/todos/')){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const id = decodeURIComponent(req.url.slice('/todos/'.length))
        const todo = todos.find(t => t.id === id)
        if (!todo) throw new Error('Todo not found')
        const patch = JSON.parse(body || '{}')
        const allowed = ['title', 'description', 'status', 'priority', 'dueDate', 'tags']
        for (const key of allowed) {
          if (patch[key] !== undefined) todo[key] = patch[key]
        }
        todo.updatedAt = new Date().toISOString()
        persist()
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ todos, todo }))
      } catch (e){
        res.writeHead(404, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'todo not found' }))
      }
    })
    return
  }

  if (req.method === 'DELETE' && req.url.startsWith('/todos/')){
    try {
      const id = decodeURIComponent(req.url.slice('/todos/'.length))
      const idx = todos.findIndex(t => t.id === id)
      if (idx === -1) throw new Error('Todo not found')
      todos.splice(idx, 1)
      persist()
      res.writeHead(200, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ todos }))
    } catch (e){
      res.writeHead(404, {'Content-Type':'application/json'})
      res.end(JSON.stringify({ error: e.message || 'todo not found' }))
    }
    return
  }

  if (req.method === 'GET' && req.url === '/ai-config'){
    res.writeHead(200, {'Content-Type':'application/json'})
    const safe = { ...aiConfig, apiKey: aiConfig.apiKey ? maskSecret(aiConfig.apiKey) : '' }
    return res.end(JSON.stringify({ config: safe, providers: AI_PROVIDER_PRESETS }))
  }

  if (req.method === 'PUT' && req.url === '/ai-config'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const update = JSON.parse(body || '{}')
        if (update.apiKey && update.apiKey.startsWith('****')) delete update.apiKey
        aiConfig = { ...aiConfig, ...update, updatedAt: new Date().toISOString() }
        persistAiConfig()
        res.writeHead(200, {'Content-Type':'application/json'})
        const safe = { ...aiConfig, apiKey: aiConfig.apiKey ? maskSecret(aiConfig.apiKey) : '' }
        res.end(JSON.stringify({ ok: true, config: safe }))
      } catch (e) {
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: e.message || 'invalid body' }))
      }
    })
    return
  }

  if (req.method === 'POST' && req.url === '/ai-config/test'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      ;(async () => {
        let testCfg = aiConfig
        try { const parsed = JSON.parse(body || '{}'); if (parsed.baseUrl) testCfg = { ...aiConfig, ...parsed } } catch (e) {}
        if (!testCfg.baseUrl || !testCfg.model) {
          res.writeHead(200, {'Content-Type':'application/json'})
          return res.end(JSON.stringify({ ok: false, message: 'Base URL and model are required.' }))
        }
        try {
          const testRes = await fetch(`${testCfg.baseUrl.replace(/\/$/, '')}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(testCfg.apiKey && !testCfg.apiKey.startsWith('****') ? { 'Authorization': `Bearer ${testCfg.apiKey}` } : {})
            },
            body: JSON.stringify({
              model: testCfg.model,
              messages: [{ role: 'user', content: 'Reply with the single word: ready' }],
              max_tokens: 10
            }),
            signal: AbortSignal.timeout(15000)
          })
          if (!testRes.ok) {
            const text = await testRes.text()
            res.writeHead(200, {'Content-Type':'application/json'})
            return res.end(JSON.stringify({ ok: false, message: `AI API returned HTTP ${testRes.status}: ${String(text).slice(0, 200)}` }))
          }
          const data = await testRes.json()
          const reply = data.choices?.[0]?.message?.content || '(no response)'
          res.writeHead(200, {'Content-Type':'application/json'})
          res.end(JSON.stringify({ ok: true, message: `Connection successful. Model replied: "${reply.trim()}"` }))
        } catch (e) {
          res.writeHead(200, {'Content-Type':'application/json'})
          res.end(JSON.stringify({ ok: false, message: `Connection failed: ${e.message}` }))
        }
      })()
    })
    return
  }

  if (req.method === 'POST' && req.url === '/majesty/chat') {
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      ;(async () => {
        const { message, history = [] } = (() => { try { return JSON.parse(body || '{}') } catch (e) { return {} } })()
        res.writeHead(200, {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive'
        })
        const sendSSE = (data) => { try { res.write(`data: ${JSON.stringify(data)}\n\n`) } catch (e) {} }

        if (!aiConfig.enabled || !aiConfig.baseUrl || !aiConfig.model) {
          const routedAgent = routeTask(message || '', agents)
          const isTaskRequest = /\b(create|assign|add|do|run|execute|help me|please|can you|make|write|draft|find|research|check|send|update|build|fix|generate)\b/i.test(message || '') && !/(status|queue|what do you know|who is|what can|help$|^hi$|^hello$)/i.test(message || '')
          if (routedAgent && isTaskRequest) {
            const task = createTaskRecord(message, routedAgent)
            tasks.unshift(task)
            persist()
            sendEvent({ agents, tasks, issues })
            const reply = `I've created task **${task.id}** and assigned it to **${routedAgent.name}**. Go to the Tasks tab to execute it when ready.`
            sendSSE({ type: 'chunk', content: reply })
            sendSSE({ type: 'done', taskId: task.id, agentName: routedAgent.name })
          } else {
            const queuedTasks = tasks.filter(t => t.status === 'queued' || t.status === 'running')
            const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'completed-with-issues')
            const openIssues = issues.filter(i => i.status !== 'resolved')
            const m = String(message || '').toLowerCase()
            let reply = ''
            if (['status', 'queue', 'task status'].includes(m)) {
              reply = `Queue: ${queuedTasks.length} queued, ${completedTasks.length} completed, ${agents.length} agents, ${connectors.filter(c => c.status === 'ready').length} connectors ready.`
            } else if (m.includes('what do you know') || m.includes('who am i')) {
              reply = `I know you as **${profile.name || 'David'}**, ${profile.role || 'Director of Communications'}. Priorities: ${profile.priorities || 'not set'}. Style: ${profile.communicationStyle || 'not set'}.`
            } else {
              reply = `I'm ready to help. AI is currently disabled - go to **AI Settings** to connect a model and unlock full capabilities. I can still route tasks to agents without AI.`
            }
            sendSSE({ type: 'chunk', content: reply })
            sendSSE({ type: 'done' })
          }
          return res.end()
        }

        const systemPrompt = buildMajestySystemPrompt()
        const messages = [
          { role: 'system', content: systemPrompt },
          ...history.slice(-8).filter(m => m.text).map(m => ({
            role: m.from === 'You' ? 'user' : 'assistant',
            content: m.text
          })),
          { role: 'user', content: message || '' }
        ]

        let fullContent = ''
        try {
          const llmRes = await fetch(`${aiConfig.baseUrl.replace(/\/$/, '')}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(aiConfig.apiKey ? { 'Authorization': `Bearer ${aiConfig.apiKey}` } : {})
            },
            body: JSON.stringify({
              model: aiConfig.model,
              messages,
              stream: true,
              max_tokens: 1500,
              temperature: 0.7
            }),
            signal: AbortSignal.timeout(60000)
          })

          if (!llmRes.ok) {
            const errText = await llmRes.text()
            sendSSE({ type: 'chunk', content: `I ran into an issue with the AI backend (HTTP ${llmRes.status}). Check AI Settings.` })
            sendSSE({ type: 'done' })
            return res.end()
          }

          const reader = llmRes.body.getReader()
          const decoder = new TextDecoder()
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            const chunk = decoder.decode(value, { stream: true })
            for (const line of chunk.split('\n')) {
              if (!line.startsWith('data: ')) continue
              const dataStr = line.slice(6).trim()
              if (dataStr === '[DONE]') continue
              try {
                const data = JSON.parse(dataStr)
                const delta = data.choices?.[0]?.delta?.content || ''
                if (delta) {
                  fullContent += delta
                  sendSSE({ type: 'chunk', content: delta })
                }
              } catch (e) {}
            }
          }
        } catch (e) {
          logger.error('Majesty chat LLM error: ' + e.message)
          sendSSE({ type: 'chunk', content: `I couldn't reach the AI backend: ${e.message}` })
          sendSSE({ type: 'done' })
          return res.end()
        }

        const taskMatch = fullContent.match(/\[TASK:(\{[^}]+\})\]/)
        if (taskMatch) {
          try {
            const taskSpec = JSON.parse(taskMatch[1])
            const hint = String(taskSpec.agentHint || '').toLowerCase()
            const routedAgent = agents.find(a => a.name !== 'AgentMajesty' && (
              String(a.name || '').toLowerCase().includes(hint) ||
              String(a.role || '').toLowerCase().includes(hint) ||
              hint.includes(String(a.name || '').toLowerCase().replace(/\s+/g, ''))
            )) || agents.find(a => a.name !== 'AgentMajesty')
            if (routedAgent) {
              const task = createTaskRecord(taskSpec.description || taskSpec.title || message, routedAgent)
              task.title = taskSpec.title || task.title
              tasks.unshift(task)
              persist()
              sendEvent({ agents, tasks, issues })
              sendSSE({ type: 'done', taskId: task.id, agentName: routedAgent.name })
            } else {
              sendSSE({ type: 'done' })
            }
          } catch (e) {
            sendSSE({ type: 'done' })
          }
        } else {
          sendSSE({ type: 'done' })
        }
        res.end()
      })()
    })
    return
  }

  // fallback
  res.writeHead(404, {'Content-Type':'text/plain'})
  res.end('Not found')
})

const PORT = process.env.AGENT_SERVER_PORT || 4000
const HOST = process.env.AGENT_SERVER_HOST || '0.0.0.0'
server.listen(PORT, HOST, () => {
  const info = getMobileBridgeInfo()
  console.log(`Agent runtime listening on http://127.0.0.1:${PORT}`)
  console.log(`iPhone bridge available at ${info.lanEndpoint}`)
  if (HOST === '0.0.0.0') console.log(`Network bind address: ${HOST}:${PORT}`)
})

// Deterministic task worker for processing running tasks in production-like mode
setInterval(async () => {
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
        await executeTaskRecord(task.id)
      } catch (e) {
        console.error('Failed to execute task:', e)
        agent.status = 'idle'
      }
      delete runningTasks[agentId]
    }
  }
  if (changed) { persist(); sendEvent({ agents, tasks, issues }) }
}, 1000)
