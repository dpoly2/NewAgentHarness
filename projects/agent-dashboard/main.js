const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  })

  // In dev you'll run a local dev server (vite). When developing, load the Vite dev server URL.
  const isDev = process.env.NODE_ENV === 'development' || process.env.ELECTRON_DEV === '1' || !!process.env.VITE_DEV_SERVER_URL
  if (isDev) {
    // Load the Vite dev server's copy of the renderer (renderer/index.html)
    const base = (process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173').replace(/\/$/, '')
    const devUrl = base + '/renderer/index.html'
    win.loadURL(devUrl)
    // Open DevTools in detached mode for debugging
    win.webContents.openDevTools({ mode: 'detach' })
  } else {
    win.loadFile(path.join(__dirname, 'renderer', 'index.html'))
  }
}

// Provide an IPC handler so preload can request agent data from the main process
ipcMain.handle('read-agents', async () => {
  // Try HTTP agent runtime first
  try {
    const res = await fetch('http://127.0.0.1:4000/agents', { cache: 'no-store' })
    if (res.ok) return await res.json()
  } catch (e) {
    console.error('read-agents http error', e)
  }
  // Fallback to file
  const fs = require('fs')
  const p = path.join(__dirname, 'data', 'agents.json')
  try {
    let raw = fs.readFileSync(p, 'utf8')
    raw = raw.replace(/^\uFEFF/, '')
    return JSON.parse(raw)
  } catch (e) {
    console.error('read-agents fallback error', e)
    return []
  }
})

// Agent commands now call the runtime HTTP API, fallback to local file update
ipcMain.handle('agent-command', async (event, { id, action }) => {
  try {
    const res = await fetch('http://127.0.0.1:4000/agent-command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, action })
    })
    if (res.ok) return await res.json()
  } catch (e) {
    console.error('agent-command http error', e)
  }
  // fallback to file modification
  const fs = require('fs')
  const p = path.join(__dirname, 'data', 'agents.json')
  try {
    let raw = fs.readFileSync(p, 'utf8')
    raw = raw.replace(/^\uFEFF/, '')
    const agents = JSON.parse(raw)
    const idx = agents.findIndex(a => a.id === id)
    if (idx === -1) return agents
    const agent = agents[idx]
    const ts = new Date().toISOString()
    if (action === 'start') {
      agent.status = 'running'
      if (!agent.progress || agent.progress >= 100) agent.progress = 0
      agent.logs = (agent.logs || []).concat([`${ts} - started`])
    } else if (action === 'stop') {
      agent.status = 'idle'
      agent.logs = (agent.logs || []).concat([`${ts} - stopped`])
    } else if (action === 'ping') {
      agent.logs = (agent.logs || []).concat([`${ts} - ping`])
    }
    agents[idx] = agent
    fs.writeFileSync(p, JSON.stringify(agents, null, 2), 'utf8')
    const wins = BrowserWindow.getAllWindows()
    for (const w of wins) {
      try { w.webContents.send('agents-updated', agents) } catch (e) { console.error('send failed', e) }
    }
    return agents
  } catch (e) {
    console.error('agent-command fallback error', e)
    return []
  }
})

// Relay renderer console messages to the main process stdout for debugging
app.on('web-contents-created', (event, contents) => {
  contents.on('console-message', (e, level, message, line, sourceId) => {
    console.log(`[RENDERER] level=${level} message=${message} source=${sourceId} line=${line}`)
  })
})

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
