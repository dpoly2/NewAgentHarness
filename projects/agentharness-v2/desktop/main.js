const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

const CORE_PORT = 4000
const WEB_URL = `http://localhost:${CORE_PORT}`
const isDev = process.env.NODE_ENV === 'development'

let mainWindow = null
let tray = null
let coreProcess = null

function startCore() {
  const serverPath = path.join(__dirname, '..', 'core', 'server.js')
  coreProcess = spawn(process.execPath, [serverPath], {
    cwd: path.join(__dirname, '..'),
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PORT: CORE_PORT }
  })
  coreProcess.stdout.on('data', d => console.log('[core]', d.toString().trim()))
  coreProcess.stderr.on('data', d => console.error('[core]', d.toString().trim()))
  coreProcess.on('exit', code => console.log('[core] exited with code', code))
}

async function waitForCore(maxWaitMs = 15000) {
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    try {
      await new Promise((resolve, reject) => {
        http.get(`${WEB_URL}/api/health`, r => {
          let d = ''; r.on('data', c => d += c); r.on('end', () => resolve(JSON.parse(d)))
        }).on('error', reject)
      })
      return true
    } catch (e) {
      await new Promise(r => setTimeout(r, 500))
    }
  }
  return false
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    title: 'AgentHarness',
    backgroundColor: '#1E1E2E',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false
  })

  mainWindow.once('ready-to-show', () => mainWindow.show())

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadURL(WEB_URL)
  }

  mainWindow.on('closed', () => { mainWindow = null })
}

function createTray() {
  const icon = nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip('AgentHarness')
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open AgentHarness', click: () => { if (mainWindow) mainWindow.show(); else createWindow() } },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() }
  ]))
  tray.on('click', () => { if (mainWindow) mainWindow.show(); else createWindow() })
}

app.whenReady().then(async () => {
  // Start core server
  startCore()

  // Show splash / loading
  const splash = new BrowserWindow({ width: 400, height: 300, frame: false, backgroundColor: '#1E1E2E', center: true, webPreferences: { nodeIntegration: false } })
  splash.loadURL('data:text/html,<html style="background:#1E1E2E;display:flex;align-items:center;justify-content:center;height:100vh;margin:0"><div style="text-align:center;color:white;font-family:Inter,sans-serif"><div style="font-size:48px;margin-bottom:12px">⭐</div><div style="font-size:20px;font-weight:bold">AgentHarness</div><div style="color:#9ca3af;font-size:13px;margin-top:6px">Starting core server...</div></div></html>')

  const ready = await waitForCore()
  splash.close()

  if (ready) {
    createWindow()
  } else {
    const { dialog } = require('electron')
    dialog.showErrorBox('AgentHarness', 'Core server failed to start. Check that Node.js is installed and dependencies are installed (npm install).')
    app.quit()
    return
  }

  createTray()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('before-quit', () => {
  if (coreProcess) { coreProcess.kill(); coreProcess = null }
})
