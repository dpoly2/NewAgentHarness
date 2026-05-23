import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import LoadingSpinner from '../components/LoadingSpinner'
import { useRosterData } from '../lib/RosterContext'

type SortKey = 'id' | 'project' | 'agentName' | 'role' | 'type' | 'status'

export default function RosterView() {
  const { roster, loading, error } = useRosterData()
  const location = useLocation()
  const [query, setQuery] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('id')
  const [ascending, setAscending] = useState(true)

  useEffect(() => {
    if (!location.hash) return
    const id = location.hash.replace('#', '')
    requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }, [location.hash])

  const rows = useMemo(() => {
    if (!roster) return []

    return roster.projects.flatMap((project) => [
      {
        id: `${project.id}-lead`,
        index: project.id,
        project: project.name,
        agentName: project.leadAgent.agentName,
        role: project.leadAgent.role,
        type: 'lead',
        status: `${project.status} ${project.statusLabel}`
      },
      ...project.specialists.map((agent, index) => ({
        id: `${project.id}-specialist-${index}`,
        index: project.id,
        project: project.name,
        agentName: agent.agentName,
        role: agent.role,
        type: 'specialist',
        status: `${project.status} ${project.statusLabel}`
      })),
      ...project.helpers.map((helper, index) => ({
        id: `${project.id}-helper-${index}`,
        index: project.id,
        project: project.name,
        agentName: helper.agentName,
        role: helper.taskType,
        type: 'helper',
        status: `${project.status} ${project.statusLabel}`
      }))
    ]).concat(
      roster.sharedAgents.map((agent, index) => ({
        id: `shared-${index}`,
        index: 999,
        project: 'Shared',
        agentName: agent.agentName,
        role: agent.specialty,
        type: 'shared',
        status: '⬜ Cross-project'
      }))
    )
  }, [roster])

  const filteredRows = useMemo(() => {
    const loweredQuery = query.trim().toLowerCase()
    const prepared = loweredQuery
      ? rows.filter((row) => Object.values(row).some((value) => String(value).toLowerCase().includes(loweredQuery)))
      : rows

    return [...prepared].sort((left, right) => {
      const leftValue = String(left[sortKey]).toLowerCase()
      const rightValue = String(right[sortKey]).toLowerCase()
      const result = leftValue.localeCompare(rightValue, undefined, { numeric: true })
      return ascending ? result : -result
    })
  }, [ascending, query, rows, sortKey])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setAscending((value) => !value)
    } else {
      setSortKey(key)
      setAscending(true)
    }
  }

  function exportCsv() {
    const header = ['#', 'Project', 'Agent Name', 'Role', 'Type', 'Status']
    const csvRows = [header.join(',')].concat(
      filteredRows.map((row) =>
        [row.index, row.project, row.agentName, row.role, row.type, row.status]
          .map((value) => `"${String(value).replace(/"/g, '""')}"`)
          .join(',')
      )
    )

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'agent-roster.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <LoadingSpinner label="Loading roster table..." skeletonCards={4} />
  }

  if (error || !roster) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">
        <h1 className="text-xl font-semibold">Unable to load roster</h1>
        <p className="mt-2 text-sm text-red-100/80">{error ?? 'Missing roster data.'}</p>
      </div>
    )
  }

  const sortIndicator = ascending ? '↑' : '↓'

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Roster</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Full agent roster</h1>
            <p className="mt-2 text-sm text-slate-400">Search, sort, and export the current roster snapshot.</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search agents, projects, roles..."
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white outline-none placeholder:text-slate-500 focus:border-blue-400 sm:w-80"
            />
            <button
              type="button"
              onClick={exportCsv}
              className="rounded-xl border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm font-medium text-blue-100 hover:border-blue-400 hover:bg-blue-500/20"
            >
              Export CSV
            </button>
          </div>
        </div>

        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                {[
                  ['id', '#'],
                  ['project', 'Project'],
                  ['agentName', 'Agent Name'],
                  ['role', 'Role'],
                  ['type', 'Type'],
                  ['status', 'Status']
                ].map(([key, label]) => (
                  <th key={key} className="px-4 py-3 font-medium">
                    <button type="button" onClick={() => toggleSort(key as SortKey)} className="flex items-center gap-2 hover:text-white">
                      <span>{label}</span>
                      {sortKey === key && <span>{sortIndicator}</span>}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row) => (
                <tr key={row.id} className="border-t border-slate-800 text-slate-200">
                  <td className="px-4 py-3">{row.index === 999 ? '—' : row.index}</td>
                  <td className="px-4 py-3">{row.project}</td>
                  <td className="px-4 py-3 font-medium text-white">{row.agentName}</td>
                  <td className="px-4 py-3 text-slate-300">{row.role}</td>
                  <td className="px-4 py-3 capitalize">{row.type}</td>
                  <td className="px-4 py-3">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section id="automations" className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <h2 className="text-2xl font-semibold text-white">Automations</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Automation</th>
                <th className="px-4 py-3 font-medium">Schedule</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {roster.automations.map((automation) => (
                <tr key={automation.name} className="border-t border-slate-800 text-slate-200">
                  <td className="px-4 py-3 font-medium text-white">{automation.name}</td>
                  <td className="px-4 py-3">{automation.schedule}</td>
                  <td className="px-4 py-3 capitalize">{automation.statusEmoji} {automation.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section id="open-items" className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <h2 className="text-2xl font-semibold text-white">Open Items</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Priority</th>
                <th className="px-4 py-3 font-medium">Item</th>
                <th className="px-4 py-3 font-medium">Project</th>
                <th className="px-4 py-3 font-medium">Deadline</th>
              </tr>
            </thead>
            <tbody>
              {roster.openItems.map((item) => (
                <tr key={`${item.project}-${item.item}`} className="border-t border-slate-800 text-slate-200">
                  <td className="px-4 py-3">{item.priority}</td>
                  <td className="px-4 py-3 font-medium text-white">{item.item}</td>
                  <td className="px-4 py-3">{item.project}</td>
                  <td className="px-4 py-3">{item.deadline}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
