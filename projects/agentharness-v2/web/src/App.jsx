import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useSocket, api } from './hooks/useSocket'
import Sidebar from './components/Sidebar'
import Command from './pages/Command'
import Home from './pages/Home'
import ProjectPage from './pages/Project'
import Todos from './pages/Todos'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'

export default function App() {
  const [roster, setRoster] = useState(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])

  const { connected } = useSocket({
    'init': (data) => {
      setUnreadCount(data.unreadNotifs || 0)
    },
    'notification:new': (n) => {
      setUnreadCount(c => c + 1)
      setNotifications(prev => [n, ...prev].slice(0, 5))
    },
    'roster:synced': (r) => setRoster(r)
  })

  // Load roster on startup
  useEffect(() => {
    api('/projects').then(data => {
      if (data?.projects?.length) setRoster(data)
    }).catch(console.error)

    api('/settings/notifications').then(notifs => {
      const unread = notifs.filter(n => !n.read).length
      setUnreadCount(unread)
    }).catch(console.error)
  }, [])

  // Auto-dismiss notification toast after 5s
  useEffect(() => {
    if (notifications.length === 0) return
    const t = setTimeout(() => setNotifications(prev => prev.slice(0, -1)), 5000)
    return () => clearTimeout(t)
  }, [notifications])

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface">
        <Sidebar roster={roster} connected={connected} unreadCount={unreadCount} />

        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Home roster={roster} />} />
            <Route path="/command" element={<Command roster={roster} />} />
            <Route path="/project/:slug" element={<ProjectPage roster={roster} />} />
            <Route path="/todos" element={<Todos roster={roster} />} />
            <Route path="/tasks" element={<Tasks roster={roster} />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Notification toasts */}
        {notifications.length > 0 && (
          <div className="fixed bottom-4 right-4 space-y-2 z-50">
            {notifications.map((n, i) => (
              <div key={i} className="bg-surface-light border border-surface-border rounded-xl px-4 py-3 shadow-xl text-sm text-gray-200 max-w-xs animate-pulse" style={{ animationIterationCount: 1 }}>
                <div className="flex items-start gap-2">
                  <span>{n.type === 'briefing' ? '📋' : n.type === 'task' ? '⚡' : n.priority === 'high' ? '🔔' : 'ℹ️'}</span>
                  <span>{n.message}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </BrowserRouter>
  )
}
