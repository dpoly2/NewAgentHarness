import { useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import { RosterProvider } from './lib/RosterContext'
import AgentView from './pages/AgentView'
import Dashboard from './pages/Dashboard'
import ProjectView from './pages/ProjectView'
import RosterView from './pages/RosterView'
import SharedAgentsPage from './pages/SharedAgentsPage'

function Shell() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <main className={`min-h-screen p-4 transition-all duration-200 md:p-6 ${collapsed ? 'md:ml-20' : 'md:ml-72'}`}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:slug" element={<ProjectView />} />
          <Route path="/agent/*" element={<AgentView />} />
          <Route path="/roster" element={<RosterView />} />
          <Route path="/shared" element={<SharedAgentsPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  return (
    <BrowserRouter>
      <RosterProvider>
        <Shell />
      </RosterProvider>
    </BrowserRouter>
  )
}
