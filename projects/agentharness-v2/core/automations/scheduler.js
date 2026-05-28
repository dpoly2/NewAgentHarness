/**
 * Automation Scheduler — node-cron based task runner
 */
const cron = require('node-cron')
const { enqueueTask, createNotification } = require('../agents/engine')
const { loadRoster } = require('../roster/parser')
const { generateMorningBrief } = require('../agents/majesty')
const { getDb } = require('../db/database')

const jobs = []

function startScheduler(profile = {}) {
  console.log('[scheduler] Starting automation scheduler...')

  // Morning Briefing — 7:00 AM CT daily
  schedule('0 7 * * *', 'morning-briefing', 'Morning Briefing', async () => {
    console.log('[scheduler] Generating morning briefing...')
    await generateMorningBrief(profile)
  })

  // Daily Email Digest — 8:00 AM CT
  schedule('0 8 * * *', 'email-digest', 'Daily Email Digest', async () => {
    await enqueueTask({
      title: 'Daily Email Digest',
      description: 'Triage all connected email accounts, summarize important messages, surface action items and follow-ups. Create todos for any items needing attention.',
      agentId: 'productivity-coordinator',
      projectSlug: 'personal'
    })
  })

  // Weekly Grant Sweep — Monday 8:00 AM CT
  schedule('0 8 * * 1', 'grant-sweep', 'Weekly Grant Sweep', async () => {
    await enqueueTask({
      title: 'Weekly Grant Research Sweep',
      description: 'Search for new grant opportunities for XFTC (501c3 track club), PBS Foundation (fraternity college pathways 501c3), Nutrue Apparel (minority-owned business), and YEPC (community sports facility). Check EDA, HUD CDBG, USATF, FHWA TAP, and state of Texas programs. Create todos for any promising leads found.',
      agentId: 'grants-research-agent',
      projectSlug: 'global'
    })
  })

  // Open Items Sync — Monday 9:00 AM CT (read roster.md, sync open items to todos)
  schedule('0 9 * * 1', 'open-items-sync', 'Open Items Sync', async () => {
    syncRosterOpenItems()
  })

  // XFTC Signup Check — every 4 hours
  schedule('0 */4 * * *', 'xftc-signup-check', 'XFTC Signup Check', async () => {
    await enqueueTask({
      title: 'XFTC Signup & Payment Check',
      description: 'Check the XFTC WordPress site for new athlete signups, pending payments, and registration activity. Report counts and any issues found.',
      agentId: 'xftc-devops-agent',
      projectSlug: 'xftc'
    })
  })

  console.log(`[scheduler] ${jobs.length} automations scheduled`)
}

function schedule(cronExpr, id, name, fn) {
  if (!cron.validate(cronExpr)) {
    console.warn(`[scheduler] Invalid cron for ${name}: ${cronExpr}`)
    return
  }
  const job = cron.schedule(cronExpr, async () => {
    console.log(`[scheduler] Running: ${name}`)
    try {
      await fn()
      logRun(id)
    } catch (e) {
      console.error(`[scheduler] ${name} failed:`, e.message)
    }
  }, { timezone: 'America/Chicago' })
  jobs.push({ id, name, cronExpr, job })
}

function logRun(automationId) {
  const db = getDb()
  db.prepare(`UPDATE automations SET last_run=datetime('now') WHERE id=?`).run(automationId)
}

function syncRosterOpenItems() {
  const roster = loadRoster()
  if (!roster?.openItems?.length) return
  const db = getDb()
  let created = 0
  for (const item of roster.openItems) {
    const priority = item.priority.includes('🔴') ? 'urgent' : item.priority.includes('🟡') ? 'high' : 'medium'
    // Skip if a todo with same title already exists
    const existing = db.prepare(`SELECT id FROM todos WHERE title=? AND status NOT IN ('done','cancelled') LIMIT 1`).get(item.item)
    if (!existing) {
      const { createTodo } = require('../agents/engine')
      createTodo({
        title: item.item,
        description: `From roster.md open items. Project: ${item.project}`,
        priority,
        dueDate: item.deadline === 'ASAP' ? null : item.deadline,
        projectSlug: slugify(item.project),
        source: 'automation',
        tags: ['open-item', 'roster']
      })
      created++
    }
  }
  if (created > 0) createNotification(`Synced ${created} new open items from roster`, 'info', null, 'low')
}

function slugify(name) {
  const map = { 'XFTC': 'xftc', 'YEPC': 'yepc', 'Elevation': 'elevation', 'PBS': 'pbs-foundation', 'Nutrue': 'nutrue', 'SmithCap': 'smithcap', 'S2T': 's2tdesigns', 'Personal': 'personal', 'Finance': 'finance', 'Solar': 'solar-repair', 'Social': 'social-media', 'Ministry': 'ministry' }
  for (const [key, val] of Object.entries(map)) {
    if (name.includes(key)) return val
  }
  return 'global'
}

function getScheduledJobs() {
  return jobs.map(({ id, name, cronExpr }) => ({ id, name, cronExpr }))
}

function stopScheduler() {
  jobs.forEach(({ job }) => job.stop())
}

module.exports = { startScheduler, stopScheduler, getScheduledJobs, syncRosterOpenItems }
