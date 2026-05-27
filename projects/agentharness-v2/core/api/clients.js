const express = require('express')
const router = express.Router()
const path = require('path')
const fs = require('fs')

const AGENTS_ROOT = path.join(__dirname, '..', '..', '..', '..', '.agents')
const S2T_DIR = path.join(AGENTS_ROOT, 'projects', 's2tdesigns')
const CLIENTS_DIR = path.join(S2T_DIR, 'clients')

function parseClientFolder(slug) {
  const dir = path.join(CLIENTS_DIR, slug)
  const projFile = path.join(dir, 'PROJECT.md')
  if (!fs.existsSync(projFile)) return null

  const text = fs.readFileSync(projFile, 'utf8')
  const nameMatch = text.match(/^# .+?[—\-] Client: (.+)/m)
  const urlMatch = text.match(/\*\*Site URL[^*]*\*\*[^:]*:\s*(?:https?:\/\/)?([^\s\n]+)/i)
  const platformMatch = text.match(/\*\*Platform\*\*:\s*(.+)/i)
  const contactMatch = text.match(/\*\*Contact\*\*:\s*(.+)/i)
  const engagementMatch = text.match(/\*\*Engagement\*\*:\s*(.+)/i)
  const leadMatch = text.match(/\*\*Lead\*\*:\s*(.+)/i)

  // Extract blockers (open checkboxes)
  const blockers = [...text.matchAll(/- \[ \] (.+)/g)].map(m => m[1].trim())

  // Extract status from status table
  const statusRows = [...text.matchAll(/\|([^|]+)\|([^|]+)\|([^|]+)\|/g)]
    .map(m => ({ phase: m[1].trim(), status: m[2].trim(), notes: m[3].trim() }))
    .filter(r => r.status.includes('✅') || r.status.includes('🟡') || r.status.includes('⬜'))

  // Determine overall status label
  const hasActive = statusRows.some(r => r.status.includes('🟡'))
  const allDone = statusRows.length > 0 && statusRows.every(r => r.status.includes('✅'))
  const statusLabel = allDone ? 'complete' : hasActive ? 'active' : 'pending'

  // List available docs
  const docs = fs.readdirSync(dir).filter(f => f.endsWith('.md')).map(f => f.replace('.md', ''))

  return {
    slug,
    name: nameMatch ? nameMatch[1].trim() : slug.toUpperCase(),
    url: urlMatch ? urlMatch[1].replace(/\).*$/, '').replace(/\*.*$/, '').trim() : null,
    platform: platformMatch ? platformMatch[1].trim() : null,
    contact: contactMatch ? contactMatch[1].trim() : null,
    engagement: engagementMatch ? engagementMatch[1].trim() : null,
    lead: leadMatch ? leadMatch[1].trim() : null,
    status: statusLabel,
    blockers,
    phases: statusRows,
    docs,
    raw: text
  }
}

// GET /api/clients — all S2T clients
router.get('/', (req, res) => {
  try {
    const clients = []
    if (!fs.existsSync(CLIENTS_DIR)) return res.json([])
    const slugs = fs.readdirSync(CLIENTS_DIR, { withFileTypes: true })
      .filter(d => d.isDirectory()).map(d => d.name)
    for (const slug of slugs) {
      const client = parseClientFolder(slug)
      if (client) clients.push(client)
    }
    // Sort: active first, then pending
    clients.sort((a, b) => {
      const order = { active: 0, pending: 1, complete: 2 }
      return (order[a.status] ?? 3) - (order[b.status] ?? 3)
    })
    res.json(clients)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/clients/:slug — single client
router.get('/:slug', (req, res) => {
  try {
    const client = parseClientFolder(req.params.slug)
    if (!client) return res.status(404).json({ error: 'Client not found' })
    res.json(client)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/clients/:slug/docs/:doc — read a doc file
router.get('/:slug/docs/:doc', (req, res) => {
  try {
    const file = path.join(CLIENTS_DIR, req.params.slug, req.params.doc + '.md')
    if (!fs.existsSync(file)) return res.status(404).json({ error: 'Not found' })
    res.json({ content: fs.readFileSync(file, 'utf8') })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
