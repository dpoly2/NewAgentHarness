import type { AgentIdentity, Automation, HelperAgent, OpenItem, Project, RosterData, SharedAgent } from './types'

const PROJECT_SLUGS: Record<string, string> = {
  'XFTC Website & Plugin': 'xftc',
  'YEPC — Hutto CR 132': 'yepc',
  'The Elevation ATX': 'elevation',
  'PBS Foundation': 'pbs-foundation',
  'Nutrue Apparel': 'nutrue',
  'Smith Capital Properties': 'smithcap',
  'S2T Designs Agency': 's2tdesigns',
  'Personal Productivity': 'personal'
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function extractLineValue(markdown: string, label: string) {
  const regex = new RegExp(`\\*\\*${escapeRegex(label)}:\\*\\*\\s*(.+)`, 'i')
  return markdown.match(regex)?.[1]?.trim() ?? ''
}

function parseTable(block: string) {
  return block
    .split(/\r?\n/)
    .filter((line) => line.trim().startsWith('|'))
    .map((line) => line.trim())
    .filter((line) => !/^\|(?:\s*:?[-]+:?\s*\|)+\s*$/.test(line))
    .map((line) => line.split('|').slice(1, -1).map((cell) => cell.trim()))
}

function extractTableAfter(section: string, headingPattern: RegExp) {
  const match = section.match(new RegExp(`${headingPattern.source}([\\s\\S]*?)(?=\\n###\\s+|\\n##\\s+|$)`, 'i'))
  return match ? parseTable(match[1]) : []
}

function extractBulletPaths(section: string) {
  const match = section.match(/###\s+Files([\s\S]*?)(?=\n###\s+|\n##\s+|$)/i)
  if (!match) return []

  return match[1]
    .split(/\r?\n/)
    .map((line) => line.match(/-\s+`?([^`]+)`?/))
    .filter((value): value is RegExpMatchArray => Boolean(value))
    .map((value) => value[1].trim())
}

function parseLead(section: string, slug: string, projectName: string, fallbackName: string): AgentIdentity {
  const leadMatch = section.match(/###\s+Lead\s*[\r\n]+\*\*(.+?)\*\*\s+[—-]\s+(.+)/i)
  const agentName = leadMatch?.[1]?.trim() || fallbackName
  const role = leadMatch?.[2]?.trim() || 'Project lead'

  return {
    agentName,
    project: projectName,
    role,
    type: 'lead',
    filePath: `.agents/agents/projects/${slug}/${agentName}.md`,
    rawMarkdown: ''
  }
}

function parseSpecialists(section: string, slug: string, projectName: string) {
  const rows = extractTableAfter(section, /###\s+(Specialist Agents|Email Agents)/)
  return rows
    .slice(1)
    .filter((row) => row.length >= 2)
    .map((row) => ({
      agentName: row[0],
      project: projectName,
      role: row[1],
      type: 'specialist' as const,
      filePath: `.agents/agents/projects/${slug}/${row[0]}.md`,
      rawMarkdown: '',
      ...(row[2] ? { status: row[2] } : {})
    }))
}

function parseHelpers(section: string, slug: string): HelperAgent[] {
  const rows = extractTableAfter(section, /###\s+Helper Agents(?:\s+\(sub-tasks\))?/) 
  return rows
    .slice(1)
    .filter((row) => row.length >= 3)
    .map((row) => ({
      agentName: row[0],
      assignedBy: row[1],
      taskType: row[2],
      filePath: `.agents/agents/projects/${slug}/helpers/${row[0]}.md`,
      rawMarkdown: ''
    }))
}

function parseProjectSections(markdown: string) {
  const matches = [...markdown.matchAll(/^##\s+PROJECT\s+(\d+)\s+[—-]\s+(.+)$/gm)]
  const sharedIndex = markdown.search(/^##\s+🤖\s+/m)

  return matches.map((match, index) => {
    const start = match.index ?? 0
    const nextIndex = matches[index + 1]?.index
    const end = typeof nextIndex === 'number' ? nextIndex : sharedIndex >= 0 ? sharedIndex : markdown.length

    return {
      id: Number(match[1]),
      content: markdown.slice(start, end)
    }
  })
}

function emojiFromStatus(value: string): Project['status'] {
  const emoji = value.match(/[🟢🟡🔴⬜]/)?.[0] as Project['status'] | undefined
  return emoji ?? '⬜'
}

function statusLabel(value: string) {
  return value.replace(/^[🟢🟡🔴⬜✅]\s*/, '').trim() || 'Pending'
}

export function parseRoster(markdown: string): RosterData {
  const lastUpdated = extractLineValue(markdown, 'Last Updated')
  const coordinator = extractLineValue(markdown, 'Coordinator')

  const indexBlock = markdown.match(/##\s+🗂️\s+PROJECT INDEX([\s\S]*?)(?=\n---|\n##\s+PROJECT\s+1)/i)?.[1] ?? ''
  const indexRows = parseTable(indexBlock).slice(1)
  const indexLookup = new Map<number, { name: string; leadAgent: string; statusCell: string }>()

  indexRows.forEach((row) => {
    if (row.length < 5) return
    indexLookup.set(Number(row[0]), {
      name: row[1],
      leadAgent: row[2],
      statusCell: row[4]
    })
  })

  const projects: Project[] = parseProjectSections(markdown).map(({ id, content }) => {
    const indexRow = indexLookup.get(id)
    const name = indexRow?.name ?? `Project ${id}`
    const slug = PROJECT_SLUGS[name] ?? name.toLowerCase().replace(/[^a-z0-9]+/g, '-')
    const rawStatus = indexRow?.statusCell ?? '⬜ Pending'
    const files = extractBulletPaths(content)
    const docsPath = files[0] ?? `.agents/projects/${slug}/`

    return {
      id,
      name,
      slug,
      leadAgent: parseLead(content, slug, name, indexRow?.leadAgent ?? `${slug}-project-lead`),
      specialists: parseSpecialists(content, slug, name),
      helpers: parseHelpers(content, slug),
      status: emojiFromStatus(rawStatus),
      statusLabel: statusLabel(rawStatus),
      agentDocsPath: `.agents/agents/projects/${slug}/`,
      projectDocsPath: docsPath,
      projectDocs: [],
      docDirectories: files.length ? files : [`.agents/projects/${slug}/`]
    }
  })

  const sharedBlock = markdown.match(/##\s+🤖\s+SHARED \/ CROSS-PROJECT AGENTS([\s\S]*?)(?=\n---|\n##\s+⚙️)/i)?.[1] ?? ''
  const sharedAgents: SharedAgent[] = parseTable(sharedBlock)
    .slice(1)
    .filter((row) => row.length >= 3)
    .map((row) => ({
      agentName: row[0],
      specialty: row[1],
      projectsServed: row[2].split(',').map((item) => item.trim()),
      filePath: `.agents/agents/${row[0]}.md`,
      rawMarkdown: ''
    }))

  const automationsBlock = markdown.match(/##\s+⚙️\s+ACTIVE AUTOMATIONS([\s\S]*?)(?=\n---|\n##\s+🚨)/i)?.[1] ?? ''
  const automations: Automation[] = parseTable(automationsBlock)
    .slice(1)
    .filter((row) => row.length >= 3)
    .map((row) => {
      const rawStatus = row[2]
      const normalized = rawStatus.toLowerCase().includes('archive')
        ? 'archived'
        : rawStatus.toLowerCase().includes('pause')
          ? 'paused'
          : 'active'

      return {
        name: row[0],
        schedule: row[1],
        status: normalized,
        statusEmoji: rawStatus.match(/[✅🟢🟡🔴⬜]/)?.[0] ?? '⬜'
      }
    })

  const openItemsBlock = markdown.match(/##\s+🚨\s+OPEN ITEMS[^\n]*([\s\S]*?)$/i)?.[1] ?? ''
  const openItems: OpenItem[] = parseTable(openItemsBlock)
    .slice(1)
    .filter((row) => row.length >= 4)
    .map((row) => ({
      priority: (row[0].match(/[🔴🟡🟢]/)?.[0] ?? '🟢') as OpenItem['priority'],
      item: row[1],
      project: row[2],
      deadline: row[3]
    }))

  return {
    lastUpdated,
    coordinator,
    projects,
    sharedAgents,
    automations,
    openItems
  }
}
