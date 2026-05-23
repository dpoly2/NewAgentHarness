import { useNavigate } from 'react-router-dom'
import type { Project } from '../lib/types'
import StatusBadge from './StatusBadge'

export default function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      onClick={() => navigate(`/project/${project.slug}`)}
      className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-700 hover:bg-slate-900"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Project {project.id}</p>
          <h3 className="mt-2 text-lg font-semibold text-white">{project.name}</h3>
        </div>
        <StatusBadge status={project.status} label={project.statusLabel} />
      </div>

      <dl className="space-y-3 text-sm text-slate-300">
        <div>
          <dt className="text-slate-500">Lead agent</dt>
          <dd className="mt-1 font-medium text-slate-100">{project.leadAgent.agentName}</dd>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-slate-500">Specialists</dt>
            <dd className="mt-1 text-base font-semibold text-white">{project.specialists.length}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Helpers</dt>
            <dd className="mt-1 text-base font-semibold text-white">{project.helpers.length}</dd>
          </div>
        </div>
        <div>
          <dt className="text-slate-500">Current phase</dt>
          <dd className="mt-1 text-slate-200">{project.statusLabel}</dd>
        </div>
      </dl>
    </button>
  )
}
