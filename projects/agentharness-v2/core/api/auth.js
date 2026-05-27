/**
 * Auth API — username/password login with session tokens.
 * Passwords hashed with scrypt (Node built-in, no native deps).
 * Tokens stored in data/sessions.json with expiry.
 */
const express = require('express')
const router = express.Router()
const crypto = require('crypto')
const path = require('path')
const fs = require('fs')

const DATA_DIR = path.join(__dirname, '..', '..', 'data')
const USERS_FILE = path.join(DATA_DIR, 'users.json')
const SESSIONS_FILE = path.join(DATA_DIR, 'sessions.json')

const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000 // 7 days

// ─── Helpers ─────────────────────────────────────────────────────────────────

function loadUsers() {
  try { return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8')) } catch { return [] }
}

function saveUsers(users) {
  fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2))
}

function loadSessions() {
  try { return JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8')) } catch { return [] }
}

function saveSessions(sessions) {
  fs.writeFileSync(SESSIONS_FILE, JSON.stringify(sessions, null, 2))
}

function cleanExpiredSessions(sessions) {
  return sessions.filter(s => s.expiresAt > Date.now())
}

async function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex')
  const hash = await new Promise((resolve, reject) => {
    crypto.scrypt(password, salt, 64, (err, key) => err ? reject(err) : resolve(key.toString('hex')))
  })
  return `${salt}:${hash}`
}

async function verifyPassword(password, stored) {
  const [salt, hash] = stored.split(':')
  const derived = await new Promise((resolve, reject) => {
    crypto.scrypt(password, salt, 64, (err, key) => err ? reject(err) : resolve(key.toString('hex')))
  })
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(derived, 'hex'))
}

function generateToken() {
  return crypto.randomBytes(32).toString('hex')
}

// ─── Ensure default admin user exists on first run ───────────────────────────
async function ensureDefaultUser() {
  const users = loadUsers()
  if (users.length === 0) {
    const defaultPassword = process.env.ADMIN_PASSWORD || 'agentharness'
    const passwordHash = await hashPassword(defaultPassword)
    users.push({
      id: crypto.randomBytes(8).toString('hex'),
      username: 'admin',
      passwordHash,
      role: 'admin',
      createdAt: new Date().toISOString()
    })
    saveUsers(users)
    if (!process.env.ADMIN_PASSWORD) {
      console.warn('⚠️  Default admin created: username=admin password=agentharness')
      console.warn('   Change password immediately in Settings → Security!')
    }
  }
}

ensureDefaultUser().catch(console.error)

// ─── Routes ──────────────────────────────────────────────────────────────────

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body
    if (!username || !password) return res.status(400).json({ error: 'username and password required' })

    const users = loadUsers()
    const user = users.find(u => u.username.toLowerCase() === username.toLowerCase())
    if (!user) return res.status(401).json({ error: 'Invalid username or password' })

    const valid = await verifyPassword(password, user.passwordHash)
    if (!valid) return res.status(401).json({ error: 'Invalid username or password' })

    // Create session token
    const token = generateToken()
    const sessions = cleanExpiredSessions(loadSessions())
    sessions.push({ token, userId: user.id, username: user.username, role: user.role, createdAt: Date.now(), expiresAt: Date.now() + SESSION_TTL_MS })
    saveSessions(sessions)

    res.json({ token, username: user.username, role: user.role, expiresAt: Date.now() + SESSION_TTL_MS })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/auth/logout
router.post('/logout', (req, res) => {
  try {
    const authHeader = req.headers['authorization'] || ''
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : req.body?.token
    if (token) {
      const sessions = loadSessions().filter(s => s.token !== token)
      saveSessions(sessions)
    }
    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// GET /api/auth/me — validate current token
router.get('/me', (req, res) => {
  try {
    const authHeader = req.headers['authorization'] || ''
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : req.query.token
    if (!token) return res.status(401).json({ error: 'No token' })

    const sessions = cleanExpiredSessions(loadSessions())
    const session = sessions.find(s => s.token === token)
    if (!session) return res.status(401).json({ error: 'Invalid or expired session' })

    res.json({ username: session.username, role: session.role, expiresAt: session.expiresAt })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

// POST /api/auth/change-password
router.post('/change-password', async (req, res) => {
  try {
    const authHeader = req.headers['authorization'] || ''
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : null
    if (!token) return res.status(401).json({ error: 'Not authenticated' })

    const sessions = cleanExpiredSessions(loadSessions())
    const session = sessions.find(s => s.token === token)
    if (!session) return res.status(401).json({ error: 'Invalid session' })

    const { currentPassword, newPassword } = req.body
    if (!currentPassword || !newPassword) return res.status(400).json({ error: 'currentPassword and newPassword required' })
    if (newPassword.length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters' })

    const users = loadUsers()
    const userIdx = users.findIndex(u => u.id === session.userId)
    if (userIdx === -1) return res.status(404).json({ error: 'User not found' })

    const valid = await verifyPassword(currentPassword, users[userIdx].passwordHash)
    if (!valid) return res.status(401).json({ error: 'Current password is incorrect' })

    users[userIdx].passwordHash = await hashPassword(newPassword)
    saveUsers(users)

    // Invalidate all other sessions for this user
    const newSessions = sessions.filter(s => s.userId !== session.userId || s.token === token)
    saveSessions(newSessions)

    res.json({ ok: true })
  } catch (e) { res.status(500).json({ error: e.message }) }
})

module.exports = { router, loadSessions, cleanExpiredSessions }
