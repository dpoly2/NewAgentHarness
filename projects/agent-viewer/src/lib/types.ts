export interface AgentIdentity {
  agentName: string
  project: string
  role: string
  type: 'lead' | 'specialist' | 'helper' | 'shared'
  filePath: string
  rawMarkdown: string
  status?: string
}

export interface HelperAgent {
  agentName: string
  assignedBy: string
  taskType: string
  filePath: string
  rawMarkdown: string
}

export interface ProjectDoc {
  filename: string
  title: string
  filePath: string
  rawMarkdown: string
}

export interface Project {
  id: number
  name: string
  slug: string
  leadAgent: AgentIdentity
  specialists: AgentIdentity[]
  helpers: HelperAgent[]
  status: '🟢' | '🟡' | '🔴' | '⬜'
  statusLabel: string
  agentDocsPath: string
  projectDocsPath: string
  projectDocs: ProjectDoc[]
  docDirectories?: string[]
}

export interface SharedAgent {
  agentName: string
  specialty: string
  projectsServed: string[]
  filePath: string
  rawMarkdown: string
}

export interface Automation {
  name: string
  schedule: string
  status: 'active' | 'paused' | 'archived'
  statusEmoji: string
}

export interface OpenItem {
  priority: '🔴' | '🟡' | '🟢'
  item: string
  project: string
  deadline: string
}

export interface RosterData {
  lastUpdated: string
  coordinator: string
  projects: Project[]
  sharedAgents: SharedAgent[]
  automations: Automation[]
  openItems: OpenItem[]
}
