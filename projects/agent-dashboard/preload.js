const { contextBridge, ipcRenderer } = require('electron')

// Use IPC to ask the main process to read files. Some preload environments
// don't provide access to Node core modules like 'fs'. Using ipcRenderer.invoke
// keeps the file access in the main process where Node is available.

contextBridge.exposeInMainWorld('electron', {
  getAgents: () => ipcRenderer.invoke('read-agents'),
  invoke: (channel, data) => ipcRenderer.invoke(channel, data),
  onAgentsUpdated: (cb) => {
    ipcRenderer.on('agents-updated', (e, data) => cb(data))
  },
  send: (channel, data) => ipcRenderer.send(channel, data),
  on: (channel, cb) => ipcRenderer.on(channel, (e, d) => cb(d)),
  offAll: (channel) => ipcRenderer.removeAllListeners(channel)
})
