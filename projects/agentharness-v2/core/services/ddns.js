/**
 * ClouDNS Dynamic DNS updater
 * Keeps your domain's A record pointed at this machine's public IP.
 * Supports both the ClouDNS Dynamic URL method (simplest) and the full REST API.
 *
 * Setup:
 *  Option A — Dynamic URL (recommended for home/dynamic IP):
 *    1. Log into ClouDNS → Dynamic DNS → Create Dynamic URL for your hostname
 *    2. Copy the "Dynamic URL" shown and paste into Settings → Remote Access
 *
 *  Option B — API credentials:
 *    1. Log into ClouDNS → API → create an API sub-user or use your auth-id + password
 *    2. Enter auth-id, auth-password, domain, and hostname in Settings
 */
const fs = require('fs')
const path = require('path')

const CONFIG_PATH = path.join(__dirname, '..', '..', 'data', 'cloudns_config.json')

let _interval = null
let _lastIp = null

const DEFAULTS = {
  enabled: false,
  method: 'dynamic-url', // 'dynamic-url' or 'api'
  dynamicUrl: '',        // ClouDNS Dynamic URL (Option A)
  authId: '',            // ClouDNS auth-id (Option B)
  authPassword: '',      // ClouDNS auth-password (Option B)
  domain: '',            // e.g. example.com (Option B)
  host: '@',             // subdomain, @ for root, or 'home' for home.example.com (Option B)
  ttl: 300,              // seconds
  updateIntervalMin: 5   // how often to check (minutes)
}

function getConfig() {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8')) }
    }
  } catch (e) { /* ignore */ }
  return { ...DEFAULTS }
}

function saveConfig(updates) {
  const config = { ...getConfig(), ...updates }
  const dir = path.dirname(CONFIG_PATH)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2))
  return config
}

/** Get this machine's current public IPv4 address */
async function getPublicIp() {
  let fetch
  try { fetch = require('node-fetch') } catch (e) { fetch = global.fetch }

  const sources = [
    'https://api.ipify.org?format=text',
    'https://icanhazip.com',
    'https://checkip.amazonaws.com'
  ]
  for (const url of sources) {
    try {
      const res = await fetch(url)
      if (res.ok) {
        const ip = (await res.text()).trim()
        if (/^\d+\.\d+\.\d+\.\d+$/.test(ip)) return ip
      }
    } catch (e) { /* try next */ }
  }
  throw new Error('Could not determine public IP address')
}

/**
 * Update ClouDNS record using the Dynamic URL method.
 * ClouDNS provides a URL like: https://ipv4.cloudns.net/api/dynamicURL/?q=<token>
 * Just call it with &ip=YOUR_IP
 */
async function updateViaDynamicUrl(dynamicUrl, ip) {
  let fetch
  try { fetch = require('node-fetch') } catch (e) { fetch = global.fetch }

  // Append IP — ClouDNS Dynamic URL already has ?q=token
  const sep = dynamicUrl.includes('?') ? '&' : '?'
  const url = `${dynamicUrl.trim()}${sep}ip=${ip}`
  const res = await fetch(url)
  const text = await res.text()
  try {
    const data = JSON.parse(text)
    if (data.status !== 'Success' && data.status !== 'IP address is the same') {
      throw new Error(`ClouDNS error: ${data.status} — ${data.statusDescription || ''}`)
    }
    return data.status
  } catch (e) {
    if (e.message.startsWith('ClouDNS')) throw e
    throw new Error(`ClouDNS unexpected response: ${text.slice(0, 100)}`)
  }
}

/**
 * Update ClouDNS A record using the REST API (Option B).
 */
async function updateViaApi(config, ip) {
  let fetch
  try { fetch = require('node-fetch') } catch (e) { fetch = global.fetch }

  const base = 'https://api.cloudns.net/dns'
  const auth = `auth-id=${encodeURIComponent(config.authId)}&auth-password=${encodeURIComponent(config.authPassword)}`

  // List A records to find the record ID
  const listUrl = `${base}/records.json?${auth}&domain-name=${encodeURIComponent(config.domain)}&type=A&host=${encodeURIComponent(config.host)}`
  const listRes = await fetch(listUrl)
  if (!listRes.ok) throw new Error(`ClouDNS API ${listRes.status}`)
  const records = await listRes.json()
  if (records.status === 'Failed') throw new Error(`ClouDNS: ${records.statusDescription}`)

  const existing = Object.values(records).find(r => typeof r === 'object' && (r.host === config.host || (config.host === '@' && !r.host)))

  if (existing) {
    if (existing.record === ip) return 'IP address is the same'
    const modUrl = `${base}/mod-record.json?${auth}&domain-name=${encodeURIComponent(config.domain)}&record-id=${existing.id}&host=${encodeURIComponent(config.host)}&type=A&record=${ip}&ttl=${config.ttl}`
    const modData = await (await fetch(modUrl, { method: 'POST' })).json()
    if (modData.status !== 'Success') throw new Error(`ClouDNS modify: ${modData.statusDescription}`)
    return 'Updated'
  } else {
    const addUrl = `${base}/add-record.json?${auth}&domain-name=${encodeURIComponent(config.domain)}&type=A&host=${encodeURIComponent(config.host)}&record=${ip}&ttl=${config.ttl}`
    const addData = await (await fetch(addUrl, { method: 'POST' })).json()
    if (addData.status !== 'Success') throw new Error(`ClouDNS create: ${addData.statusDescription}`)
    return 'Created'
  }
}

/**
 * Detect public IP and update DNS if it changed.
 * Returns { ip, status, updated } or throws on error.
 */
async function updateDdns(force = false) {
  const config = getConfig()
  if (!config.enabled) return { skipped: true, reason: 'DDNS disabled' }

  const ip = await getPublicIp()
  if (!force && ip === _lastIp) return { ip, status: 'IP address is the same', updated: false }

  let status
  if (config.method === 'dynamic-url') {
    if (!config.dynamicUrl) throw new Error('ClouDNS Dynamic URL not configured')
    status = await updateViaDynamicUrl(config.dynamicUrl, ip)
  } else {
    if (!config.authId || !config.domain) throw new Error('ClouDNS API credentials not configured')
    status = await updateViaApi(config, ip)
  }

  _lastIp = ip
  console.log(`[ddns] ${ip} → ${status}`)
  return { ip, status, updated: status !== 'IP address is the same' }
}

/** Start background DDNS polling loop */
function startDdns() {
  const config = getConfig()
  if (!config.enabled) return
  updateDdns(true).catch(e => console.warn('[ddns] Initial update failed:', e.message))
  if (_interval) clearInterval(_interval)
  const ms = (config.updateIntervalMin || 5) * 60 * 1000
  _interval = setInterval(() => updateDdns().catch(e => console.warn('[ddns] Update failed:', e.message)), ms)
  console.log(`[ddns] ClouDNS DDNS started — checking every ${config.updateIntervalMin} min`)
}

function stopDdns() {
  if (_interval) { clearInterval(_interval); _interval = null }
}

module.exports = { getConfig, saveConfig, updateDdns, startDdns, stopDdns, getPublicIp }
