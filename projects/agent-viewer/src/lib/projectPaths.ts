import type { Project } from './types'

const SHARED_AGENT_OVERRIDES: Record<string, string[]> = {
  'grants-research-agent': ['agents/grants_research_agent.md'],
  'grant-writer-agent': ['agents/grant_writer_agent.md'],
  'github-sync-agent': ['agents/github_sync_agent.md'],
  'wordpresspluginsagent': ['agents/wordpresspluginsagent.md'],
  'web-dev-researcher': ['agents/web_dev_researcher.md']
}

function dedupe(paths: string[]) {
  return [...new Set(paths.filter(Boolean).map((value) => value.replace(/\\/g, '/').replace(/^\/+/, '').replace(/\/+/g, '/')))]
}

export function getProjectDocDirectories(project: Project) {
  const configured = project.docDirectories?.length ? project.docDirectories : [project.projectDocsPath]
  const generated = configured.flatMap((path) => {
    const trimmed = path.replace(/`/g, '').replace(/\/$/, '')
    const normalized = trimmed.replace(/\\/g, '/')
    const withoutAgentsPrefix = normalized.startsWith('.agents/') ? normalized.slice('.agents/'.length) : ''

    return [normalized, withoutAgentsPrefix, `.agents/projects/${project.slug}`, `projects/${project.slug}`]
  })

  return dedupe(generated)
}

export function getAgentPathCandidates(filePath: string) {
  const normalized = filePath.replace(/\\/g, '/').replace(/^\/+/, '')
  const basename = normalized.split('/').pop()?.replace(/\.md$/i, '') ?? ''
  const underscored = basename.replace(/-/g, '_')
  const stripped = normalized.startsWith('.agents/') ? normalized.slice('.agents/'.length) : ''
  const candidates = [normalized, stripped]

  if (!/\/projects\//.test(normalized)) {
    candidates.push(`agents/${basename}.md`)
    candidates.push(`agents/${underscored}.md`)
    candidates.push(`.agents/agents/${basename}.md`)
    candidates.push(`.agents/agents/${underscored}.md`)
    candidates.push(...(SHARED_AGENT_OVERRIDES[basename] ?? []))
  }

  return dedupe(candidates)
}
