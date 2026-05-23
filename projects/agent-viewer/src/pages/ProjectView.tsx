import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate, useParams } from 'react-router-dom'
import AgentCard from '../components/AgentCard'
import HelperBadge from '../components/HelperBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import { getFile, listDir } from '../lib/github'
import { useRosterData } from '../lib/RosterContext'
import { getProjectDocDirectories } from '../lib/projectPaths'
import type { ProjectDoc } from '../lib/types'

function getDocTitle(markdown: string, filename: string) {
  return markdown.match(/^#\s+(.+)$/m)?.[1]?.trim() || filename.replace(/\.md$/i, '')
}

export default function ProjectView() {
  const navigate = useNavigate()
  const { slug } = useParams()
  const { roster, loading, error } = useRosterData()
  const [docs, setDocs] = useState<ProjectDoc[]>([])
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [docsError, setDocsError] = useState<string | null>(null)
  const [activeDoc, setActiveDoc] = useState('')

  const project = useMemo(() => roster?.projects.find((entry) => entry.slug === slug) ?? null, [roster, slug])

  useEffect(() => {
    let cancelled = false

    async function loadDocs() {
      if (!project) return
      setLoadingDocs(true)
      setDocsError(null)

      try {
        const directories = getProjectDocDirectories(project)
        const directoryResults = await Promise.all(directories.map((directory) => listDir(directory)))
        const uniqueFiles = new Map<string, { name: string; path: string }>()

        directoryResults.flat().forEach((entry) => {
          if (entry.type === 'file' && entry.name.toLowerCase().endsWith('.md')) {
            uniqueFiles.set(entry.path, { name: entry.name, path: entry.path })
          }
        })

        const orderedFiles = [...uniqueFiles.values()].sort((left, right) => {
          if (left.name === 'PROJECT.md') return -1
          if (right.name === 'PROJECT.md') return 1
          return left.name.localeCompare(right.name)
        })

        const loadedDocs = await Promise.all(
          orderedFiles.map(async (file) => {
            const rawMarkdown = await getFile(file.path)
            return {
              filename: file.name,
              title: getDocTitle(rawMarkdown, file.name),
              filePath: file.path,
              rawMarkdown
            }
          })
        )

        if (!cancelled) {
          setDocs(loadedDocs)
          setActiveDoc((current) => current || loadedDocs[0]?.filePath || '')
        }
      } catch (loadError) {
        if (!cancelled) {
          setDocsError(loadError instanceof Error ? loadError.message : 'Unable to load project documents.')
        }
      } finally {
        if (!cancelled) {
          setLoadingDocs(false)
        }
      }
    }

    void loadDocs()

    return () => {
      cancelled = true
    }
  }, [project])

  if (loading) {
    return <LoadingSpinner label="Loading project roster..." skeletonCards={3} />
  }

  if (error || !project) {
    return (
      <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-red-100">
        <button type="button" onClick={() => navigate('/')} className="mb-4 text-sm text-red-100/80 hover:text-white">
          ← Back to Dashboard
        </button>
        <h1 className="text-xl font-semibold">Project not available</h1>
        <p className="mt-2 text-sm text-red-100/80">{error ?? 'The requested project could not be found.'}</p>
      </div>
    )
  }

  const currentDoc = docs.find((doc) => doc.filePath === activeDoc) ?? docs[0]

  return (
    <div className="space-y-6">
      <button type="button" onClick={() => navigate('/')} className="text-sm text-slate-400 hover:text-white">
        ← Back to Dashboard
      </button>

      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Project {project.id}</p>
        <h1 className="text-3xl font-semibold text-white">{project.name}</h1>
        <p className="text-sm text-slate-400">Lead: {project.leadAgent.agentName} · {project.statusLabel}</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[40%_60%]">
        <section className="space-y-6">
          <div>
            <h2 className="mb-3 text-lg font-semibold text-white">Lead agent</h2>
            <AgentCard agent={project.leadAgent} prominent status={{ emoji: project.status, label: project.statusLabel }} />
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold text-white">Specialists</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {project.specialists.map((agent) => (
                <AgentCard key={agent.agentName} agent={agent} status={{ emoji: project.status, label: project.statusLabel }} />
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold text-white">Helper Agents</h2>
            <div className="flex flex-wrap gap-2">
              {project.helpers.length > 0 ? (
                project.helpers.map((helper) => <HelperBadge key={helper.agentName} helper={helper} />)
              ) : (
                <p className="text-sm text-slate-400">No helper agents listed.</p>
              )}
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900/70 p-4 sm:p-6">
          <div className="mb-4 flex flex-wrap gap-2 border-b border-slate-800 pb-4">
            {loadingDocs && docs.length === 0 ? (
              <LoadingSpinner label="Loading docs..." />
            ) : docs.length > 0 ? (
              docs.map((doc) => (
                <button
                  key={doc.filePath}
                  type="button"
                  onClick={() => setActiveDoc(doc.filePath)}
                  className={`rounded-full px-3 py-1.5 text-sm transition ${
                    currentDoc?.filePath === doc.filePath
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                >
                  {doc.filename}
                </button>
              ))
            ) : (
              <span className="text-sm text-slate-400">No markdown docs found for this project yet.</span>
            )}
          </div>

          {docsError && <p className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">{docsError}</p>}

          {currentDoc ? (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-semibold text-white">{currentDoc.title}</h2>
                <p className="mt-1 text-xs text-slate-500">{currentDoc.filePath}</p>
              </div>
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentDoc.rawMarkdown}</ReactMarkdown>
              </div>
            </div>
          ) : !loadingDocs ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
              No project docs available.
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
