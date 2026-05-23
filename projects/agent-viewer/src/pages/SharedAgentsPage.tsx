import { useNavigate } from 'react-router-dom'
import LoadingSpinner from '../components/LoadingSpinner'
import { useRosterData } from '../lib/RosterContext'

export default function SharedAgentsPage() {
  const navigate = useNavigate()
  const { roster, loading, error } = useRosterData()

  if (loading) {
    return <LoadingSpinner label="Loading shared agents..." skeletonCards={3} />
  }

  if (error || !roster) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">
        <h1 className="text-xl font-semibold">Unable to load shared agents</h1>
        <p className="mt-2 text-sm text-red-100/80">{error ?? 'Missing roster data.'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Shared</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Cross-project agents</h1>
        <p className="mt-2 text-sm text-slate-400">Shared capabilities available across the AgentHarness portfolio.</p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {roster.sharedAgents.map((agent) => (
          <button
            key={agent.agentName}
            type="button"
            onClick={() => navigate(`/agent/${encodeURIComponent(agent.filePath)}`)}
            className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 text-left transition hover:-translate-y-0.5 hover:border-slate-700"
          >
            <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Shared agent</p>
            <h2 className="mt-2 text-xl font-semibold text-white">{agent.agentName}</h2>
            <p className="mt-3 text-sm text-slate-300">{agent.specialty}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {agent.projectsServed.map((project) => (
                <span key={project} className="rounded-full bg-purple-500/15 px-3 py-1 text-xs text-purple-100">
                  {project}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
