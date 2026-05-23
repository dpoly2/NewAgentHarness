import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate, useParams } from 'react-router-dom'
import LoadingSpinner from '../components/LoadingSpinner'
import { getFileWithFallback } from '../lib/github'
import { parseAgent } from '../lib/parseAgent'
import { useRosterData } from '../lib/RosterContext'
import { getAgentPathCandidates } from '../lib/projectPaths'
import type { AgentIdentity } from '../lib/types'

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function extractSection(markdown: string, heading: string) {
  return markdown.match(new RegExp(`##\\s+${escapeRegex(heading)}([\\s\\S]*?)(?=\\n##\\s+|$)`, 'i'))?.[1]?.trim() ?? ''
}

function extractIdentityFields(markdown: string) {
  const section = extractSection(markdown, 'Identity')
  return section
    .split(/\r?\n/)
    .map((line) => line.match(/-\s+\*\*(.+?):\*\*\s*(.+)/))
    .filter((value): value is RegExpMatchArray => Boolean(value))
    .reduce<Record<string, string>>((accumulator, match) => {
      accumulator[match[1]] = match[2].trim()
      return accumulator
    }, {})
}

function extractKeyFiles(markdown: string) {
  const section = extractSection(markdown, 'Key Files')
  return section
    .split(/\r?\n/)
    .map((line) => line.match(/-\s+`?([^`]+)`?/))
    .filter((value): value is RegExpMatchArray => Boolean(value))
    .map((value) => value[1].trim())
}

export default function AgentView() {
  const navigate = useNavigate()
  const { '*': rawParam } = useParams()
  const { roster, loading: rosterLoading } = useRosterData()
  const [agent, setAgent] = useState<AgentIdentity | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [identityFields, setIdentityFields] = useState<Record<string, string>>({})
  const [delegationRules, setDelegationRules] = useState('')
  const [keyFiles, setKeyFiles] = useState<string[]>([])

  const decodedPath = decodeURIComponent(rawParam ?? '')

  const agentLookup = useMemo(() => {
    if (!roster) return new Map<string, string>()

    const entries: Array<[string, string]> = roster.projects.flatMap((project) => [
      [project.leadAgent.agentName, project.leadAgent.filePath],
      ...project.specialists.map((specialist) => [specialist.agentName, specialist.filePath] as [string, string]),
      ...project.helpers.map((helper) => [helper.agentName, helper.filePath] as [string, string])
    ])

    roster.sharedAgents.forEach((shared) => entries.push([shared.agentName, shared.filePath]))
    return new Map(entries)
  }, [roster])

  useEffect(() => {
    let cancelled = false

    async function loadAgent() {
      if (!decodedPath) {
        setError('Missing agent file path.')
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const result = await getFileWithFallback(getAgentPathCandidates(decodedPath))
        const parsed = parseAgent(result.content, result.path)

        if (!cancelled) {
          setAgent(parsed)
          setIdentityFields(extractIdentityFields(result.content))
          setDelegationRules(extractSection(result.content, 'Delegation Rules'))
          setKeyFiles(extractKeyFiles(result.content))
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Unable to load agent markdown.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadAgent()

    return () => {
      cancelled = true
    }
  }, [decodedPath])

  const projectMatch = useMemo(() => {
    if (!roster || !agent) return null

    return roster.projects.find(
      (project) =>
        project.leadAgent.agentName === agent.agentName ||
        project.specialists.some((specialist) => specialist.agentName === agent.agentName) ||
        project.helpers.some((helper) => helper.agentName === agent.agentName)
    )
  }, [agent, roster])

  const mentionedAgents = useMemo(() => {
    const names = [...agentLookup.keys()]
    return names.filter((name) => delegationRules.includes(name))
  }, [agentLookup, delegationRules])

  if (loading || rosterLoading) {
    return <LoadingSpinner label="Loading agent profile..." />
  }

  if (error || !agent) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">
        <button type="button" onClick={() => navigate(-1)} className="mb-4 text-sm text-red-100/80 hover:text-white">
          ← Back
        </button>
        <h1 className="text-xl font-semibold">Unable to load agent</h1>
        <p className="mt-2 text-sm text-red-100/80">{error ?? 'Unknown agent error.'}</p>
      </div>
    )
  }

  const projectName = projectMatch?.name || agent.project || identityFields.Project || 'Shared'
  const role = agent.role || identityFields.Role || identityFields.Specialty || 'Unspecified'

  return (
    <div className="space-y-6">
      <div className="space-y-3 text-sm text-slate-400">
        <button type="button" onClick={() => navigate(-1)} className="hover:text-white">
          ← Back
        </button>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={() => navigate('/')} className="hover:text-white">Dashboard</button>
          <span>›</span>
          {projectMatch ? (
            <button type="button" onClick={() => navigate(`/project/${projectMatch.slug}`)} className="hover:text-white">
              {projectMatch.name}
            </button>
          ) : (
            <span>{projectName}</span>
          )}
          <span>›</span>
          <span className="text-slate-200">{agent.agentName}</span>
        </div>
      </div>

      <header className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500">{agent.type}</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">{agent.agentName}</h1>
        <p className="mt-2 max-w-3xl text-slate-300">{role}</p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Object.entries({
            Project: projectName,
            Type: identityFields.Type || agent.type,
            Role: role,
            ...(identityFields['Assigned By'] ? { 'Assigned By': identityFields['Assigned By'] } : {}),
            ...(agent.status ? { Status: agent.status } : {})
          }).map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
              <p className="mt-2 text-sm text-slate-100">{value}</p>
            </div>
          ))}
        </div>
      </header>

      {mentionedAgents.length > 0 && (
        <section className="rounded-3xl border border-blue-500/20 bg-blue-500/10 p-5">
          <h2 className="text-lg font-semibold text-white">Delegation Rules</h2>
          <p className="mt-2 text-sm text-slate-300">Referenced agents from the delegation section.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {mentionedAgents.map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => navigate(`/agent/${encodeURIComponent(agentLookup.get(name) ?? '')}`)}
                className="rounded-full border border-blue-400/30 bg-blue-500/10 px-3 py-1.5 text-sm text-blue-100 hover:border-blue-300 hover:bg-blue-500/20"
              >
                {name}
              </button>
            ))}
          </div>
        </section>
      )}

      {keyFiles.length > 0 && (
        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5">
          <h2 className="text-lg font-semibold text-white">Key Files</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {keyFiles.map((file) => (
              <span key={file} className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-200">
                {file}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{agent.rawMarkdown}</ReactMarkdown>
        </div>
      </section>
    </div>
  )
}
