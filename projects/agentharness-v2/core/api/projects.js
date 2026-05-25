const express = require('express')
const router = express.Router()
const { loadRoster, listProjectDocs, readProjectDoc, loadAgentProfile } = require('../roster/parser')
const { getDb } = require('../db/database')

// GET /api/projects — all projects from roster
router.get('/', (req, res) => {
  try {
    const roster = loadRoster()
    if (!roster) return res.json({ projects: [], sharedAgents: [], openItems: [], automations: [] })
    res.json(roster)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/projects/:slug/docs
router.get('/:slug/docs', (req, res) => {
  try {
    const docs = listProjectDocs(req.params.slug)
    res.json(docs)
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/projects/:slug/docs/:filename
router.get('/:slug/docs/:filename', (req, res) => {
  try {
    const content = readProjectDoc(req.params.slug, req.params.filename)
    if (content === null) return res.status(404).json({ error: 'not found' })
    res.json({ content })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/projects/:slug/summary — stats for one project
router.get('/:slug/summary', (req, res) => {
  try {
    const db = getDb()
    const slug = req.params.slug
    const tasks = db.prepare(`SELECT status, COUNT(*) as count FROM agent_tasks WHERE project_slug=? GROUP BY status`).all(slug)
    const todos = db.prepare(`SELECT priority, COUNT(*) as count FROM todos WHERE project_slug=? AND status NOT IN ('done','cancelled') GROUP BY priority`).all(slug)
    const recentTasks = db.prepare(`SELECT * FROM agent_tasks WHERE project_slug=? ORDER BY updated_at DESC LIMIT 5`).all(slug)
    res.json({ slug, tasks, todos, recentTasks })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = router
