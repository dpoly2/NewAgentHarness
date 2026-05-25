/**
 * Push Notification Bridge
 * Sends alerts to Apple Watch (via iPhone) and other devices.
 *
 * Supported providers:
 *   ntfy    — free, self-hostable, iOS app mirrors to Apple Watch
 *   pushover — $5 one-time iOS app, best Watch complication support
 *   pushcut — webhook-driven, native Apple Shortcuts + Watch complication
 *
 * Config stored in data/push_config.json
 */
const fs = require('fs')
const path = require('path')

const CONFIG_PATH = path.join(__dirname, '..', '..', 'data', 'push_config.json')

const DEFAULTS = {
  enabled: false,
  provider: 'ntfy',       // 'ntfy' | 'pushover' | 'pushcut'
  minPriority: 'high',    // 'urgent' | 'high' | 'medium' | 'low' — only push at or above
  // ntfy
  ntfyTopic: '',          // e.g. 'agentharness-david' or full URL for self-hosted
  ntfyServer: 'https://ntfy.sh',
  // Pushover
  pushoverToken: '',
  pushoverUser: '',
  // Pushcut
  pushcutWebhook: ''      // Full webhook URL from Pushcut app
}

const PRIORITY_ORDER = { low: 0, medium: 1, high: 2, urgent: 3 }

function getConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8')) }
    }
  } catch (e) { /* ignore */ }
  return { ...DEFAULTS }
}

function saveConfig(updates) {
  const current = getConfig()
  const next = { ...current, ...updates }
  const dir = path.dirname(CONFIG_PATH)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(next, null, 2))
  return next
}

/**
 * Send a push notification.
 * @param {string} message  — body text
 * @param {string} title    — notification title (default: 'AgentHarness')
 * @param {string} priority — 'urgent' | 'high' | 'medium' | 'low'
 * @param {string} [tag]    — emoji tag e.g. 'robot', 'white_check_mark'
 */
async function sendPush(message, title = 'AgentHarness', priority = 'medium', tag = 'robot') {
  const config = getConfig()
  if (!config.enabled) return

  const msgPriority = PRIORITY_ORDER[priority] ?? 1
  const minPriority = PRIORITY_ORDER[config.minPriority] ?? 2
  if (msgPriority < minPriority) return  // below threshold

  try {
    switch (config.provider) {
      case 'ntfy':    return await sendNtfy(config, message, title, priority, tag)
      case 'pushover': return await sendPushover(config, message, title, priority)
      case 'pushcut': return await sendPushcut(config, message, title)
      default: console.warn('[push] Unknown provider:', config.provider)
    }
  } catch (e) {
    console.error('[push] Failed to send push notification:', e.message)
  }
}

// ─── ntfy ─────────────────────────────────────────────────────────────────────

const NTFY_PRIORITY = { urgent: 5, high: 4, medium: 3, low: 2 }
const NTFY_TAGS = { task: 'robot', todo: 'white_check_mark', info: 'bell', warning: 'warning', error: 'x' }

async function sendNtfy(config, message, title, priority, tag) {
  if (!config.ntfyTopic) {
    console.warn('[push/ntfy] ntfyTopic not configured — set it in Settings → Push Notifications')
    return
  }
  const url = `${config.ntfyServer.replace(/\/$/, '')}/${config.ntfyTopic}`
  const fetch = require('node-fetch')
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'text/plain',
      'Title': title,
      'Priority': String(NTFY_PRIORITY[priority] || 3),
      'Tags': NTFY_TAGS[tag] || tag || 'robot'
    },
    body: message
  })
  if (!res.ok) console.warn(`[push/ntfy] HTTP ${res.status}: ${await res.text()}`)
  else console.log('[push/ntfy] Sent:', title)
}

// ─── Pushover ─────────────────────────────────────────────────────────────────

const PUSHOVER_PRIORITY = { urgent: 1, high: 0, medium: -1, low: -2 }

async function sendPushover(config, message, title, priority) {
  if (!config.pushoverToken || !config.pushoverUser) {
    console.warn('[push/pushover] Token/User not configured')
    return
  }
  const fetch = require('node-fetch')
  const body = new URLSearchParams({
    token: config.pushoverToken,
    user: config.pushoverUser,
    title,
    message,
    priority: String(PUSHOVER_PRIORITY[priority] ?? 0),
    sound: priority === 'urgent' ? 'siren' : 'pushover'
  })
  const res = await fetch('https://api.pushover.net/1/messages.json', {
    method: 'POST',
    body,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  const json = await res.json()
  if (json.status !== 1) console.warn('[push/pushover] Error:', json.errors)
  else console.log('[push/pushover] Sent:', title)
}

// ─── Pushcut (Apple Shortcuts webhook) ───────────────────────────────────────

async function sendPushcut(config, message, title) {
  if (!config.pushcutWebhook) {
    console.warn('[push/pushcut] Webhook URL not configured')
    return
  }
  const fetch = require('node-fetch')
  const res = await fetch(config.pushcutWebhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, text: message })
  })
  if (!res.ok) console.warn(`[push/pushcut] HTTP ${res.status}`)
  else console.log('[push/pushcut] Sent:', title)
}

module.exports = { sendPush, getConfig, saveConfig }
