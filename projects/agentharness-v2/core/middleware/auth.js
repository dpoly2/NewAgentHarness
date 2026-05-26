/**
 * Bearer-token authentication middleware.
 * Set ACCESS_TOKEN in .env or environment variables to protect the API.
 * If not set, the server runs in open (LAN-only) mode with a warning.
 */
const path = require('path')
const fs = require('fs')

const TOKEN_FILE = path.join(__dirname, '..', '..', 'data', 'access_token.json')

function getAccessToken() {
  // 1. Prefer environment variable
  if (process.env.ACCESS_TOKEN) return process.env.ACCESS_TOKEN
  // 2. Fall back to persisted token file
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      const data = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'))
      if (data.token) return data.token
    }
  } catch (e) { /* ignore */ }
  return null
}

function requireAuth(req, res, next) {
  const token = getAccessToken()
  if (!token) return next() // no token configured = open LAN mode

  // Always allow localhost access without token (for local UI)
  const ip = req.ip || req.socket?.remoteAddress || ''
  if (ip === '127.0.0.1' || ip === '::1' || ip === '::ffff:127.0.0.1') return next()

  // Check Authorization header: Bearer <token>
  const authHeader = req.headers['authorization'] || ''
  const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : null

  // Also accept x-api-key header and ?token= query param (for SSE/EventSource clients)
  const apiKey = req.headers['x-api-key'] || req.query.token || bearerToken

  if (!apiKey || apiKey !== token) {
    return res.status(401).json({ error: 'Unauthorized. Provide a valid Bearer token.' })
  }
  next()
}

module.exports = { requireAuth, getAccessToken }
