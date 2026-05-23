import type { AgentIdentity } from './types'

function extractIdentitySection(rawMarkdown: string) {
  const match = rawMarkdown.match(/##\s+Identity([\s\S]*?)(?=\n##\s+|$)/i)
  return match?.[1] ?? ''
}

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function extractField(section: string, field: string) {
  const regex = new RegExp(`-\\s+\\*\\*${escapeRegex(field)}:\\*\\*\\s*(.+)`, 'i')
  return section.match(regex)?.[1]?.trim() ?? ''
}

function filenameFromPath(path: string) {
  return path.split('/').filter(Boolean).pop() ?? ''
}

export function parseAgent(rawMarkdown: string, filePath: string): AgentIdentity {
  const section = extractIdentitySection(rawMarkdown)
  const filename = filenameFromPath(filePath)
  const agentName = extractField(section, 'Agent Name') || filename.replace(/\.md$/i, '')
  const project = extractField(section, 'Project')
  const role = extractField(section, 'Role') || extractField(section, 'Specialty') || extractField(section, 'Lane')
  const declaredType = extractField(section, 'Type').toLowerCase()
  const status = extractField(section, 'Status') || rawMarkdown.match(/-\s+\*\*Status:\*\*\s*(.+)/i)?.[1]?.trim()

  let type: AgentIdentity['type'] = 'specialist'
  if (declaredType.includes('helper')) type = 'helper'
  else if (/-(project-lead|project-manager)\.md$/i.test(filename)) type = 'lead'
  else if (/-helper\.md$/i.test(filename) || /\/helpers\//.test(filePath)) type = 'helper'
  else if (!/\/projects\//.test(filePath)) type = 'shared'

  return {
    agentName,
    project,
    role,
    type,
    filePath,
    rawMarkdown,
    ...(status ? { status } : {})
  }
}
