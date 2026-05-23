import { NavLink } from 'react-router-dom'
import { useRosterData } from '../lib/RosterContext'
import StatusBadge from './StatusBadge'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

function navClass(active: boolean, collapsed: boolean) {
  return [
    'flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition',
    collapsed ? 'justify-center' : 'justify-between',
    active ? 'bg-blue-500/15 text-blue-100' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
  ].join(' ')
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { roster } = useRosterData()
  const redItems = roster?.openItems.filter((item) => item.priority === '🔴').length ?? 0

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-20 hidden border-r border-slate-800 bg-slate-950/95 backdrop-blur md:flex md:flex-col ${collapsed ? 'w-20' : 'w-72'}`}
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-4">
        {!collapsed && (
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">AgentHarness</p>
            <p className="text-sm font-semibold text-white">Viewer</p>
          </div>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="rounded-lg border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:border-slate-500 hover:text-white"
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto px-3 py-4">
        <NavLink to="/" className={({ isActive }) => navClass(isActive, collapsed)}>
          <span className="flex items-center gap-3"><span>🏠</span>{!collapsed && <span>Dashboard</span>}</span>
        </NavLink>
        <NavLink to="/roster" className={({ isActive }) => navClass(isActive, collapsed)}>
          <span className="flex items-center gap-3"><span>📋</span>{!collapsed && <span>Full Roster</span>}</span>
        </NavLink>
        <NavLink to="/shared" className={({ isActive }) => navClass(isActive, collapsed)}>
          <span className="flex items-center gap-3"><span>🤖</span>{!collapsed && <span>Shared Agents</span>}</span>
        </NavLink>

        {!collapsed && <div className="my-4 border-t border-slate-800 pt-4 text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Projects</div>}

        <div className="space-y-2">
          {roster?.projects.map((project) => (
            <NavLink key={project.slug} to={`/project/${project.slug}`} className={({ isActive }) => navClass(isActive, collapsed)}>
              <span className="flex min-w-0 items-center gap-3">
                <span className="shrink-0 text-slate-500">{project.id}.</span>
                {!collapsed && <span className="truncate">{project.name}</span>}
              </span>
              {!collapsed && <StatusBadge status={project.status} label={project.statusLabel} compact />}
            </NavLink>
          ))}
        </div>

        {!collapsed && <div className="my-4 border-t border-slate-800 pt-4" />}

        <NavLink to="/roster#automations" className={({ isActive }) => navClass(isActive, collapsed)}>
          <span className="flex items-center gap-3"><span>⚙️</span>{!collapsed && <span>Automations</span>}</span>
        </NavLink>
        <NavLink to="/roster#open-items" className={({ isActive }) => navClass(isActive, collapsed)}>
          <span className="flex items-center gap-3"><span>🚨</span>{!collapsed && <span>Open Items</span>}</span>
          {!collapsed && redItems > 0 && (
            <span className="rounded-full bg-red-600 px-2 py-0.5 text-xs font-semibold text-white">{redItems}</span>
          )}
        </NavLink>
      </nav>
    </aside>
  )
}
