const { contextBridge, ipcRenderer } = require('electron')
const path = require('path')
const fs = require('fs')

const dataPath = path.join(__dirname, 'data', 'agents.json')

function readAgents() {
  try {
    const raw = fs.readFileSync(dataPath, 'utf8')
    return JSON.parse(raw)
  } catch (e) {
    return []
  }
}

contextBridge.exposeInMainWorld('electron', {
  getAgents: () => readAgents(),
  onAgentsUpdated: (cb) => {
    ipcRenderer.on('agents-updated', (e, data) => cb(data))
  },
  send: (channel, data) => ipcRenderer.send(channel, data),
  on: (channel, cb) => ipcRenderer.on(channel, (e, d) => cb(d))
})
