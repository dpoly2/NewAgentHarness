import { useNavigate } from 'react-router-dom'
import type { HelperAgent } from '../lib/types'

export default function HelperBadge({ helper }: { helper: HelperAgent }) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      onClick={() => navigate(`/agent/${encodeURIComponent(helper.filePath)}`)}
      className="rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs text-slate-200 transition hover:border-slate-500 hover:bg-slate-800"
      title={helper.assignedBy}
    >
      [{helper.agentName} → {helper.taskType}]
    </button>
  )
}
