/**
 * Agent Runner API
 * Spawns the Python LangGraph engine as a subprocess and streams
 * stdout/stderr back to the browser via SSE.
 *
 * Routes:
 *   GET  /api/agent-runner/agents       list all agents from .md files
 *   GET  /api/agent-runner/runs         run history
 *   GET  /api/agent-runner/stream/:id   SSE — live log for a run
 *   GET  /api/agent-runner/skill/:id    read skill file content
 *   POST /api/agent-runner/run          start a new agent run
 *   POST /api/agent-runner/run/:id/stop cancel a running job
 */

const express = require('express')
const path    = require('path')
const fs      = require('fs')
const { spawn } = require('child_process')

const router = express.Router()

// ── Paths ─────────────────────────────────────────────────────────────────
const REPO_ROOT    = path.join(__dirname, '..', '..', '..', '..')
const PYTHON_EXE   = path.join(REPO_ROOT, '.venv', 'Scripts', 'python.exe')
const RUN_PY       = path.join(REPO_ROOT, '.agents', 'agentharness', 'run.py')
const AGENTS_ROOT  = path.join(REPO_ROOT, '.agents', 'agents')
const RUNS_FILE    = path.join(__dirname, '..', '..', 'data', 'agent-runs.json')

// ── In-memory run registry (SSE channels) ─────────────────────────────────
const activeRuns = new Map()   // runId -> { proc, clients: Set<res>, logs: [] }

// ── Helpers ───────────────────────────────────────────────────────────────
function loadRuns() {
  try { return JSON.parse(fs.readFileSync(RUNS_FILE, 'utf8')) }
  catch { return [] }
}

function saveRuns(runs) {
  fs.writeFileSync(RUNS_FILE, JSON.stringify(runs, null, 2))
}

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
}

/** Walk .agents/agents/projects/ and return all agent IDs (from filenames) */
function listAgents() {
  const agents = []
  const projectsDir = path.join(AGENTS_ROOT, 'projects')
  if (!fs.existsSync(projectsDir)) return agents

  const projects = fs.readdirSync(projectsDir, { withFileTypes: true })
    .filter(d => d.isDirectory()).map(d => d.name)

  for (const proj of projects) {
    const projDir = path.join(projectsDir, proj)
    const scan = (dir) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true })
      for (const e of entries) {
        if (e.isDirectory()) {
          scan(path.join(dir, e.name))
        } else if (e.name.endsWith('.md') && !e.name.startsWith('_')) {
          const agentId = e.name.replace('.md', '').replace(/_/g, '-')
          agents.push({ id: agentId, project: proj, file: path.join(dir, e.name) })
        }
      }
    }
    scan(projDir)
  }

  // Also top-level agent files (grants, etc.)
  const topLevel = fs.readdirSync(AGENTS_ROOT, { withFileTypes: true })
    .filter(e => e.isFile() && e.name.endsWith('.md') &&
                 !['roster.md', 'agent_profiles.md'].includes(e.name))
  for (const e of topLevel) {
    const agentId = e.name.replace('.md', '').replace(/_/g, '-')
    agents.push({ id: agentId, project: 'general', file: path.join(AGENTS_ROOT, e.name) })
  }

  return agents.sort((a, b) => a.id.localeCompare(b.id))
}

/** Find a skill file for an agent */
function findSkillFile(agentId) {
  const slug = agentId.replace(/-/g, '_')
  const all  = listAgents()
  const match = all.find(a => a.id === agentId || a.id === slug)
  return match ? match.file : null
}

// ── GET /agents ────────────────────────────────────────────────────────────
router.get('/agents', (req, res) => {
  try {
    res.json(listAgents())
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// ── GET /runs ──────────────────────────────────────────────────────────────
router.get('/runs', (req, res) => {
  res.json(loadRuns().slice().reverse())
})

// ── GET /skill/:agentId ────────────────────────────────────────────────────
router.get('/skill/:agentId', (req, res) => {
  const file = findSkillFile(req.params.agentId)
  if (!file || !fs.existsSync(file)) {
    return res.status(404).json({ error: 'Skill file not found' })
  }
  res.json({ content: fs.readFileSync(file, 'utf8'), file })
})

// ── POST /run ──────────────────────────────────────────────────────────────
router.post('/run', (req, res) => {
  const { agent, project, task, graph = 'reflexion', maxRevisions = 3 } = req.body

  if (!agent || !project || !task) {
    return res.status(400).json({ error: 'agent, project, and task are required' })
  }

  // Check Python exists
  if (!fs.existsSync(PYTHON_EXE)) {
    return res.status(500).json({
      error: `Python venv not found at ${PYTHON_EXE}. Run: py -m venv .venv && pip install -r requirements.txt`
    })
  }

  // Check run.py exists
  if (!fs.existsSync(RUN_PY)) {
    return res.status(500).json({ error: `run.py not found at ${RUN_PY}` })
  }

  const runId = genId()
  const startedAt = new Date().toISOString()

  // Persist as "running"
  const runs = loadRuns()
  runs.push({ id: runId, agent, project, task, graph, maxRevisions, status: 'running', startedAt, score: null, revisions: null, output: null })
  saveRuns(runs)

  // Set up run entry
  activeRuns.set(runId, { proc: null, clients: new Set(), logs: [] })

  // Spawn Python
  const args = [
    RUN_PY,
    '--agent', agent,
    '--project', project,
    '--task', task,
    '--graph', graph,
  ]

  const env = { ...process.env }
  // Load .env from agentharness folder if OPENAI_API_KEY not set
  const envFile = path.join(REPO_ROOT, '.agents', 'agentharness', '.env')
  if (!env.OPENAI_API_KEY && fs.existsSync(envFile)) {
    const lines = fs.readFileSync(envFile, 'utf8').split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [k, ...v] = trimmed.split('=')
        env[k.trim()] = v.join('=').trim()
      }
    }
  }
  // Also check the v2 .env
  const v2Env = path.join(__dirname, '..', '..', '.env')
  if (!env.OPENAI_API_KEY && fs.existsSync(v2Env)) {
    const lines = fs.readFileSync(v2Env, 'utf8').split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [k, ...v] = trimmed.split('=')
        env[k.trim()] = v.join('=').trim()
      }
    }
  }

  if (!env.OPENAI_API_KEY) {
    const run = activeRuns.get(runId)
    const errMsg = 'OPENAI_API_KEY is not set. Add it in Settings or create .agents/agentharness/.env'
    broadcast(runId, { type: 'error', text: errMsg })
    broadcast(runId, { type: 'done', status: 'error', score: null, revisions: null })
    updateRun(runId, { status: 'error', output: errMsg })
    return res.json({ runId, status: 'error', error: errMsg })
  }

  const proc = spawn(PYTHON_EXE, args, {
    cwd: REPO_ROOT,
    env,
    windowsHide: true
  })

  activeRuns.get(runId).proc = proc

  proc.stdout.on('data', chunk => {
    const text = chunk.toString()
    text.split('\n').filter(l => l.trim()).forEach(line => {
      broadcast(runId, { type: 'log', text: line })
    })
  })

  proc.stderr.on('data', chunk => {
    const text = chunk.toString()
    text.split('\n').filter(l => l.trim()).forEach(line => {
      broadcast(runId, { type: 'stderr', text: line })
    })
  })

  proc.on('close', code => {
    const entry = activeRuns.get(runId)
    const logs  = entry ? entry.logs : []

    // Parse score + revision from logs
    let score = null, revisions = null, output = ''
    for (const l of logs) {
      const sm = l.text.match(/Score:\s+([\d.]+)/)
      if (sm) score = parseFloat(sm[1])
      const rm = l.text.match(/Revisions:\s+(\d+)/)
      if (rm) revisions = parseInt(rm[1])
      if (l.type === 'log') output += l.text + '\n'
    }

    const status = code === 0 ? 'complete' : 'error'
    broadcast(runId, { type: 'done', status, score, revisions, code })
    updateRun(runId, { status, score, revisions, output: output.trim(), finishedAt: new Date().toISOString() })

    // Keep logs in memory for 5 min, then clean up
    setTimeout(() => activeRuns.delete(runId), 5 * 60 * 1000)
  })

  res.json({ runId, status: 'running' })
})

// ── POST /run/:id/stop ─────────────────────────────────────────────────────
router.post('/run/:id/stop', (req, res) => {
  const entry = activeRuns.get(req.params.id)
  if (!entry || !entry.proc) return res.status(404).json({ error: 'Run not found or already finished' })
  entry.proc.kill('SIGTERM')
  updateRun(req.params.id, { status: 'stopped', finishedAt: new Date().toISOString() })
  res.json({ ok: true })
})

// ── GET /stream/:id (SSE) ─────────────────────────────────────────────────
router.get('/stream/:id', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders()

  const runId = req.params.id
  const entry = activeRuns.get(runId)

  if (!entry) {
    // Run finished or unknown — send stored logs from DB
    const runs = loadRuns()
    const run  = runs.find(r => r.id === runId)
    if (run) {
      res.write(`data: ${JSON.stringify({ type: 'log', text: run.output || '(no output)' })}\n\n`)
      res.write(`data: ${JSON.stringify({ type: 'done', status: run.status, score: run.score, revisions: run.revisions })}\n\n`)
    } else {
      res.write(`data: ${JSON.stringify({ type: 'error', text: 'Run not found' })}\n\n`)
    }
    res.end()
    return
  }

  // Send buffered logs so far
  for (const item of entry.logs) {
    res.write(`data: ${JSON.stringify(item)}\n\n`)
  }

  // Register as live client
  entry.clients.add(res)

  // Heartbeat
  const hb = setInterval(() => res.write(': heartbeat\n\n'), 15000)

  req.on('close', () => {
    clearInterval(hb)
    const e = activeRuns.get(runId)
    if (e) e.clients.delete(res)
  })
})

// ── Internal helpers ──────────────────────────────────────────────────────
function broadcast(runId, item) {
  const entry = activeRuns.get(runId)
  if (!entry) return
  entry.logs.push(item)
  const payload = `data: ${JSON.stringify(item)}\n\n`
  for (const client of entry.clients) {
    try { client.write(payload) } catch {}
  }
}

function updateRun(runId, patch) {
  const runs = loadRuns()
  const idx  = runs.findIndex(r => r.id === runId)
  if (idx !== -1) {
    Object.assign(runs[idx], patch)
    saveRuns(runs)
  }
}

module.exports = router
