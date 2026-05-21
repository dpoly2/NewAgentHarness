const http = require('http')
const fs = require('fs')
const path = require('path')

const agentsFile = path.join(__dirname, 'data', 'agents.json')
let agents = []
try {
  let raw = fs.readFileSync(agentsFile, 'utf8')
  raw = raw.replace(/^\uFEFF/, '')
  agents = JSON.parse(raw)
} catch (e) {
  console.error('Failed to load agents.json, starting with empty list', e)
  agents = []
}

const clients = []
function sendEvent(data){
  const payload = `data: ${JSON.stringify(data)}\n\n`
  clients.forEach(res => res.write(payload))
}
function persist(){
  try { fs.writeFileSync(agentsFile, JSON.stringify(agents, null, 2), 'utf8') } catch(e) { console.error('Failed to persist agents', e) }
}

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/agents'){
    res.writeHead(200, {'Content-Type':'application/json'})
    return res.end(JSON.stringify(agents))
  }

  if (req.method === 'GET' && req.url === '/events'){
    // SSE endpoint
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    })
    res.write('\n')
    clients.push(res)
    req.on('close', () => {
      const idx = clients.indexOf(res)
      if (idx !== -1) clients.splice(idx,1)
    })
    return
  }

  if (req.method === 'POST' && req.url === '/agent-command'){
    let body = ''
    req.on('data', chunk => body += chunk)
    req.on('end', () => {
      try {
        const { id, action } = JSON.parse(body)
        const idx = agents.findIndex(a => a.id === id)
        if (idx === -1) {
          res.writeHead(404, {'Content-Type':'application/json'})
          return res.end(JSON.stringify({ error: 'agent not found' }))
        }
        const agent = agents[idx]
        const ts = new Date().toISOString()
        if (action === 'start'){
          agent.status = 'running'
          if (!agent.progress || agent.progress >= 100) agent.progress = 0
          agent.logs = (agent.logs || []).concat([`${ts} - started`])
        } else if (action === 'stop'){
          agent.status = 'idle'
          agent.logs = (agent.logs || []).concat([`${ts} - stopped`])
        } else if (action === 'ping'){
          agent.logs = (agent.logs || []).concat([`${ts} - ping`])
        }
        agents[idx] = agent
        persist()
        // notify SSE clients
        sendEvent(agents)
        res.writeHead(200, {'Content-Type':'application/json'})
        res.end(JSON.stringify(agents))
      } catch (e){
        res.writeHead(400, {'Content-Type':'application/json'})
        res.end(JSON.stringify({ error: 'invalid body' }))
      }
    })
    return
  }

  // fallback
  res.writeHead(404, {'Content-Type':'text/plain'})
  res.end('Not found')
})

const PORT = process.env.AGENT_SERVER_PORT || 4000
server.listen(PORT, '127.0.0.1', () => {
  console.log(`Agent runtime stub listening on http://127.0.0.1:${PORT}`)
})

// simple incremental progress simulator for running agents
setInterval(() => {
  let changed = false
  agents.forEach(a => {
    if (a.status === 'running'){
      a.progress = Math.min(100, (a.progress || 0) + Math.floor(Math.random()*10)+1)
      a.logs = (a.logs || []).concat([`${new Date().toISOString()} - progress ${a.progress}%`])
      if (a.progress >= 100) { a.status = 'idle'; changed = true }
      changed = true
    }
  })
  if (changed){ persist(); sendEvent(agents) }
}, 5000)
