const express = require('express')
const router = express.Router()
const { getDb, generateId } = require('../db/database')
const { enqueueTask, getQueueStatus } = require('../agents/engine')

// GET /api/tasks — queue status
router.get('/', (req, res) => {
  try {
    const { status, project_slug } = req.query
    const db = getDb()
    let query = 'SELECT * FROM agent_tasks'
    const params = []
    const where = []
    if (status) { where.push('status=?'); params.push(status) }
    if (project_slug) { where.push('project_slug=?'); params.push(project_slug) }
    if (where.length) query += ' WHERE ' + where.join(' AND ')
    query += ' ORDER BY created_at DESC LIMIT 50'
    res.json(db.prepare(query).all(...params))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/tasks/queue
router.get('/queue', (req, res) => {
  try { res.json(getQueueStatus()) }
  catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/tasks — manually queue a task
router.post('/', async (req, res) => {
  try {
    const { title, description, agentId, projectSlug } = req.body
    if (!title || !agentId) return res.status(400).json({ error: 'title and agentId required' })
    const task = await enqueueTask({ title, description, agentId, projectSlug })
    res.json(task)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/tasks/:id
router.get('/:id', (req, res) => {
  try {
    const db = getDb()
    const task = db.prepare('SELECT * FROM agent_tasks WHERE id=?').get(req.params.id)
    if (!task) return res.status(404).json({ error: 'not found' })
    res.json(task)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// DELETE /api/tasks/:id — cancel a task
router.delete('/:id', (req, res) => {
  try {
    const db = getDb()
    db.prepare(`UPDATE agent_tasks SET status='cancelled', updated_at=datetime('now') WHERE id=? AND status='queued'`).run(req.params.id)
    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
