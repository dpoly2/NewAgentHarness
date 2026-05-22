const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const os = require('os')
const path = require('path')

const AGENT_RUNTIME_URL = `http://127.0.0.1:${process.env.AGENT_SERVER_PORT || 4000}`
let readRuntimeWarningShown = false
let commandRuntimeWarningShown = false

app.commandLine.appendSwitch('disk-cache-dir', path.join(app.getPath('temp'), 'agent-dashboard-cache'))
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache')

function readAgentsFile() {
  const fs = require('fs')
  const p = path.join(__dirname, 'data', 'agents.json')
  let raw = fs.readFileSync(p, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  return JSON.parse(raw)
}

function readJsonFile(filename, fallback) {
  const fs = require('fs')
  const p = path.join(__dirname, 'data', filename)
  if (!fs.existsSync(p)) {
    fs.writeFileSync(p, JSON.stringify(fallback, null, 2), 'utf8')
    return fallback
  }
  let raw = fs.readFileSync(p, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  return JSON.parse(raw)
}

function writeJsonFile(filename, data) {
  const fs = require('fs')
  const p = path.join(__dirname, 'data', filename)
  fs.writeFileSync(p, JSON.stringify(data, null, 2), 'utf8')
}

function readTasksFile() {
  return readJsonFile('tasks.json', [])
}

function writeTasksFile(tasks) {
  writeJsonFile('tasks.json', tasks)
}

function readIssuesFile() {
  return readJsonFile('issues.json', [])
}

function writeIssuesFile(issues) {
  writeJsonFile('issues.json', issues)
}

function readConnectorsFile() {
  return readJsonFile('connectors.json', [])
}

function writeConnectorsFile(connectors) {
  writeJsonFile('connectors.json', connectors)
}

function readProjectsFile() {
  return readJsonFile('projects.json', [])
}

function writeProjectsFile(projects) {
  writeJsonFile('projects.json', projects)
}

function readAiConfigFile() {
  return readJsonFile('ai_config.json', {
    provider: 'ollama',
    baseUrl: 'http://localhost:11434/v1',
    apiKey: '',
    model: 'llama3.2',
    enabled: false
  })
}

function writeAiConfigFile(config) {
  writeJsonFile('ai_config.json', config)
}

const AI_PROVIDER_PRESETS = {
  ollama: { baseUrl: 'http://localhost:11434/v1', model: 'llama3.2' },
  openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  github: { baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini' }
}

function readMobileBridgeFile() {
  return readJsonFile('mobile_bridge.json', {
    enabled: true,
    channel: 'iPhone Shortcuts',
    trustedSender: '',
    messages: []
  })
}

function writeMobileBridgeFile(config) {
  writeJsonFile('mobile_bridge.json', config)
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

function readProfileFile() {
  return readJsonFile('profile.json', defaultProfile())
}

function writeProfileFile(profile) {
  writeJsonFile('profile.json', profile)
}

function readContactsFile() {
  return readJsonFile('contacts.json', [])
}

function writeContactsFile(contacts) {
  writeJsonFile('contacts.json', contacts)
}

function createContactRecord(input, contacts) {
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
  return text.length <= 4 ? '****' : `****${text.slice(-4)}`
}

function sanitizeConnectorForClient(connector) {
  const safe = { ...connector, config: { ...(connector.config || {}) } }
  for (const key of ['password', 'apiKey', 'apiSecret', 'clientSecret', 'accessToken', 'refreshToken']) {
    if (safe.config[key]) safe.config[key] = maskSecret(safe.config[key])
  }
  return safe
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

function createConnectorRecord(input, connectors) {
  const type = String(input.type || '').trim()
  if (!['gmail', 'outlook', 'smtp', 'constant-contact'].includes(type)) throw new Error('Connector type is required')
  const name = String(input.name || '').trim()
  if (!name) throw new Error('Connector name is required')
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

function updateConnectorRecord(id, input, connectors) {
  const connector = connectors.find(item => item.id === id)
  if (!connector) throw new Error('Connector not found')
  const now = new Date().toISOString()
  if (input.name !== undefined) connector.name = String(input.name || '').trim() || connector.name
  if (input.config) connector.config = { ...(connector.config || {}), ...normalizeConnectorConfig({ ...input, type: connector.type }) }
  connector.updatedAt = now
  connector.logs = (connector.logs || []).concat([`${now} - Connector updated.`])
  return connector
}

function testConnectorRecord(id, connectors) {
  const connector = connectors.find(item => item.id === id)
  if (!connector) throw new Error('Connector not found')
  const now = new Date().toISOString()
  const config = connector.config || {}
  let ok = true
  let message = 'Configuration is ready for a live adapter.'
  if (connector.type === 'smtp') {
    ok = Boolean(config.host && config.port && config.username && config.password)
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

function walkProjectFiles(rootDir, limit = 600) {
  const fs = require('fs')
  const ignored = new Set(['.git', 'node_modules', 'dist', 'build', '.next', '.cache', 'logs'])
  const files = []
  function walk(dir) {
    if (files.length >= limit) return
    let entries = []
    try { entries = fs.readdirSync(dir, { withFileTypes: true }) } catch (e) { return }
    for (const entry of entries) {
      if (files.length >= limit) break
      if (ignored.has(entry.name)) continue
      const fullPath = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        walk(fullPath)
      } else if (entry.isFile()) {
        let stat = null
        try { stat = fs.statSync(fullPath) } catch (e) {}
        files.push({
          path: path.relative(rootDir, fullPath),
          ext: path.extname(entry.name).toLowerCase(),
          size: stat ? stat.size : 0,
          updatedAt: stat ? stat.mtime.toISOString() : null
        })
      }
    }
  }
  walk(rootDir)
  return files
}

function readProjectDocSnippets(rootDir, files) {
  const fs = require('fs')
  const docNames = /(^readme|todo|notes|plan|project|status|changelog|requirements)/i
  return files
    .filter(file => docNames.test(path.basename(file.path)) && ['.md', '.txt', '.json'].includes(file.ext))
    .slice(0, 8)
    .map(file => {
      try {
        const text = fs.readFileSync(path.join(rootDir, file.path), 'utf8').replace(/^\uFEFF/, '')
        return { path: file.path, text: text.slice(0, 1200) }
      } catch (e) {
        return { path: file.path, text: '' }
      }
    })
}

function readGitTimeline(rootDir) {
  const { execFileSync } = require('child_process')
  try {
    const output = execFileSync('git', ['-C', rootDir, 'log', '--date=iso', '--pretty=format:%h|%ad|%s', '-n', '30'], {
      encoding: 'utf8',
      timeout: 5000,
      windowsHide: true
    })
    return output.split(/\r?\n/).filter(Boolean).map(line => {
      const [hash, date, ...subject] = line.split('|')
      return { hash, date, subject: subject.join('|') }
    })
  } catch (e) {
    return []
  }
}

function inferProjectAgents(files, docs) {
  const text = `${files.map(file => file.path).join(' ')} ${docs.map(doc => doc.text).join(' ')}`.toLowerCase()
  const suggestions = []
  if (/wordpress|plugin|wp-content/.test(text)) suggestions.push('WordPress Agent')
  if (/grant|funding|proposal/.test(text)) suggestions.push('Grant Research Agent')
  if (/newsletter|constant contact|campaign|email/.test(text)) suggestions.push('Communications Agent')
  if (/real estate|property|parcel/.test(text)) suggestions.push('Real Estate Research Agent')
  if (/timeline|milestone|roadmap|project/.test(text)) suggestions.push('Project Manager Agent')
  return Array.from(new Set(suggestions))
}

function createProjectImport(folderPath, projects, agents, tasks) {
  const fs = require('fs')
  if (!folderPath || !fs.existsSync(folderPath)) throw new Error('Project folder not found')
  const now = new Date().toISOString()
  const files = walkProjectFiles(folderPath)
  const docs = readProjectDocSnippets(folderPath, files)
  const gitTimeline = readGitTimeline(folderPath)
  const suggestedAgents = inferProjectAgents(files, docs)
  const project = {
    id: `project-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
    name: path.basename(folderPath),
    path: folderPath,
    status: 'imported',
    importedAt: now,
    updatedAt: now,
    summary: {
      filesScanned: files.length,
      docsImported: docs.length,
      commitsImported: gitTimeline.length,
      suggestedAgents
    },
    docs,
    files: files.slice(0, 250),
    timeline: gitTimeline.map(commit => ({
      type: 'commit',
      date: commit.date,
      title: commit.subject,
      ref: commit.hash
    })),
    notes: [`${now} - Imported from local folder.`]
  }
  projects.unshift(project)
  const routed = routeTask(`Review imported project ${project.name} and create execution plan`, agents)
  const task = createTaskRecord(`Review imported project ${project.name} and create execution plan`, routed)
  task.projectId = project.id
  task.logs = (task.logs || []).concat([`${now} - Project import created this planning task.`])
  tasks.unshift(task)
  return { project, task }
}

function scoreProjectForTask(project, task) {
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const haystack = `${project.name || ''} ${project.path || ''} ${(project.docs || []).map(doc => `${doc.path} ${doc.text}`).join(' ')}`.toLowerCase()
  return text.split(/\W+/).filter(word => word.length > 3 && haystack.includes(word)).length
}

function getTaskProject(task, projects) {
  if (task.projectId) return projects.find(project => project.id === task.projectId) || null
  return projects
    .map(project => ({ project, score: scoreProjectForTask(project, task) }))
    .sort((a, b) => b.score - a.score)[0]?.project || projects[0] || null
}

function runProjectFileAdapter(task, projects) {
  const project = getTaskProject(task, projects)
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
  const words = text.split(/\W+/).filter(word => word.length > 4)
  const matches = files.filter(file => words.some(word => file.path.toLowerCase().includes(word))).slice(0, 12)
  const todoDocs = docs
    .map(doc => ({
      path: doc.path,
      lines: String(doc.text || '').split(/\r?\n/).filter(line => /todo|fixme|next|task|issue|bug/i.test(line)).slice(0, 8)
    }))
    .filter(doc => doc.lines.length)
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
      recentTimeline: (project.timeline || []).slice(0, 8)
    },
    nextActions: [
      matches.length ? 'Review matching files before making edits.' : 'Import deeper docs or mention a specific file for targeted work.',
      todoDocs.length ? 'Convert detected TODO/issue lines into queue tasks.' : 'Ask AgentMajesty to create a project plan from imported docs.',
      'Require approval before writing files.'
    ]
  }
}

function runConnectorAdapter(task, connectors) {
  const text = `${task.title || ''} ${task.description || ''}`.toLowerCase()
  const wantsMail = /email|gmail|outlook|smtp|newsletter|campaign|constant contact/.test(text)
  if (!wantsMail) {
    return { name: 'connector-adapter', status: 'skipped', summary: 'Task does not require an external connector.', data: {}, nextActions: [] }
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
    summary: ready.length ? `Found ${ready.length} ready connector(s) for this task.` : `Found ${relevant.length} connector profile(s), but none are ready yet.`,
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
    return { name: 'public-research-adapter', status: 'skipped', summary: 'Task does not require public research.', data: {}, nextActions: [] }
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
    data: { query, sources: uniqueSources, errors, researchedAt: new Date().toISOString() },
    nextActions: uniqueSources.length
      ? ['Review source snippets and links before using them in final work.', 'Ask AgentMajesty to turn sources into a brief or task plan.']
      : ['Refine the research query with specific names, location, program, or date range.']
  }
}

async function runAdaptersForTask(task, agent, projects, connectors) {
  return [
    runProjectFileAdapter(task, projects),
    await runPublicResearchAdapter(task, agent),
    runConnectorAdapter(task, connectors)
  ]
}

function messagePartsToText(parts) {
  if (!Array.isArray(parts)) return ''
  return parts.map(part => {
    if (typeof part === 'string') return part
    if (part && typeof part.text === 'string') return part.text
    return ''
  }).join('\n').trim()
}

function extractChatGptUserMessages(conversations) {
  if (!Array.isArray(conversations)) return []
  const messages = []
  for (const conversation of conversations) {
    const title = conversation.title || 'Untitled conversation'
    const mapping = conversation.mapping || {}
    for (const node of Object.values(mapping)) {
      const message = node && node.message
      if (!message || message.author?.role !== 'user') continue
      const text = messagePartsToText(message.content?.parts)
      if (text) messages.push({ title, text })
    }
  }
  return messages
}

function summarizeChatGptHistory(messages) {
  const text = messages.map(message => message.text).join('\n').toLowerCase()
  const topics = [
    ['communications', /communication|newsletter|email|social media|blast|press release|sigma signal/g],
    ['grants', /grant|funding|proposal|nonprofit|foundation/g],
    ['real estate', /real estate|property|parcel|capital|investor/g],
    ['websites', /wordpress|website|plugin|dashboard|app/g],
    ['agents', /agent|automation|workflow|task|dashboard/g]
  ].map(([name, pattern]) => ({ name, count: (text.match(pattern) || []).length }))
    .filter(topic => topic.count > 0)
    .sort((a, b) => b.count - a.count)
  const preferenceLines = messages
    .map(message => message.text)
    .filter(line => /\b(i prefer|i like|i don't like|always ask me|do not|don't|my priority is|i usually|make sure)\b/i.test(line))
    .slice(0, 12)
  return { count: messages.length, topics, preferenceLines }
}

function writeAgentsFile(agents) {
  const fs = require('fs')
  const p = path.join(__dirname, 'data', 'agents.json')
  fs.writeFileSync(p, JSON.stringify(agents, null, 2), 'utf8')
}

function broadcastDashboard(agents, tasks, issues, connectors) {
  const wins = BrowserWindow.getAllWindows()
  for (const w of wins) {
    try { w.webContents.send('agents-updated', agents) } catch (e) { console.error('send failed', e) }
    if (tasks) {
      try { w.webContents.send('tasks-updated', tasks) } catch (e) { console.error('send failed', e) }
    }
    if (issues) {
      try { w.webContents.send('issues-updated', issues) } catch (e) { console.error('send failed', e) }
    }
    if (connectors) {
      try { w.webContents.send('connectors-updated', connectors) } catch (e) { console.error('send failed', e) }
    }
  }
}

function broadcastChiefOfStaff(profile, contacts) {
  const wins = BrowserWindow.getAllWindows()
  for (const w of wins) {
    if (profile) {
      try { w.webContents.send('profile-updated', profile) } catch (e) { console.error('send failed', e) }
    }
    if (contacts) {
      try { w.webContents.send('contacts-updated', contacts) } catch (e) { console.error('send failed', e) }
    }
  }
}

function slugifyAgentName(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function createAgentRecord(input, agents) {
  const name = String(input.name || '').trim()
  if (!name) throw new Error('Agent name is required')
  const existing = agents.find(a => a.name.toLowerCase() === name.toLowerCase())
  if (existing) return { agent: existing, created: false }
  const idBase = slugifyAgentName(name) || `agent-${agents.length + 1}`
  let id = idBase
  let suffix = 2
  while (agents.some(a => a.id === id)) {
    id = `${idBase}-${suffix}`
    suffix += 1
  }
  const now = new Date().toISOString()
  const agent = {
    id,
    name,
    status: 'idle',
    progress: 0,
    role: String(input.role || 'Specialized agent').trim(),
    logs: [`${now} - Agent added manually.`]
  }
  agents.push(agent)
  return { agent, created: true }
}

function routeTask(message, agents) {
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
  return {
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
}

function createIssueRecord(input, issues) {
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
    source: input.source || 'main-fallback',
    createdAt: now,
    updatedAt: now,
    resolution: null
  }
  issues.unshift(issue)
  return issue
}

function openIssuesForAgent(agentId, issues) {
  return issues.filter(issue => issue.agentId === agentId && issue.status !== 'resolved')
}

function detectTaskIssues(task, agent, issues) {
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
    }, issues))
  }
  if (/blocked|error|failed|not working|stuck/.test(text)) {
    found.push(createIssueRecord({
      taskId: task.id,
      agentId: agent.id,
      agentName: agent.name,
      severity: 'medium',
      title: 'Task includes a blocker signal',
      detail: 'The task language indicates a possible blocker. AgentMajesty should ask for missing detail or escalate before external action.'
    }, issues))
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

function buildTaskResponse(task, agent, linkedIssues, learning, issues, adapterResults) {
  const adapterActions = adapterResults.flatMap(result => result.nextActions || [])
  return {
    summary: `${agent.name} completed the local execution pass for "${task.title}".`,
    recommendation: linkedIssues.length ? 'Treat this as complete with production blockers logged.' : 'Ready for review and the next execution step.',
    nextActions: adapterActions.length ? adapterActions : linkedIssues.length
      ? ['Resolve the logged issue before external production execution.', 'Confirm credentials or missing context with David.', 'Re-run the task after the issue is resolved.']
      : ['Review the response data for quality.', 'Approve any external action before sending, publishing, committing, or spending.', 'Use this task as a learning reference for the next similar request.'],
    data: {
      assignedAgentId: agent.id,
      assignedAgentName: agent.name,
      completedAt: new Date().toISOString(),
      appliedLearning: task.appliedLearning || [],
      newLearning: learning ? learning.text : null,
      openAgentIssues: openIssuesForAgent(agent.id, issues).length,
      adaptersRun: adapterResults.map(result => ({ name: result.name, status: result.status })),
      confidence: linkedIssues.length ? 'needs-review' : 'local-runtime-complete'
    },
    adapters: adapterResults,
    issues: linkedIssues.map(issue => ({ id: issue.id, severity: issue.severity, title: issue.title, status: issue.status })),
    artifacts: []
  }
}

async function executeTaskRecord(taskId, agents, tasks, issues, projects = [], connectors = []) {
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
  const linkedIssues = detectTaskIssues(task, agent, issues)
  task.issueIds = Array.from(new Set([...(task.issueIds || []), ...linkedIssues.map(issue => issue.id)]))
  const adapterResults = await runAdaptersForTask(task, agent, projects, connectors)
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
  task.responseData = buildTaskResponse(task, agent, linkedIssues, learning, issues, adapterResults)
  task.result = task.responseData.summary
  agent.status = 'idle'
  agent.progress = 100
  agent.logs = (agent.logs || []).concat([
    `${now} - Executed task ${task.id}: ${task.title}`,
    `${now} - Learned: ${learning.text}`,
    `${now} - completed`
  ])
  return task
}

function receiveMobileMessage(input, agents, tasks, bridge) {
  const text = String(input.text || input.message || '').trim()
  if (!text) throw new Error('Message text is required')
  const from = String(input.from || 'iPhone').trim()
  const now = new Date().toISOString()
  const routed = routeTask(text, agents)
  const task = createTaskRecord(text, routed)
  task.source = 'mobile'
  task.mobileFrom = from
  task.logs = (task.logs || []).concat([`${now} - Received from ${from} through ${bridge.channel || 'mobile bridge'}.`])
  tasks.unshift(task)
  if (routed) {
    routed.logs = (routed.logs || []).concat([`${now} - Mobile message routed as ${task.id}: ${text}`])
  }
  bridge.messages = [{
    id: `mobile-${Date.now()}`,
    from,
    text,
    taskId: task.id,
    receivedAt: now
  }].concat(Array.isArray(bridge.messages) ? bridge.messages : []).slice(0, 50)
  return task
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  })

  // In dev you'll run a local dev server (vite). When developing, load the Vite dev server URL.
  const isDev = process.env.NODE_ENV === 'development' || process.env.ELECTRON_DEV === '1' || !!process.env.VITE_DEV_SERVER_URL
  if (isDev) {
    // Load the Vite dev server's copy of the renderer (renderer/index.html)
    const base = (process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173').replace(/\/$/, '')
    const devUrl = base + '/renderer/index.html'
    win.loadURL(devUrl)
    // Open DevTools in detached mode for debugging
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(path.join(__dirname, 'dist', 'renderer', 'index.html'))
  }
}

// Provide an IPC handler so preload can request agent data from the main process
ipcMain.handle('read-agents', async () => {
  // Try HTTP agent runtime first
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/agents`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading agents from local file.`)
      readRuntimeWarningShown = true
    }
  }
  // Fallback to file
  try {
    return readAgentsFile()
  } catch (e) {
    console.error('read-agents fallback error', e)
    return []
  }
})

// Agent commands now call the runtime HTTP API, fallback to local file update
ipcMain.handle('agent-command', async (event, { id, action }) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/agent-command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, action })
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; applying command to local file.`)
      commandRuntimeWarningShown = true
    }
  }
  // fallback to file modification
  try {
    const agents = readAgentsFile()
    const idx = agents.findIndex(a => a.id === id)
    if (idx === -1) return agents
    const agent = agents[idx]
    const ts = new Date().toISOString()
    if (action === 'start') {
      agent.status = 'running'
      if (!agent.progress || agent.progress >= 100) agent.progress = 0
      agent.logs = (agent.logs || []).concat([`${ts} - started`])
    } else if (action === 'stop') {
      agent.status = 'idle'
      agent.logs = (agent.logs || []).concat([`${ts} - stopped`])
    } else if (action === 'ping') {
      agent.logs = (agent.logs || []).concat([`${ts} - ping`])
    }
    agents[idx] = agent
    writeAgentsFile(agents)
    broadcastDashboard(agents)
    return agents
  } catch (e) {
    console.error('agent-command fallback error', e)
    return []
  }
})

ipcMain.handle('add-agent', async (event, input) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; adding agent to local file.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const agents = readAgentsFile()
    createAgentRecord(input, agents)
    writeAgentsFile(agents)
    broadcastDashboard(agents)
    return agents
  } catch (e) {
    console.error('add-agent fallback error', e)
    return []
  }
})

ipcMain.handle('agent-chat', async (event, { message }) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/agent-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; routing chat locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const agents = readAgentsFile()
    const tasks = readTasksFile()
    const routed = routeTask(message, agents)
    const ts = new Date().toISOString()
    const task = createTaskRecord(message, routed)
    tasks.unshift(task)
    if (routed) {
      routed.logs = (routed.logs || []).concat([`${ts} - AgentMajesty routed task ${task.id}: ${message}`])
    }
    writeAgentsFile(agents)
    writeTasksFile(tasks)
    broadcastDashboard(agents, tasks)
    return {
      agents,
      tasks,
      task,
      reply: routed
        ? `AgentMajesty created ${task.id} and assigned it to ${routed.name}.`
        : 'AgentMajesty could not find a specialized agent yet. Add one from the sidebar.'
    }
  } catch (e) {
    console.error('agent-chat fallback error', e)
    return { agents: [], tasks: [], reply: 'AgentMajesty could not route that task.' }
  }
})

ipcMain.handle('read-tasks', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/tasks`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading tasks from local file.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return readTasksFile()
  } catch (e) {
    console.error('read-tasks fallback error', e)
    return []
  }
})

ipcMain.handle('read-issues', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/issues`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading issues from local file.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return readIssuesFile()
  } catch (e) {
    console.error('read-issues fallback error', e)
    return []
  }
})

ipcMain.handle('read-connectors', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/connectors`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading connectors from local file.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return readConnectorsFile().map(sanitizeConnectorForClient)
  } catch (e) {
    console.error('read-connectors fallback error', e)
    return []
  }
})

ipcMain.handle('add-connector', async (event, input) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/connectors`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; adding connector locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const connectors = readConnectorsFile()
    createConnectorRecord(input, connectors)
    writeConnectorsFile(connectors)
    const safe = connectors.map(sanitizeConnectorForClient)
    broadcastDashboard(readAgentsFile(), readTasksFile(), readIssuesFile(), safe)
    return safe
  } catch (e) {
    console.error('add-connector fallback error', e)
    return []
  }
})

ipcMain.handle('test-connector', async (event, { id }) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/connectors/${encodeURIComponent(id)}/test`, { method: 'POST' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; testing connector locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const connectors = readConnectorsFile()
    const connector = testConnectorRecord(id, connectors)
    writeConnectorsFile(connectors)
    const safe = connectors.map(sanitizeConnectorForClient)
    broadcastDashboard(readAgentsFile(), readTasksFile(), readIssuesFile(), safe)
    return { connectors: safe, connector: sanitizeConnectorForClient(connector) }
  } catch (e) {
    console.error('test-connector fallback error', e)
    return { connectors: [], error: e.message || 'Connector test failed' }
  }
})

ipcMain.handle('read-projects', async () => {
  try {
    return readProjectsFile()
  } catch (e) {
    console.error('read-projects fallback error', e)
    return []
  }
})

ipcMain.handle('select-project-folder', async () => {
  const result = await dialog.showOpenDialog({
    title: 'Select project folder to import',
    properties: ['openDirectory']
  })
  return result.canceled ? null : result.filePaths[0]
})

ipcMain.handle('import-project-folder', async (event, { folderPath }) => {
  try {
    const projects = readProjectsFile()
    const agents = readAgentsFile()
    const tasks = readTasksFile()
    const result = createProjectImport(folderPath, projects, agents, tasks)
    writeProjectsFile(projects)
    writeAgentsFile(agents)
    writeTasksFile(tasks)
    broadcastDashboard(agents, tasks, readIssuesFile(), readConnectorsFile().map(sanitizeConnectorForClient))
    return { projects, agents, tasks, ...result }
  } catch (e) {
    console.error('import-project-folder error', e)
    return { error: e.message || 'Project import failed' }
  }
})

ipcMain.handle('execute-task', async (event, { id }) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/tasks/${encodeURIComponent(id)}/execute`, {
      method: 'POST'
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; executing task locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const agents = readAgentsFile()
    const tasks = readTasksFile()
    const issues = readIssuesFile()
    const projects = readProjectsFile()
    const connectors = readConnectorsFile()
    const task = await executeTaskRecord(id, agents, tasks, issues, projects, connectors)
    writeAgentsFile(agents)
    writeTasksFile(tasks)
    writeIssuesFile(issues)
    broadcastDashboard(agents, tasks, issues)
    return { agents, tasks, issues, task }
  } catch (e) {
    console.error('execute-task fallback error', e)
    return { agents: [], tasks: [], error: e.message || 'Task execution failed' }
  }
})

ipcMain.handle('log-issue', async (event, input) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/issues`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; logging issue locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const issues = readIssuesFile()
    const issue = createIssueRecord(input, issues)
    writeIssuesFile(issues)
    broadcastDashboard(readAgentsFile(), readTasksFile(), issues)
    return { issues, issue }
  } catch (e) {
    console.error('log-issue fallback error', e)
    return { issues: [], error: e.message || 'Issue logging failed' }
  }
})

ipcMain.handle('resolve-issue', async (event, { id }) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/issues/${encodeURIComponent(id)}/resolve`, { method: 'POST' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; resolving issue locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const issues = readIssuesFile()
    const issue = issues.find(item => item.id === id)
    if (!issue) throw new Error('Issue not found')
    issue.status = 'resolved'
    issue.resolution = 'Resolved from dashboard'
    issue.updatedAt = new Date().toISOString()
    writeIssuesFile(issues)
    broadcastDashboard(readAgentsFile(), readTasksFile(), issues)
    return { issues, issue }
  } catch (e) {
    console.error('resolve-issue fallback error', e)
    return { issues: [], error: e.message || 'Issue resolve failed' }
  }
})

ipcMain.handle('read-profile', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/profile`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading profile from local file.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return readProfileFile()
  } catch (e) {
    console.error('read-profile fallback error', e)
    return defaultProfile()
  }
})

ipcMain.handle('update-profile', async (event, profileUpdate) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileUpdate)
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; updating profile locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const current = readProfileFile()
    const profile = { ...current, ...profileUpdate, updatedAt: new Date().toISOString() }
    writeProfileFile(profile)
    broadcastChiefOfStaff(profile)
    return profile
  } catch (e) {
    console.error('update-profile fallback error', e)
    return defaultProfile()
  }
})

ipcMain.handle('remember-note', async (event, { note }) => {
  const cleaned = String(note || '').trim()
  if (!cleaned) return readProfileFile()
  try {
    const current = readProfileFile()
    const memory = Array.isArray(current.memory) ? current.memory : []
    const profile = {
      ...current,
      memory: [{ text: cleaned, createdAt: new Date().toISOString() }].concat(memory).slice(0, 50),
      updatedAt: new Date().toISOString()
    }
    writeProfileFile(profile)
    broadcastChiefOfStaff(profile)
    return profile
  } catch (e) {
    console.error('remember-note fallback error', e)
    return defaultProfile()
  }
})

ipcMain.handle('read-contacts', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/contacts`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading contacts from local file.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return readContactsFile()
  } catch (e) {
    console.error('read-contacts fallback error', e)
    return []
  }
})

ipcMain.handle('add-contact', async (event, input) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/contacts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input)
    })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!commandRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; adding contact locally.`)
      commandRuntimeWarningShown = true
    }
  }
  try {
    const contacts = readContactsFile()
    createContactRecord(input, contacts)
    writeContactsFile(contacts)
    broadcastChiefOfStaff(null, contacts)
    return contacts
  } catch (e) {
    console.error('add-contact fallback error', e)
    return []
  }
})

ipcMain.handle('select-chatgpt-export', async () => {
  const result = await dialog.showOpenDialog({
    title: 'Select ChatGPT conversations.json',
    properties: ['openFile'],
    filters: [{ name: 'ChatGPT conversations export', extensions: ['json'] }]
  })
  return result.canceled ? null : result.filePaths[0]
})

ipcMain.handle('import-chatgpt-history', async (event, { filePath }) => {
  const fs = require('fs')
  try {
    if (!filePath) throw new Error('Select a conversations.json file first')
    const raw = fs.readFileSync(filePath, 'utf8')
    const conversations = JSON.parse(raw.replace(/^\uFEFF/, ''))
    const messages = extractChatGptUserMessages(conversations)
    const summary = summarizeChatGptHistory(messages)
    const profile = readProfileFile()
    const existingMemory = Array.isArray(profile.memory) ? profile.memory : []
    const now = new Date().toISOString()
    const importedMemory = [
      {
        topic: 'chatgpt_import_summary',
        text: `Imported ${summary.count} user messages from ChatGPT history. Top themes: ${summary.topics.map(t => `${t.name} (${t.count})`).join(', ') || 'none detected'}.`,
        createdAt: now
      },
      ...summary.preferenceLines.map(line => ({
        topic: 'chatgpt_import_preference',
        text: line.length > 220 ? `${line.slice(0, 217)}...` : line,
        createdAt: now
      }))
    ]
    const updated = {
      ...profile,
      memory: importedMemory.concat(existingMemory).slice(0, 80),
      chatGptImport: {
        importedAt: now,
        sourceFile: filePath,
        userMessages: summary.count,
        topics: summary.topics
      },
      updatedAt: now
    }
    writeProfileFile(updated)
    broadcastChiefOfStaff(updated)
    return { profile: updated, summary }
  } catch (e) {
    console.error('import-chatgpt-history error', e)
    return { error: e.message || 'Import failed' }
  }
})

ipcMain.handle('read-mobile-bridge', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/mobile-bridge`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    if (!readRuntimeWarningShown) {
      console.warn(`Agent runtime unavailable at ${AGENT_RUNTIME_URL}; reading mobile bridge locally.`)
      readRuntimeWarningShown = true
    }
  }
  try {
    return { config: readMobileBridgeFile(), info: getMobileBridgeInfo() }
  } catch (e) {
    console.error('read-mobile-bridge fallback error', e)
    return { config: { enabled: true, channel: 'iPhone Shortcuts', messages: [] }, info: getMobileBridgeInfo() }
  }
})

ipcMain.handle('update-mobile-bridge', async (event, configUpdate) => {
  try {
    const current = readMobileBridgeFile()
    const next = { ...current, ...configUpdate, updatedAt: new Date().toISOString() }
    writeMobileBridgeFile(next)
    return { config: next, info: getMobileBridgeInfo() }
  } catch (e) {
    console.error('update-mobile-bridge fallback error', e)
    return { config: { enabled: true, channel: 'iPhone Shortcuts', messages: [] }, info: getMobileBridgeInfo() }
  }
})

ipcMain.handle('receive-mobile-message', async (event, input) => {
  try {
    const agents = readAgentsFile()
    const tasks = readTasksFile()
    const bridge = readMobileBridgeFile()
    const task = receiveMobileMessage(input, agents, tasks, bridge)
    writeAgentsFile(agents)
    writeTasksFile(tasks)
    writeMobileBridgeFile(bridge)
    broadcastDashboard(agents, tasks)
    return { agents, tasks, bridge, task, reply: `AgentMajesty created ${task.id} from your iPhone message.` }
  } catch (e) {
    console.error('receive-mobile-message fallback error', e)
    return { error: e.message || 'Mobile message failed' }
  }
})

ipcMain.handle('read-ai-config', async () => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/ai-config`, { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) { /* runtime not running, fallback to file */ }
  try {
    const config = readAiConfigFile()
    const safe = { ...config, apiKey: config.apiKey ? `****${String(config.apiKey).slice(-4)}` : '' }
    return { config: safe, providers: AI_PROVIDER_PRESETS }
  } catch (e) {
    console.error('read-ai-config fallback error', e)
    return { config: { provider: 'ollama', baseUrl: 'http://localhost:11434/v1', apiKey: '', model: 'llama3.2', enabled: false }, providers: AI_PROVIDER_PRESETS }
  }
})

ipcMain.handle('save-ai-config', async (event, update) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/ai-config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update)
    })
    if (res.ok) return await res.json()
  } catch (e) { /* fallback to file */ }
  try {
    const current = readAiConfigFile()
    if (update.apiKey && update.apiKey.startsWith('****')) delete update.apiKey
    const next = { ...current, ...update, updatedAt: new Date().toISOString() }
    writeAiConfigFile(next)
    const safe = { ...next, apiKey: next.apiKey ? `****${String(next.apiKey).slice(-4)}` : '' }
    return { ok: true, config: safe }
  } catch (e) {
    console.error('save-ai-config fallback error', e)
    return { ok: false, error: e.message }
  }
})

ipcMain.handle('test-ai-config', async (event, testConfig) => {
  try {
    const res = await fetch(`${AGENT_RUNTIME_URL}/ai-config/test`, { method: 'POST' })
    if (res.ok) return await res.json()
  } catch (e) { /* fallback to local test */ }
  const cfg = testConfig || readAiConfigFile()
  if (!cfg.enabled || !cfg.baseUrl || !cfg.model) {
    return { ok: false, message: 'AI backend is disabled or not configured.' }
  }
  try {
    const testRes = await fetch(`${cfg.baseUrl.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(cfg.apiKey && !cfg.apiKey.startsWith('****') ? { 'Authorization': `Bearer ${cfg.apiKey}` } : {})
      },
      body: JSON.stringify({
        model: cfg.model,
        messages: [{ role: 'user', content: 'Reply with the single word: ready' }],
        max_tokens: 10
      }),
      signal: AbortSignal.timeout(15000)
    })
    if (!testRes.ok) {
      const text = await testRes.text()
      return { ok: false, message: `AI API returned HTTP ${testRes.status}: ${String(text).slice(0, 200)}` }
    }
    const data = await testRes.json()
    const reply = data.choices?.[0]?.message?.content || '(no response)'
    return { ok: true, message: `Connection successful. Model replied: "${reply.trim()}"` }
  } catch (e) {
    return { ok: false, message: `Connection failed: ${e.message}` }
  }
})

// Relay renderer console messages to the main process stdout for debugging
app.on('web-contents-created', (event, contents) => {
  contents.on('console-message', (event) => {
    const { level, message, lineNumber, sourceId } = event
    console.log(`[RENDERER] level=${level} message=${message} source=${sourceId} line=${lineNumber}`)
  })
})

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
