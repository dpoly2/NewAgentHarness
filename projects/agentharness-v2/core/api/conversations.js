const express = require('express')
const router = express.Router()
const { getConversations, getMessages, deleteConversation } = require('../agents/majesty')
const { getDb, generateId } = require('../db/database')

// GET /api/conversations
router.get('/', (req, res) => {
  try {
    res.json(getConversations())
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/conversations
router.post('/', (req, res) => {
  try {
    const db = getDb()
    const id = generateId()
    const ts = new Date().toISOString().replace('T', ' ').slice(0, 19)
    const { slug = 'global', title = 'New Conversation' } = req.body
    db.prepare('INSERT INTO conversations (id, slug, title, created_at, updated_at) VALUES (?,?,?,?,?)').run(id, slug, title, ts, ts)
    // Build response directly — avoids SELECT-after-INSERT fragility in JSON DB
    const conv = db.prepare('SELECT * FROM conversations WHERE id=?').get(id) || { id, slug, title, created_at: ts, updated_at: ts }
    res.json(conv)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/conversations/:id/messages
router.get('/:id/messages', (req, res) => {
  try {
    res.json(getMessages(req.params.id))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// DELETE /api/conversations/:id
router.delete('/:id', (req, res) => {
  try {
    deleteConversation(req.params.id)
    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// PATCH /api/conversations/:id
router.patch('/:id', (req, res) => {
  try {
    const db = getDb()
    const { title, slug } = req.body
    if (title) db.prepare(`UPDATE conversations SET title=? WHERE id=?`).run(title, req.params.id)
    if (slug) db.prepare(`UPDATE conversations SET slug=? WHERE id=?`).run(slug, req.params.id)
    res.json(db.prepare('SELECT * FROM conversations WHERE id=?').get(req.params.id))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
