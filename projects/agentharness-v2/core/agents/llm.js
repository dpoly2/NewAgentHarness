/**
 * LLM Adapter — supports Ollama, OpenAI, Anthropic, GitHub Models
 */
const path = require('path')
const fs = require('fs')

const CONFIG_PATH = path.join(__dirname, '..', '..', 'data', 'ai_config.json')

const PRESETS = {
  ollama:    { baseUrl: 'http://localhost:11434/v1', model: 'llama3.2' },
  openai:    { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  anthropic: { baseUrl: 'https://api.anthropic.com/v1', model: 'claude-3-haiku-20240307' },
  github:    { baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini' }
}

let _config = null

function loadConfig() {
  if (_config) return _config
  const defaults = { provider: 'ollama', baseUrl: 'http://localhost:11434/v1', apiKey: '', model: 'llama3.2', enabled: false }
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      _config = { ...defaults, ...JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8').replace(/^\uFEFF/, '')) }
    } else {
      _config = defaults
    }
  } catch (e) { _config = defaults }
  return _config
}

function reloadConfig() { _config = null; return loadConfig() }
function saveConfig(update) {
  const c = { ...loadConfig(), ...update }
  _config = c
  const dir = path.dirname(CONFIG_PATH)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(c, null, 2))
  return c
}
function getConfig() { return loadConfig() }

async function callLLM(messages, { maxTokens = 2000, stream = false } = {}) {
  let fetch
  try { fetch = require('node-fetch') } catch (e) { fetch = global.fetch }

  const config = loadConfig()
  if (!config.enabled) {
    return '[AI not configured. Go to Settings → AI Provider to enable.]\n\nTo configure: set your provider (Ollama for local, OpenAI, or GitHub Models), enter your API key if needed, and toggle AI on.'
  }

  const isAnthropic = config.provider === 'anthropic'
  const url = isAnthropic ? `${config.baseUrl}/messages` : `${config.baseUrl}/chat/completions`

  const headers = { 'Content-Type': 'application/json' }
  if (config.apiKey) headers['Authorization'] = `Bearer ${config.apiKey}`
  if (isAnthropic) { headers['x-api-key'] = config.apiKey; headers['anthropic-version'] = '2023-06-01'; delete headers['Authorization'] }

  let body
  if (isAnthropic) {
    const sysMsg = messages.find(m => m.role === 'system')
    const userMsgs = messages.filter(m => m.role !== 'system')
    body = JSON.stringify({ model: config.model, max_tokens: maxTokens, system: sysMsg?.content || '', messages: userMsgs })
  } else {
    body = JSON.stringify({ model: config.model, messages, max_tokens: maxTokens, stream: false })
  }

  const res = await fetch(url, { method: 'POST', headers, body })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`LLM API error ${res.status}: ${err.slice(0, 200)}`)
  }

  const data = await res.json()
  if (isAnthropic) return data.content?.[0]?.text || ''
  return data.choices?.[0]?.message?.content || ''
}

async function* streamLLM(messages, { maxTokens = 2000 } = {}) {
  let fetch
  try { fetch = require('node-fetch') } catch (e) { fetch = global.fetch }

  const config = loadConfig()
  if (!config.enabled) {
    yield '[AI not configured. Go to Settings → AI Provider to enable.]'
    return
  }

  const isAnthropic = config.provider === 'anthropic'
  const url = isAnthropic ? `${config.baseUrl}/messages` : `${config.baseUrl}/chat/completions`

  const headers = { 'Content-Type': 'application/json' }
  if (config.apiKey) headers['Authorization'] = `Bearer ${config.apiKey}`
  if (isAnthropic) { headers['x-api-key'] = config.apiKey; headers['anthropic-version'] = '2023-06-01'; delete headers['Authorization'] }

  let body
  if (isAnthropic) {
    const sysMsg = messages.find(m => m.role === 'system')
    const userMsgs = messages.filter(m => m.role !== 'system')
    body = JSON.stringify({ model: config.model, max_tokens: maxTokens, system: sysMsg?.content || '', messages: userMsgs, stream: true })
  } else {
    body = JSON.stringify({ model: config.model, messages, max_tokens: maxTokens, stream: true })
  }

  const res = await fetch(url, { method: 'POST', headers, body })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`LLM API error ${res.status}: ${err.slice(0, 200)}`)
  }

  for await (const chunk of res.body) {
    const lines = chunk.toString().split('\n').filter(l => l.startsWith('data: '))
    for (const line of lines) {
      const data = line.slice(6).trim()
      if (data === '[DONE]') return
      try {
        const parsed = JSON.parse(data)
        if (isAnthropic) {
          const delta = parsed.delta?.text
          if (delta) yield delta
        } else {
          const delta = parsed.choices?.[0]?.delta?.content
          if (delta) yield delta
        }
      } catch (e) { /* skip malformed chunks */ }
    }
  }
}

module.exports = { callLLM, streamLLM, getConfig, saveConfig, reloadConfig }
