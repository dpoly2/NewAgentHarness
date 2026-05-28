const { contextBridge } = require('electron')
// Expose minimal API — web app talks to Core Server directly via fetch/websocket
contextBridge.exposeInMainWorld('agentharness', {
  version: '2.0.0',
  platform: process.platform
})
