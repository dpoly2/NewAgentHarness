import { useRosterData } from '../lib/RosterContext'
import LoadingSpinner from '../components/LoadingSpinner'
import ProjectCard from '../components/ProjectCard'

export default function Dashboard() {
  const { roster, loading, error, reload } = useRosterData()

  if (loading) {
    return <LoadingSpinner label="Loading roster from GitHub..." skeletonCards={6} />
  }

  if (error || !roster) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">
        <h1 className="text-xl font-semibold">Unable to load AgentHarness data</h1>
        <p className="mt-2 text-sm text-red-100/80">{error ?? 'Missing roster data.'}</p>
      </div>
    )
  }

  const urgentItems = roster.openItems.filter((item) => item.priority === '🔴')

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-red-300">🚨 Action Required</p>
            <p className="mt-1 text-sm text-slate-400">High-priority items pulled directly from the master roster.</p>
          </div>
        </div>
        <div className="flex gap-4 overflow-x-auto pb-2">
          {urgentItems.length > 0 ? (
            urgentItems.map((item) => (
              <article key={`${item.project}-${item.item}`} className="min-w-[280px] rounded-2xl border border-red-500/30 bg-red-500/10 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-red-200">
                  <span>{item.priority}</span>
                  <span>{item.project}</span>
                </div>
                <h2 className="mt-3 text-base font-semibold text-white">{item.item}</h2>
                <p className="mt-2 text-sm text-red-100/80">Deadline: {item.deadline}</p>
              </article>
            ))
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">No red-priority items right now.</div>
          )}
        </div>
      </section>

      <section className="space-y-5">
        <div className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-300">AgentHarness</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Project & agent dashboard</h1>
            <p className="mt-2 text-sm text-slate-400">Coordinator: {roster.coordinator} · Last updated: {roster.lastUpdated}</p>
          </div>
          <button
            type="button"
            onClick={() => void reload()}
            className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 hover:border-blue-400 hover:bg-blue-500/20"
          >
            Refresh
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {roster.projects.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </section>
    </div>
  )
}
