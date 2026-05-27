import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useSocket, api, getStoredToken, setStoredToken } from './hooks/useSocket'
import Sidebar from './components/Sidebar'
import Command from './pages/Command'
import Home from './pages/Home'
import ProjectPage from './pages/Project'
import Todos from './pages/Todos'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'
import Login from './pages/Login'

export default function App() {
  const [roster, setRoster] = useState(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [authUser, setAuthUser] = useState(null)   // null=unknown, false=not logged in, object=logged in
  const [authChecked, setAuthChecked] = useState(false)

  // Check if we have a valid session on startup
  useEffect(() => {
    const token = getStoredToken()
    if (!token) { setAuthUser(false); setAuthChecked(true); return }
    fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        setAuthUser(data || false)
        setAuthChecked(true)
        if (!data) setStoredToken(null) // clear invalid token
      })
      .catch(() => { setAuthUser(false); setAuthChecked(true) })
  }, [])

  const { connected } = useSocket({
    'init': (data) => { setUnreadCount(data.unreadNotifs || 0) },
    'notification:new': (n) => {
      setUnreadCount(c => c + 1)
      setNotifications(prev => [n, ...prev].slice(0, 5))
    },
    'roster:synced': (r) => setRoster(r)
  })

  useEffect(() => {
    if (!authUser) return
    api('/projects').then(data => {
      if (data?.projects?.length) setRoster(data)
    }).catch(console.error)
    api('/settings/notifications').then(notifs => {
      setUnreadCount(notifs.filter(n => !n.read).length)
    }).catch(console.error)
  }, [authUser])

  useEffect(() => {
    if (notifications.length === 0) return
    const t = setTimeout(() => setNotifications(prev => prev.slice(0, -1)), 5000)
    return () => clearTimeout(t)
  }, [notifications])

  async function handleLogout() {
    const token = getStoredToken()
    if (token) {
      await fetch('/api/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } }).catch(() => {})
    }
    setStoredToken(null)
    setAuthUser(false)
  }

  // Show nothing while checking auth (avoids flash)
  if (!authChecked) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand/30 border-t-brand rounded-full animate-spin" />
      </div>
    )
  }

  // Show login if not authenticated — localhost always auto-passes via server, but
  // this gate protects remote browsers trying to use the app.
  if (authUser === false) {
    return <Login onLogin={user => setAuthUser(user)} />
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface">
        <Sidebar roster={roster} connected={connected} unreadCount={unreadCount} authUser={authUser} onLogout={handleLogout} />

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

