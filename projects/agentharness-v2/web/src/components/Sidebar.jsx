import { NavLink } from 'react-router-dom'

const PROJECT_ICONS = {
  xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕',
  smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️',
  ministry:'⛪', finance:'💰', personal:'🗓️', 'sigma-signal':'📰', travel:'✈️'
}

export default function Sidebar({ roster, connected, unreadCount, authUser, onLogout }) {
  const projects = roster?.projects || []

  return (
    <div className="flex flex-col h-full bg-surface border-r border-surface-border w-56 flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-surface-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-brand/20 flex items-center justify-center text-brand font-bold text-sm">AH</div>
          <div>
            <div className="text-sm font-bold text-white leading-tight">AgentHarness</div>
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-success' : 'bg-danger'}`} />
              <span className="text-xs text-gray-500">{connected ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main nav */}
      <nav className="p-2 space-y-0.5">
        <NavItem to="/command" icon="💬" label="Command" badge={unreadCount > 0 ? unreadCount : null} exact />
        <NavItem to="/" icon="🏠" label="Dashboard" exact />
        <NavItem to="/agents" icon="🤖" label="Agents" />
        <NavItem to="/clients" icon="👥" label="Clients" />
        <div className="border-t border-surface-border my-2" />
      </nav>

      {/* Projects list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        <div className="text-xs text-gray-600 px-3 py-1.5 font-semibold uppercase tracking-wider">Projects</div>
        {projects.length === 0 && (
          <div className="text-xs text-gray-600 px-3 py-2">Loading roster...</div>
        )}
        {projects.map(proj => (
          <NavLink key={proj.slug} to={`/project/${proj.slug}`}
            className={({ isActive }) => `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all cursor-pointer ${isActive ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}>
            <span className="flex-shrink-0">{PROJECT_ICONS[proj.slug] || '📁'}</span>
            <span className="truncate flex-1">{proj.name?.split(' ').slice(0, 3).join(' ')}</span>
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${proj.status === 'active' ? 'bg-success' : 'bg-warning'}`} />
          </NavLink>
        ))}
      </div>

      {/* Bottom nav */}
      <div className="p-2 border-t border-surface-border space-y-0.5">
        <NavItem to="/todos" icon="✅" label="Todos" />
        <NavItem to="/tasks" icon="⚡" label="Tasks" />
        <NavItem to="/settings" icon="⚙️" label="Settings" />
        {authUser && (
          <div className="pt-2 mt-1 border-t border-surface-border">
            <div className="flex items-center gap-2 px-3 py-1.5">
              <span className="text-xs text-gray-500 flex-1 truncate">👤 {authUser.username}</span>
              <button onClick={onLogout} title="Sign out"
                className="text-xs text-gray-500 hover:text-error transition-colors px-1.5 py-0.5 rounded hover:bg-error/10">
                ⏏
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function NavItem({ to, icon, label, badge, exact }) {
  return (
    <NavLink to={to} end={exact}
      className={({ isActive }) => `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all cursor-pointer ${isActive ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}>
      <span>{icon}</span>
      <span className="flex-1">{label}</span>
      {badge > 0 && <span className="w-4 h-4 rounded-full bg-brand text-white text-xs flex items-center justify-center leading-none">{badge > 9 ? '9+' : badge}</span>}
    </NavLink>
  )
}

