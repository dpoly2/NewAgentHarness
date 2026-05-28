import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

const API_BASE = import.meta.env.VITE_API_URL || ''

let _socket = null

function getSocket() {
  if (!_socket) {
    const token = localStorage.getItem('agentharness_token')
    _socket = io(API_BASE || window.location.origin, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      auth: token ? { token } : {}
    })
  }
  return _socket
}

/** Get stored access token (used for remote/protected deployments) */
export function getStoredToken() { return localStorage.getItem('agentharness_token') || '' }
export function setStoredToken(t) {
  if (t) localStorage.setItem('agentharness_token', t)
  else localStorage.removeItem('agentharness_token')
  _socket = null // force reconnect with new token
}

export function useSocket(events = {}) {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const socket = getSocket()
    socket.on('connect', () => setConnected(true))
    socket.on('disconnect', () => setConnected(false))
    if (socket.connected) setConnected(true)

    const handlers = []
    for (const [event, handler] of Object.entries(events)) {
      socket.on(event, handler)
      handlers.push([event, handler])
    }
    return () => {
      handlers.forEach(([e, h]) => socket.off(e, h))
    }
  }, [])

  return { connected, socket: getSocket() }
}

export async function api(path, options = {}) {
  const url = `${API_BASE}/api${path}`
  const method = options.method || 'GET'
  const token = getStoredToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(url, {
    method,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || res.statusText)
  }
  return res.json()
}

export { getSocket }
