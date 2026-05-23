import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { clearCache, getFileWithFallback } from './github'
import { parseRoster } from './parseRoster'
import type { RosterData } from './types'

interface RosterContextValue {
  roster: RosterData | null
  loading: boolean
  error: string | null
  reload: () => Promise<void>
}

const RosterContext = createContext<RosterContextValue | undefined>(undefined)

export function RosterProvider({ children }: { children: React.ReactNode }) {
  const [roster, setRoster] = useState<RosterData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadRoster = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await getFileWithFallback(['.agents/agents/roster.md', 'agents/roster.md'])
      setRoster(parseRoster(result.content))
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load roster data.')
    } finally {
      setLoading(false)
    }
  }, [])

  const reload = useCallback(async () => {
    clearCache()
    await loadRoster()
  }, [loadRoster])

  useEffect(() => {
    void loadRoster()
  }, [loadRoster])

  const value = useMemo(() => ({ roster, loading, error, reload }), [error, loading, reload, roster])

  return <RosterContext.Provider value={value}>{children}</RosterContext.Provider>
}

export function useRosterData() {
  const context = useContext(RosterContext)
  if (!context) {
    throw new Error('useRosterData must be used inside RosterProvider')
  }
  return context
}
