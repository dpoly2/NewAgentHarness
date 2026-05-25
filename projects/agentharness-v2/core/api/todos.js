const express = require('express')
const router = express.Router()
const { getDb, generateId } = require('../db/database')
const { createTodo } = require('../agents/engine')

// GET /api/todos
router.get('/', (req, res) => {
  try {
    const { status, project_slug, priority } = req.query
    const db = getDb()
    let query = 'SELECT * FROM todos'
    const params = []
    const where = []
    if (status) { where.push('status=?'); params.push(status) }
    if (project_slug && project_slug !== 'global') { where.push('project_slug=?'); params.push(project_slug) }
    if (priority) { where.push('priority=?'); params.push(priority) }
    if (where.length) query += ' WHERE ' + where.join(' AND ')
    query += ` ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, due_date ASC NULLS LAST`
    res.json(db.prepare(query).all(...params))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/todos
router.post('/', (req, res) => {
  try {
    const { title, description, priority, projectSlug, dueDate, tags } = req.body
    if (!title) return res.status(400).json({ error: 'title required' })
    const todo = createTodo({ title, description, priority, projectSlug, dueDate, tags, source: 'user' })
    res.json(todo)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// PATCH /api/todos/:id
router.patch('/:id', (req, res) => {
  try {
    const db = getDb()
    const { title, description, status, priority, dueDate, projectSlug } = req.body
    const fields = []
    const params = []
    if (title !== undefined) { fields.push('title=?'); params.push(title) }
    if (description !== undefined) { fields.push('description=?'); params.push(description) }
    if (status !== undefined) { fields.push('status=?'); params.push(status) }
    if (priority !== undefined) { fields.push('priority=?'); params.push(priority) }
    if (dueDate !== undefined) { fields.push('due_date=?'); params.push(dueDate) }
    if (projectSlug !== undefined) { fields.push('project_slug=?'); params.push(projectSlug) }
    if (!fields.length) return res.status(400).json({ error: 'no fields to update' })
    fields.push(`updated_at=datetime('now')`)
    params.push(req.params.id)
    db.prepare(`UPDATE todos SET ${fields.join(',')} WHERE id=?`).run(...params)
    res.json(db.prepare('SELECT * FROM todos WHERE id=?').get(req.params.id))
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// DELETE /api/todos/:id
router.delete('/:id', (req, res) => {
  try {
    const db = getDb()
    db.prepare('DELETE FROM todos WHERE id=?').run(req.params.id)
    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/todos/summary — counts by project
router.get('/summary', (req, res) => {
  try {
    const db = getDb()
    res.json(db.prepare(`
      SELECT project_slug, COUNT(*) as total,
        SUM(CASE WHEN status NOT IN ('done','cancelled') THEN 1 ELSE 0 END) as open,
        SUM(CASE WHEN priority IN ('urgent','high') AND status NOT IN ('done','cancelled') THEN 1 ELSE 0 END) as urgent
      FROM todos GROUP BY project_slug
    `).all())
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
