const path = require('path')
const fs = require('fs')

const AGENTS_ROOT = path.join(__dirname, '..', '..', '..', '..')

function parseRosterMarkdown(content) {
  const lastUpdatedMatch = content.match(/\*\*Last Updated:\*\*\s*(.+)/)
  const lastUpdated = lastUpdatedMatch ? lastUpdatedMatch[1].trim() : ''
  const coordinatorMatch = content.match(/\*\*Coordinator:\*\*\s*(.+)/)
  const coordinator = coordinatorMatch ? coordinatorMatch[1].trim() : ''

  const projects = []
  const SLUG_MAP = {
    'XFTC Website & Plugin': 'xftc',
    'YEPC': 'yepc',
    'The Elevation ATX': 'elevation',
    'PBS Foundation': 'pbs-foundation',
    'Nutrue Apparel': 'nutrue',
    'Smith Capital Properties': 'smithcap',
    'S2T Designs Agency': 's2tdesigns',
    'Personal Productivity': 'personal'
  }
  const ICON_MAP = { xftc:'⚽', yepc:'🏟️', elevation:'✨', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', personal:'👤', finance:'💰', 'solar-repair':'☀️', 'social-media':'📱', ministry:'✝️', 'sigma-signal':'📰' }
  const EXTRA_SLUG_MAP = { 'SMITHCAP FINANCIAL': 'finance', 'SOLAR': 'solar-repair', 'S2T DESIGNS SOCIAL': 'social-media', 'MINISTRY': 'ministry', 'SIGMA SIGNAL': 'sigma-signal' }
  const NAME_MAP = { finance: 'SmithCap FMO', 'solar-repair': 'Solar Repair Co.', 'social-media': 'S2T Social Media', ministry: 'Ministry & Preaching', 'sigma-signal': 'The Sigma Signal' }

  const indexSection = content.match(/## [^\n]*PROJECT INDEX([\s\S]*?)\r?\n---\r?\n/)
  if (indexSection) {
    indexSection[1].split('\n').filter(l => /^\|\s*\d/.test(l)).forEach(row => {
      const cols = row.split('|').map(c => c.trim()).filter(Boolean)
      if (cols.length >= 4) {
        const id = parseInt(cols[0])
        const name = cols[1]
        const leadAgent = cols[2]
        const statusRaw = cols[4] || cols[3] || ''
        const status = statusRaw.includes('🟢') ? 'active' : statusRaw.includes('🔴') ? 'blocked' : 'in-progress'
        let slug = 'project-' + id
        for (const [key, val] of Object.entries(SLUG_MAP)) {
          if (name.toUpperCase().includes(key.toUpperCase())) { slug = val; break }
        }
        projects.push({ id, slug, name, icon: ICON_MAP[slug] || '📁', leadAgent, leadRole: '', status, statusLabel: statusRaw.replace(/[🟢🟡🔴]/g, '').trim(), specialists: [], helpers: [] })
      }
    })
  }

  // Also capture ## PROJECT N / ## Project N sections not in the INDEX (projects 9+)
  const projectSectionRe = /## project (\d+)\s*[—–-]\s*([^\n]+)/gi
  let psMatch
  while ((psMatch = projectSectionRe.exec(content)) !== null) {
    const id = parseInt(psMatch[1])
    if (projects.some(p => p.id === id)) continue
    const rawTitle = psMatch[2].trim()
    let slug = 'project-' + id
    for (const [key, val] of Object.entries(EXTRA_SLUG_MAP)) {
      if (rawTitle.toUpperCase().includes(key)) { slug = val; break }
    }
    if (slug === 'project-' + id) slug = rawTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30)
    projects.push({ id, slug, name: NAME_MAP[slug] || rawTitle, icon: ICON_MAP[slug] || '📁', leadAgent: '', leadRole: '', status: 'in-progress', statusLabel: 'Active', specialists: [], helpers: [] })
  }
  projects.sort((a, b) => a.id - b.id)

  for (const proj of projects) {
    const re = new RegExp(`## project ${proj.id} [\\s\\S]*?(?=\\r?\\n---\\r?\\n|\\n## project \\d|\\n## |$)`, 'i')
    const m = content.match(re)
    if (!m) continue
    const block = m[0]
    // Inline bold lead (projects 1-8): **agent** — role
    const leadLine = block.match(/\*\*([^*]+)\*\*\s*—\s*(.+)/)
    if (leadLine) {
      if (!proj.leadAgent) proj.leadAgent = leadLine[1].trim()
      proj.leadRole = leadLine[2].trim()
    }
    // ### Lead section (projects 9+)
    const leadSection = block.match(/### Lead\s*\n\*\*([^*]+)\*\*\s*—\s*(.+)/)
    if (leadSection) {
      if (!proj.leadAgent) proj.leadAgent = leadSection[1].trim()
      proj.leadRole = leadSection[2].trim()
    }

    const specBlock = block.match(/### Specialist Agents([\s\S]*?)(?=###|$)/)
    if (specBlock) {
      specBlock[1].split('\n').filter(l => /^\|\s*[a-zA-Z]/.test(l)).forEach(row => {
        const cols = row.split('|').map(c => c.trim()).filter(Boolean)
        if (cols.length >= 2) proj.specialists.push({ name: cols[0], role: cols[1], responsibilities: cols[2] || '', type: 'specialist' })
      })
    }
    const helperBlock = block.match(/### Helper Agents[\s\S]*?(?=###|$)/)
    if (helperBlock) {
      helperBlock[0].split('\n').filter(l => /^\|\s*[a-zA-Z]/.test(l)).forEach(row => {
        const cols = row.split('|').map(c => c.trim()).filter(Boolean)
        if (cols.length >= 3) proj.helpers.push({ name: cols[0], assignedBy: cols[1], taskType: cols[2], type: 'helper' })
      })
    }
    const emailBlock = block.match(/### Email Agents([\s\S]*?)(?=###|$)/)
    if (emailBlock) {
      emailBlock[1].split('\n').filter(l => /^\|\s*[a-zA-Z]/.test(l)).forEach(row => {
        const cols = row.split('|').map(c => c.trim()).filter(Boolean)
        if (cols.length >= 2) proj.specialists.push({ name: cols[0], role: cols[1], status: cols[2] || '', type: 'email-agent' })
      })
    }
  }

  const sharedAgents = []
  const sharedMatch = content.match(/## [^\n]*SHARED[^\n]*\n([\s\S]*?)(?=\r?\n---\r?\n|\n## )/)
  if (sharedMatch) {
    sharedMatch[1].split('\n').filter(l => /^\|\s*[a-zA-Z]/.test(l)).forEach(row => {
      const cols = row.split('|').map(c => c.trim()).filter(Boolean)
      if (cols.length >= 3) sharedAgents.push({ agentName: cols[0], specialty: cols[1], projectsServed: cols[2].split(',').map(p => p.trim()) })
    })
  }

  const automations = []
  const autoMatch = content.match(/## [^\n]*ACTIVE AUTOMATIONS([\s\S]*?)(?=\r?\n---\r?\n|\n## [^\n]*OPEN ITEMS)/)
  if (autoMatch) {
    autoMatch[1].split('\n').filter(l => /^\|\s*[A-Za-z]/.test(l)).forEach(row => {
      const cols = row.split('|').map(c => c.trim()).filter(Boolean)
      if (cols.length >= 3) {
        const active = cols[2].includes('✅')
        automations.push({ name: cols[0], schedule: cols[1], active, statusNote: cols[2].replace('✅', '').replace('⬜', '').trim() })
      }
    })
  }

  const openItems = []
  const openMatch = content.match(/## [^\n]*OPEN ITEMS[\s\S]*$/)
  if (openMatch) {
    openMatch[0].split('\n').filter(l => /^\|[^|]*[🔴🟡🟢]/.test(l)).forEach(row => {
      const cols = row.split('|').map(c => c.trim()).filter(Boolean)
      if (cols.length >= 4) openItems.push({ priority: cols[0], item: cols[1], project: cols[2], deadline: cols[3] })
    })
  }

  return { lastUpdated, coordinator, projects, sharedAgents, automations, openItems }
}

function loadRoster() {
  try {
    const rosterPath = path.join(AGENTS_ROOT, '.agents', 'agents', 'roster.md')
    if (!fs.existsSync(rosterPath)) return null
    const content = fs.readFileSync(rosterPath, 'utf8').replace(/^\uFEFF/, '')
    return parseRosterMarkdown(content)
  } catch (e) {
    console.error('[roster] parse error:', e.message)
    return null
  }
}

function loadAgentProfile(agentId) {
  const searchDirs = [
    path.join(AGENTS_ROOT, '.agents', 'agents', 'projects'),
    path.join(AGENTS_ROOT, '.agents', 'agents'),
    path.join(AGENTS_ROOT, 'agents')
  ]
  const variants = [agentId, agentId.replace(/-/g, '_'), agentId.replace(/_/g, '-')]
  for (const dir of searchDirs) {
    if (!fs.existsSync(dir)) continue
    for (const v of variants) {
      const candidates = [`${v}.md`, `${v.toLowerCase()}.md`]
      for (const c of candidates) {
        const fp = path.join(dir, c)
        if (fs.existsSync(fp)) return fs.readFileSync(fp, 'utf8')
      }
    }
    // Search recursively one level
    try {
      const subdirs = fs.readdirSync(dir, { withFileTypes: true }).filter(d => d.isDirectory())
      for (const sub of subdirs) {
        for (const v of variants) {
          const fp = path.join(dir, sub.name, `${v}.md`)
          if (fs.existsSync(fp)) return fs.readFileSync(fp, 'utf8')
        }
      }
    } catch (e) { /* ignore */ }
  }
  return null
}

function listProjectDocs(slug) {
  const pathOverrides = { xftc: 'xftc-redevelopment', elevation: 'rowdy-crown' }
  const folder = pathOverrides[slug] || slug
  const docPath = path.join(AGENTS_ROOT, '.agents', 'projects', folder)
  if (!fs.existsSync(docPath)) return []
  return fs.readdirSync(docPath).filter(f => f.endsWith('.md')).map(f => ({ name: f, slug, folder }))
}

function readProjectDoc(slug, filename) {
  const pathOverrides = { xftc: 'xftc-redevelopment', elevation: 'rowdy-crown' }
  const folder = pathOverrides[slug] || slug
  const fp = path.join(AGENTS_ROOT, '.agents', 'projects', folder, filename)
  if (!fs.existsSync(fp)) return null
  return fs.readFileSync(fp, 'utf8')
}

module.exports = { loadRoster, loadAgentProfile, listProjectDocs, readProjectDoc, parseRosterMarkdown }
