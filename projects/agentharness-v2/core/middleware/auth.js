/**
 * Bearer-token authentication middleware.
 * Validates against:
 *   1. Session tokens created by /api/auth/login (username+password)
 *   2. Static ACCESS_TOKEN env var (legacy / headless API access)
 * Localhost always bypasses auth for local UI access.
 */
const path = require('path')
const fs = require('fs')
const crypto = require('crypto')

const TOKEN_FILE = path.join(__dirname, '..', '..', 'data', 'access_token.json')
const SESSIONS_FILE = path.join(__dirname, '..', '..', 'data', 'sessions.json')

function getStaticToken() {
  if (process.env.ACCESS_TOKEN) return process.env.ACCESS_TOKEN
  try {
    if (fs.existsSync(TOKEN_FILE)) {
      const data = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'))
      if (data.token) return data.token
    }
  } catch (e) { /* ignore */ }
  return null
}

function isValidSessionToken(token) {
  try {
    if (!fs.existsSync(SESSIONS_FILE)) return false
    const sessions = JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8'))
    const now = Date.now()
    return sessions.some(s => s.token === token && s.expiresAt > now)
  } catch { return false }
}

function requireAuth(req, res, next) {
  // Always allow localhost (local UI / CLI access)
  const ip = req.ip || req.socket?.remoteAddress || ''
  const isLocal = ip === '127.0.0.1' || ip === '::1' || ip === '::ffff:127.0.0.1'
  if (isLocal) return next()

  // Extract token from request
  const authHeader = req.headers['authorization'] || ''
  const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : null
  const token = req.headers['x-api-key'] || req.query.token || bearerToken

  if (!token) return res.status(401).json({ error: 'Authentication required. Please log in.' })

  // 1. Check session tokens (login-based auth)
  if (isValidSessionToken(token)) return next()

  // 2. Check static ACCESS_TOKEN (env / headless API access)
  const staticToken = getStaticToken()
  if (staticToken && token === staticToken) return next()

  return res.status(401).json({ error: 'Invalid or expired session. Please log in again.' })
}

function getAccessToken() { return getStaticToken() }

module.exports = { requireAuth, getAccessToken }

