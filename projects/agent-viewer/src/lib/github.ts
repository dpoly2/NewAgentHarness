const BASE = 'https://api.github.com'
const REPO = import.meta.env.VITE_GITHUB_REPO || 'dpoly2/AgentHarness'
const PAT = import.meta.env.VITE_GITHUB_PAT || ''
const BRANCH = import.meta.env.VITE_GITHUB_BRANCH || 'main'
const CACHE_TTL = 15 * 60 * 1000

export interface DirectoryEntry {
  name: string
  path: string
  type: 'file' | 'dir'
}

function cacheKey(path: string) {
  return `agv:${path}`
}

function getCache(path: string): string | null {
  try {
    const raw = localStorage.getItem(cacheKey(path))
    if (!raw) return null
    const { content, ts } = JSON.parse(raw) as { content: string; ts: number }
    if (Date.now() - ts > CACHE_TTL) {
      localStorage.removeItem(cacheKey(path))
      return null
    }
    return content
  } catch {
    return null
  }
}

function setCache(path: string, content: string) {
  try {
    localStorage.setItem(cacheKey(path), JSON.stringify({ content, ts: Date.now() }))
  } catch {
    // Ignore storage failures.
  }
}

function decodeBase64(content: string) {
  const binary = atob(content.replace(/\n/g, ''))
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0))
  return new TextDecoder().decode(bytes)
}

function normalizeRepoPath(path: string) {
  return path.replace(/^\/+/, '').replace(/\\/g, '/').replace(/\/+/g, '/')
}

export function clearCache() {
  const keys: string[] = []
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i)
    if (key?.startsWith('agv:')) keys.push(key)
  }
  keys.forEach((key) => localStorage.removeItem(key))
}

const headers: Record<string, string> = {
  Accept: 'application/vnd.github+json',
  ...(PAT ? { Authorization: `token ${PAT}` } : {})
}

export async function getFile(path: string): Promise<string> {
  const normalized = normalizeRepoPath(path)
  const cached = getCache(normalized)
  if (cached) return cached

  const url = `${BASE}/repos/${REPO}/contents/${normalized}?ref=${BRANCH}`
  const response = await fetch(url, { headers })
  if (!response.ok) throw new Error(`GitHub API error ${response.status} for ${normalized}`)

  const data = await response.json()
  const content = decodeBase64(data.content)
  setCache(normalized, content)
  return content
}

export async function listDir(path: string): Promise<DirectoryEntry[]> {
  const normalized = normalizeRepoPath(path)
  const dirKey = `dir:${normalized}`
  const cached = getCache(dirKey)
  if (cached) return JSON.parse(cached) as DirectoryEntry[]

  const url = `${BASE}/repos/${REPO}/contents/${normalized}?ref=${BRANCH}`
  const response = await fetch(url, { headers })
  if (!response.ok) return []

  const data = await response.json()
  const result = Array.isArray(data)
    ? data.map((entry: { name: string; path: string; type: 'file' | 'dir' }) => ({
        name: entry.name,
        path: entry.path,
        type: entry.type
      }))
    : []

  setCache(dirKey, JSON.stringify(result))
  return result
}

export async function getFileWithFallback(paths: string[]) {
  const seen = new Set<string>()
  let lastError: unknown

  for (const rawPath of paths) {
    const path = normalizeRepoPath(rawPath)
    if (!path || seen.has(path)) continue
    seen.add(path)

    try {
      const content = await getFile(path)
      return { path, content }
    } catch (error) {
      lastError = error
    }
  }

  throw lastError ?? new Error('No readable file paths found')
}
