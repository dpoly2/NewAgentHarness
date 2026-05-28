const fs = require('fs')
const path = require('path')

const root = path.join(__dirname, '..')
const dataDir = path.join(root, 'data')
const configPath = path.join(dataDir, 'config.json')
const statePath = path.join(dataDir, 'state.json')
const requestsPath = path.join(dataDir, 'requests.json')

function readJson(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'))
  } catch {
    return fallback
  }
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, 'utf8')
}

function daysUntil(dateString, now = new Date()) {
  const target = new Date(`${dateString}T09:00:00-05:00`)
  return Math.ceil((target.getTime() - now.getTime()) / 86400000)
}

function classifyRequest(message) {
  const haystack = `${message.subject || ''} ${message.snippet || ''}`.toLowerCase()
  if (/(advertis|sponsor|promo|promotion)/.test(haystack)) return 'advertising'
  if (/(submit|submission|article|story|press release|announcement)/.test(haystack)) return 'submission'
  if (/(event|calendar|save the date)/.test(haystack)) return 'event'
  if (/(unsubscribe|remove me|stop sending)/.test(haystack)) return 'unsubscribe'
  return 'general'
}

function buildSummary(config, state, requests) {
  const openRequests = requests.filter((item) => item.status !== 'closed')
  const urgent = openRequests.filter((item) => item.priority === 'high')
  const daysToNewsletter = daysUntil(config.newsletter.nextIssueTargetDate)
  const newsletterStatus = daysToNewsletter <= 7
    ? `Newsletter window is active: target send is ${config.newsletter.nextIssueTargetDate}.`
    : `Next newsletter target is ${config.newsletter.nextIssueTargetDate}.`

  return {
    generatedAt: new Date().toISOString(),
    health: urgent.length ? 'yellow' : 'green',
    newsletterStatus,
    openRequestCount: openRequests.length,
    urgentRequestCount: urgent.length,
    watchAddress: config.gmail.watchAddress,
    lastSuccessfulCheckAt: state.lastSuccessfulCheckAt,
    nextRecommendedCheck: 'Every morning, plus once after any Constant Contact campaign is sent.'
  }
}

function run() {
  const config = readJson(configPath, {})
  const state = readJson(statePath, {})
  const requests = readJson(requestsPath, [])
  const now = new Date().toISOString()

  const updatedRequests = requests.map((request) => ({
    ...request,
    type: request.type || classifyRequest(request)
  }))

  const updatedState = {
    ...state,
    lastLocalCheckAt: now,
    monitorMode: process.env.GMAIL_CLIENT_ID ? 'gmail-api-ready' : 'local-app',
    setupStatus: process.env.GMAIL_CLIENT_ID
      ? 'Gmail API environment variables detected.'
      : 'Waiting for Gmail OAuth/API credentials or a Codex Gmail connector for thesigmasignal.1stvp1914@gmail.com.',
    summary: buildSummary(config, state, updatedRequests)
  }

  writeJson(requestsPath, updatedRequests)
  writeJson(statePath, updatedState)

  if (process.argv.includes('--check')) {
    console.log(JSON.stringify(updatedState.summary, null, 2))
    return
  }

  console.log(`Checked ${config.gmail.watchAddress}. Open requests: ${updatedState.summary.openRequestCount}. Health: ${updatedState.summary.health}.`)
}

run()
