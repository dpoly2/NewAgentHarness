const express = require('express')
const router = express.Router()
const { loadAgentProfile } = require('../roster/parser')
const { saveConfig, getConfig } = require('../agents/llm')
const { getDb } = require('../db/database')
const { saveConfig: savePushConfig, getConfig: getPushConfig, sendPush } = require('../notifications/push')
const path = require('path')
const fs = require('fs')

// GET /api/settings/ai
router.get('/ai', (req, res) => {
  try {
    const c = getConfig()
    res.json({ ...c, apiKey: c.apiKey ? '***' : '' })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/ai
router.post('/ai', (req, res) => {
  try {
    const config = saveConfig(req.body)
    res.json({ ...config, apiKey: config.apiKey ? '***' : '' })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/settings/profile
router.get('/profile', (req, res) => {
  try {
    const profilePath = path.join(__dirname, '..', '..', 'data', 'profile.json')
    if (!fs.existsSync(profilePath)) return res.json({})
    res.json(JSON.parse(fs.readFileSync(profilePath, 'utf8')))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/profile
router.post('/profile', (req, res) => {
  try {
    const profilePath = path.join(__dirname, '..', '..', 'data', 'profile.json')
    const dir = path.dirname(profilePath)
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(profilePath, JSON.stringify(req.body, null, 2))
    res.json(req.body)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/settings/agents/:id/profile
router.get('/agents/:id/profile', (req, res) => {
  try {
    const content = loadAgentProfile(req.params.id)
    if (!content) return res.status(404).json({ error: 'Agent profile not found' })
    res.json({ id: req.params.id, content })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/settings/notifications
router.get('/notifications', (req, res) => {
  try {
    const db = getDb()
    res.json(db.prepare(`SELECT * FROM notifications ORDER BY created_at DESC LIMIT 50`).all())
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/notifications/read-all
router.post('/notifications/read-all', (req, res) => {
  try {
    const db = getDb()
    db.prepare(`UPDATE notifications SET read=1`).run()
    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// ─── Push Notifications ────────────────────────────────────────────────────

// GET /api/settings/push
router.get('/push', (req, res) => {
  try {
    const config = getPushConfig()
    // Mask secrets
    res.json({
      ...config,
      pushoverToken: config.pushoverToken ? '***' : '',
      pushoverUser: config.pushoverUser ? config.pushoverUser : ''
    })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/push
router.post('/push', (req, res) => {
  try {
    const updates = req.body
    // Don't overwrite token with masked value
    if (updates.pushoverToken === '***') delete updates.pushoverToken
    const config = savePushConfig(updates)
    res.json({ ...config, pushoverToken: config.pushoverToken ? '***' : '' })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/push/test — send a test notification
router.post('/push/test', async (req, res) => {
  try {
    const config = getPushConfig()
    if (!config.enabled) return res.status(400).json({ error: 'Push notifications are disabled. Enable them first.' })
    await sendPush('AgentHarness is connected! Your Apple Watch will receive agent alerts.', 'Test Notification', 'high', 'bell')
    res.json({ ok: true, message: 'Test notification sent' })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/settings/briefings — list daily briefs
router.get('/briefings', (req, res) => {
  try {
    const db = getDb()
    res.json(db.prepare(`SELECT * FROM daily_briefs ORDER BY generated_at DESC LIMIT 10`).all())
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/settings/briefings/generate — trigger now
router.post('/briefings/generate', async (req, res) => {
  try {
    const { generateMorningBrief } = require('../agents/majesty')
    const profilePath = path.join(__dirname, '..', '..', 'data', 'profile.json')
    let profile = {}
    try { if (fs.existsSync(profilePath)) profile = JSON.parse(fs.readFileSync(profilePath, 'utf8')) } catch (e) {}
    const brief = await generateMorningBrief(profile)
    res.json(brief)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
