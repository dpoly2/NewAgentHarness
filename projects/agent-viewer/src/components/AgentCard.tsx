import { useNavigate } from 'react-router-dom'
import type { AgentIdentity } from '../lib/types'
import StatusBadge from './StatusBadge'

interface AgentCardProps {
  agent: AgentIdentity
  status?: { emoji: '🟢' | '🟡' | '🔴' | '⬜'; label?: string }
  prominent?: boolean
}

const BORDER_STYLES: Record<AgentIdentity['type'], string> = {
  lead: 'border-l-4 border-blue-500',
  specialist: 'border-l-4 border-teal-500',
  helper: 'border-l-4 border-slate-400',
  shared: 'border-l-4 border-purple-500'
}

const TYPE_STYLES: Record<AgentIdentity['type'], string> = {
  lead: 'bg-blue-500/15 text-blue-200',
  specialist: 'bg-teal-500/15 text-teal-200',
  helper: 'bg-slate-500/15 text-slate-200',
  shared: 'bg-purple-500/15 text-purple-200'
}

export default function AgentCard({ agent, status, prominent = false }: AgentCardProps) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      onClick={() => navigate(`/agent/${encodeURIComponent(agent.filePath)}`)}
      className={`w-full rounded-2xl border border-slate-800 bg-slate-900/80 p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-700 hover:bg-slate-900 ${BORDER_STYLES[agent.type]} ${prominent ? 'min-h-[180px]' : ''}`}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">{agent.agentName}</h3>
          <p className="mt-1 text-sm text-slate-400 line-clamp-2">{agent.role}</p>
        </div>
        <span className={`rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-wide ${TYPE_STYLES[agent.type]}`}>
          {agent.type}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
        {agent.project && <span>{agent.project}</span>}
        {status && <StatusBadge status={status.emoji} label={status.label} compact />}
        {!status && agent.status && <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-200">{agent.status}</span>}
      </div>
    </button>
  )
}
