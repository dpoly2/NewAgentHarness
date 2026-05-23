interface StatusBadgeProps {
  status: '🟢' | '🟡' | '🔴' | '⬜'
  label?: string
  compact?: boolean
}

const STATUS_STYLES: Record<StatusBadgeProps['status'], string> = {
  '🟢': 'bg-green-600 text-white',
  '🟡': 'bg-yellow-400 text-slate-950',
  '🔴': 'bg-red-600 text-white',
  '⬜': 'bg-slate-500 text-white'
}

const STATUS_NAMES: Record<StatusBadgeProps['status'], string> = {
  '🟢': 'Active',
  '🟡': 'In Progress',
  '🔴': 'Blocked',
  '⬜': 'Pending'
}

export default function StatusBadge({ status, label, compact = false }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLES[status]}`}
      title={`${STATUS_NAMES[status]}${label ? ` — ${label}` : ''}`}
    >
      <span>{status}</span>
      {!compact && <span>{label || STATUS_NAMES[status]}</span>}
    </span>
  )
}
