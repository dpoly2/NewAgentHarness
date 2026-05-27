/**
 * AgentHarness v2 — Core Server
 * Express + socket.io + SQLite
 * Runs on :4000, serves API + WebSocket
 */
require('dotenv').config()
const express = require('express')
const http = require('http')
const path = require('path')
const fs = require('fs')
const cors = require('cors')
const helmet = require('helmet')
const rateLimit = require('express-rate-limit')
const os = require('os')
const { patchConsole } = require('./services/logger')
patchConsole() // redirect console.* to rotating log files

function getLanIP() {
  const nets = os.networkInterfaces()
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) return net.address
    }
  }
  return null
}

const { Server } = require('socket.io')
const { getDb, generateId } = require('./db/database')
const { setIO } = require('./agents/engine')
const { chat } = require('./agents/majesty')
const { startScheduler } = require('./automations/scheduler')
const { requireAuth, getAccessToken } = require('./middleware/auth')
const { validateChat } = require('./middleware/validate')
const { startDdns } = require('./services/ddns')

const PORT = process.env.PORT || 4000
const WEB_DIST = path.join(__dirname, '..', 'web', 'dist')
const PROFILE_PATH = path.join(__dirname, '..', 'data', 'profile.json')

// Build Express app
const app = express()
const server = http.createServer(app)

// ─── CORS configuration ───────────────────────────────────────────
const allowedOrigins = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim())
const corsOptions = allowedOrigins.includes('*')
  ? { origin: '*' }
  : { origin: (origin, cb) => {
      if (!origin || allowedOrigins.includes(origin)) cb(null, true)
      else cb(new Error('CORS: origin not allowed'))
    }, credentials: true }

// socket.io
const io = new Server(server, {
  cors: allowedOrigins.includes('*') ? { origin: '*', methods: ['GET', 'POST'] } : { origin: allowedOrigins, credentials: true }
})
setIO(io)

// ─── Security middleware ──────────────────────────────────────────
app.use(helmet({
  contentSecurityPolicy: false, // disabled to allow React app to load
  crossOriginEmbedderPolicy: false
}))
app.use(cors(corsOptions))
app.use(express.json({ limit: '2mb' }))

// ─── Rate limiting ────────────────────────────────────────────────
const globalLimiter = rateLimit({ windowMs: 60 * 1000, max: 200, standardHeaders: true, legacyHeaders: false, message: { error: 'Too many requests, slow down.' } })
const chatLimiter = rateLimit({ windowMs: 60 * 1000, max: 30, message: { error: 'Chat rate limit exceeded.' } })
const taskLimiter = rateLimit({ windowMs: 60 * 1000, max: 20, message: { error: 'Task rate limit exceeded.' } })
app.use(globalLimiter)

// ─── API Routes ──────────────────────────────────────────────────
// Public health check (no auth needed)
app.get('/api/health', (req, res) => {
  const db = getDb()
  const convCount = db.prepare('SELECT COUNT(*) as c FROM conversations').get().c
  const taskCount = db.prepare(`SELECT COUNT(*) as c FROM agent_tasks WHERE status='running'`).get().c
  const todoCount = db.prepare(`SELECT COUNT(*) as c FROM todos WHERE status NOT IN ('done','cancelled')`).get().c
  const authEnabled = true // login always required for remote access
  res.json({ status: 'ok', version: '2.0.0', conversations: convCount, runningTasks: taskCount, openTodos: todoCount, authEnabled })
})

// Auth routes — public (no token required for login)
app.use('/api/auth', require('./api/auth').router)

// All other API routes require authentication (if configured)
app.use('/api', requireAuth)
app.use('/api/conversations', require('./api/conversations'))
app.use('/api/tasks', taskLimiter, require('./api/tasks'))
app.use('/api/todos', require('./api/todos'))
app.use('/api/projects', require('./api/projects'))
app.use('/api/clients', require('./api/clients'))
app.use('/api/settings', require('./api/settings'))

// ─── Chat Endpoint (streaming SSE) ───────────────────────────────
app.post('/api/chat', chatLimiter, validateChat, async (req, res) => {
  const { conversationId, message, projectSlug } = req.body
  if (!message) return res.status(400).json({ error: 'message required' })
  if (!conversationId) return res.status(400).json({ error: 'conversationId required' })

  let profile = {}
  try { if (fs.existsSync(PROFILE_PATH)) profile = JSON.parse(fs.readFileSync(PROFILE_PATH, 'utf8')) } catch (e) {}

  // Check if client wants SSE streaming
  const wantsStream = req.headers['accept'] === 'text/event-stream'

  if (wantsStream) {
    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')

    await chat({
      conversationId,
      userMessage: message,
      projectSlug: projectSlug || null,
      profile,
      onChunk: (chunk) => {
        res.write(`data: ${JSON.stringify({ chunk })}\n\n`)
      }
    })
    res.write(`data: ${JSON.stringify({ done: true })}\n\n`)
    res.end()
  } else {
    const result = await chat({ conversationId, userMessage: message, projectSlug, profile })
    res.json(result)
  }
})

// ─── Serve React web app (production) ─────────────────────────────
if (fs.existsSync(WEB_DIST)) {
  app.use(express.static(WEB_DIST))
  app.get('*', (req, res) => {
    if (req.path.startsWith('/api')) return res.status(404).json({ error: 'not found' })
    res.sendFile(path.join(WEB_DIST, 'index.html'))
  })
}

// ─── WebSocket Events ──────────────────────────────────────────────
io.on('connection', (socket) => {
  console.log(`[ws] Client connected: ${socket.id}`)

  // Send initial state on connect
  try {
    const db = getDb()
    socket.emit('init', {
      runningTasks: db.prepare(`SELECT * FROM agent_tasks WHERE status IN ('running','queued') ORDER BY created_at DESC`).all(),
      recentTodos: db.prepare(`SELECT * FROM todos WHERE status NOT IN ('done','cancelled') ORDER BY created_at DESC LIMIT 20`).all(),
      unreadNotifs: db.prepare(`SELECT COUNT(*) as c FROM notifications WHERE read=0`).get().c,
      latestBrief: db.prepare(`SELECT * FROM daily_briefs ORDER BY generated_at DESC LIMIT 1`).get()
    })
  } catch (e) { /* db may not be ready */ }

  socket.on('disconnect', () => {
    console.log(`[ws] Client disconnected: ${socket.id}`)
  })

  // Client can request mark-notification-read
  socket.on('mark-read', (id) => {
    try {
      const db = getDb()
      db.prepare(`UPDATE notifications SET read=1 WHERE id=?`).run(id)
    } catch (e) { /* ignore */ }
  })
})

// ─── Bootstrap ────────────────────────────────────────────────────
async function bootstrap() {
  // Initialize DB
  try {
    getDb()
    console.log('[db] SQLite initialized')
  } catch (e) {
    console.warn('[db] SQLite unavailable, running without persistence:', e.message)
  }

  // Seed automations table
  try {
    const db = getDb()
    const automations = [
      { id: 'morning-briefing', name: 'Morning Briefing', schedule: '0 7 * * *', enabled: 1 },
      { id: 'email-digest', name: 'Daily Email Digest', schedule: '0 8 * * *', enabled: 1 },
      { id: 'grant-sweep', name: 'Weekly Grant Sweep', schedule: '0 8 * * 1', enabled: 1 },
      { id: 'open-items-sync', name: 'Open Items Sync', schedule: '0 9 * * 1', enabled: 1 },
      { id: 'xftc-signup-check', name: 'XFTC Signup Check', schedule: '0 */4 * * *', enabled: 1 }
    ]
    for (const a of automations) {
      db.prepare(`INSERT OR IGNORE INTO automations (id, name, schedule, enabled) VALUES (?,?,?,?)`).run(a.id, a.name, a.schedule, a.enabled)
    }
  } catch (e) { /* ignore */ }

  // Load profile for scheduler
  let profile = {}
  try { if (fs.existsSync(PROFILE_PATH)) profile = JSON.parse(fs.readFileSync(PROFILE_PATH, 'utf8')) } catch (e) {}

  // Start automation scheduler
  try {
    startScheduler(profile)
  } catch (e) {
    console.warn('[scheduler] Could not start:', e.message)
  }

  // Start ClouDNS DDNS updater (if configured)
  try {
    startDdns()
  } catch (e) {
    console.warn('[ddns] Could not start:', e.message)
  }

  // Start server — bind to 0.0.0.0 so it's reachable on the local network
  const HOST = process.env.HOST || '0.0.0.0'
  server.listen(PORT, HOST, () => {
    const lanIP = getLanIP()
    const accessToken = getAccessToken()
    console.log(`\n╔══════════════════════════════════════════╗`)
    console.log(`║  AgentHarness v2 Core Server              ║`)
    console.log(`║  Local:   http://localhost:${PORT}              ║`)
    if (lanIP) {
      console.log(`║  Network: http://${lanIP}:${PORT}`.padEnd(44) + '║')
    }
    console.log(`╚══════════════════════════════════════════╝`)
    if (!accessToken) {
      console.warn(`\n⚠️  WARNING: No ACCESS_TOKEN set. API is open to anyone on the network.`)
      console.warn(`   Set ACCESS_TOKEN in .env to secure this server before internet exposure.\n`)
    } else {
      console.log(`\n🔒 Authentication enabled (Bearer token)\n`)
    }
  })
}

// ─── Graceful shutdown ─────────────────────────────────────────────
function shutdown(signal) {
  console.log(`\n[server] ${signal} received, shutting down gracefully...`)
  server.close(() => {
    console.log('[server] HTTP server closed.')
    process.exit(0)
  })
  setTimeout(() => { console.error('[server] Forced shutdown.'); process.exit(1) }, 10000)
}
process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('SIGINT', () => shutdown('SIGINT'))
process.on('unhandledRejection', (reason) => console.error('[server] Unhandled rejection:', reason))
process.on('uncaughtException', (err) => { console.error('[server] Uncaught exception:', err); process.exit(1) })

bootstrap().catch(console.error)

module.exports = { app, server, io }
