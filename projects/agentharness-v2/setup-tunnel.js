#!/usr/bin/env node
/**
 * AgentHarness v2 — Cloudflare Tunnel Setup Script
 * Run: node setup-tunnel.js
 */
const { execSync, spawn } = require('child_process')
const readline = require('readline')
const path = require('path')
const fs = require('fs')

const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
const ask = q => new Promise(r => rl.question(q, r))

async function main() {
  console.log('\n╔══════════════════════════════════════════╗')
  console.log('║  AgentHarness Cloudflare Tunnel Setup    ║')
  console.log('╚══════════════════════════════════════════╝\n')

  // Check if cloudflared is installed
  let cfInstalled = false
  try { execSync('cloudflared --version', { stdio: 'ignore' }); cfInstalled = true } catch (e) {}

  if (!cfInstalled) {
    console.log('📦 Installing cloudflared...')
    try {
      execSync('npm install -g cloudflared', { stdio: 'inherit' })
      console.log('✅ cloudflared installed\n')
    } catch (e) {
      console.log('\nInstall manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/')
      process.exit(1)
    }
  } else {
    const ver = execSync('cloudflared --version').toString().trim()
    console.log(`✅ ${ver}\n`)
  }

  const choice = await ask('Setup type:\n  1. Quick tunnel (no domain, temporary URL)\n  2. Named tunnel (persistent, uses your domain)\nEnter 1 or 2: ')

  if (choice.trim() === '1') {
    console.log('\n🚀 Starting quick tunnel...')
    console.log('(This gives you a temporary HTTPS URL. For persistent access, use option 2 with a domain.)\n')
    const proc = spawn('cloudflared', ['tunnel', '--url', 'http://localhost:4000'], { stdio: 'inherit' })
    proc.on('error', e => console.error('Failed to start tunnel:', e.message))
    rl.close()
    return
  }

  // Named tunnel setup
  console.log('\n📋 Named Tunnel Setup')
  console.log('This requires a Cloudflare account and a domain managed by Cloudflare.\n')

  console.log('Step 1: Login to Cloudflare...')
  try { execSync('cloudflared tunnel login', { stdio: 'inherit' }) } catch (e) { console.log('Login failed or already logged in') }

  const tunnelName = await ask('\nTunnel name (default: agentharness): ') || 'agentharness'

  console.log(`\nStep 2: Creating tunnel "${tunnelName}"...`)
  let tunnelId = ''
  try {
    const out = execSync(`cloudflared tunnel create ${tunnelName}`).toString()
    console.log(out)
    const m = out.match(/Created tunnel (\S+)/)
    if (m) tunnelId = m[1]
  } catch (e) {
    console.log('Tunnel may already exist. Continuing...')
    try {
      const list = execSync('cloudflared tunnel list').toString()
      const m = list.match(new RegExp(`(\\S+)\\s+${tunnelName}`))
      if (m) tunnelId = m[1]
    } catch (e2) {}
  }

  const domain = await ask('\nYour domain (e.g. agentharness.yourdomain.com): ')

  if (domain && tunnelId) {
    console.log(`\nStep 3: Routing ${domain} → ${tunnelName}...`)
    try { execSync(`cloudflared tunnel route dns ${tunnelName} ${domain}`, { stdio: 'inherit' }) } catch (e) { console.log('Route may already exist') }
  }

  // Write config
  const configDir = path.join(process.env.HOME || process.env.USERPROFILE, '.cloudflared')
  if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true })

  const configPath = path.join(configDir, 'config.yml')
  const config = `tunnel: ${tunnelName}
credentials-file: ${configDir}/${tunnelId}.json

ingress:
  - hostname: ${domain || `${tunnelName}.yourdomain.com`}
    service: http://localhost:4000
  - service: http_status:404
`
  fs.writeFileSync(configPath, config)
  console.log(`\n✅ Config written to ${configPath}`)

  // Write npm script
  const pkgPath = path.join(__dirname, 'package.json')
  try {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'))
    pkg.scripts['tunnel'] = `cloudflared tunnel run ${tunnelName}`
    fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2))
    console.log('✅ Added "npm run tunnel" script to package.json')
  } catch (e) {}

  console.log(`
╔══════════════════════════════════════════╗
║  Setup Complete!                          ║
║                                           ║
║  Start AgentHarness:                      ║
║    npm run core          (server only)    ║
║    npm run electron      (desktop app)    ║
║                                           ║
║  Start Cloudflare Tunnel:                 ║
║    npm run tunnel                         ║
║                                           ║
║  Web access: https://${(domain || 'your-domain').slice(0,20).padEnd(20)} ║
╚══════════════════════════════════════════╝
`)
  rl.close()
}

main().catch(e => { console.error(e); process.exit(1) })
