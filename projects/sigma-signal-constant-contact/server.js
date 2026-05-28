const http = require('http')
const fs = require('fs')
const path = require('path')

const root = __dirname
const publicDir = path.join(root, 'public')
const dataDir = path.join(root, 'data')
const port = Number(process.env.PORT || 4177)

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml'
}

function readJson(fileName, fallback) {
  try {
    return JSON.parse(fs.readFileSync(path.join(dataDir, fileName), 'utf8'))
  } catch {
    return fallback
  }
}

function sendJson(res, body) {
  res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(body, null, 2))
}

function notFound(res) {
  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
  res.end('Not found')
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`)

  if (url.pathname === '/api/status') {
    const config = readJson('config.json', {})
    const state = readJson('state.json', {})
    const requests = readJson('requests.json', [])
    return sendJson(res, { config, state, requests })
  }

  if (url.pathname === '/api/requests') {
    return sendJson(res, readJson('requests.json', []))
  }

  const requested = url.pathname === '/' ? '/index.html' : url.pathname
  const safePath = path.normalize(requested).replace(/^(\.\.[/\\])+/, '')
  const filePath = path.join(publicDir, safePath)

  if (!filePath.startsWith(publicDir)) {
    return notFound(res)
  }

  fs.readFile(filePath, (err, content) => {
    if (err) return notFound(res)
    res.writeHead(200, { 'Content-Type': mimeTypes[path.extname(filePath)] || 'application/octet-stream' })
    res.end(content)
  })
})

server.listen(port, '127.0.0.1', () => {
  console.log(`Sigma Signal monitor running at http://127.0.0.1:${port}`)
})
