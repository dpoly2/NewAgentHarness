import { useState, useEffect, useRef, useCallback } from 'react'
import { marked } from 'marked'
import { api, getSocket } from '../hooks/useSocket'

marked.setOptions({ breaks: true, gfm: true })

function generateId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }

const PROJECT_ICONS = { xftc:'🌐', yepc:'🏟️', elevation:'🎭', 'pbs-foundation':'🏛️', nutrue:'👕', smithcap:'🏢', s2tdesigns:'🎨', 'social-media':'📱', 'solar-repair':'☀️', ministry:'⛪', finance:'💰', personal:'🗓️', 'sigma-signal':'📰', global:'✨' }

export default function Command({ roster }) {
  const [conversations, setConversations] = useState([])
  const [activeConvId, setActiveConvId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamBuffer, setStreamBuffer] = useState('')
  const [projectScope, setProjectScope] = useState('global')
  const [showNewConv, setShowNewConv] = useState(false)
  const [chatError, setChatError] = useState('')
  const chatRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(null)

  // Load conversations
  useEffect(() => {
    api('/conversations').then(convs => {
      setConversations(convs)
      if (convs.length > 0 && !activeConvId) {
        setActiveConvId(convs[0].id)
      } else if (convs.length === 0) {
        createNewConversation()
      }
    }).catch(console.error)
  }, [])

  // Load messages when conversation changes
  useEffect(() => {
    if (!activeConvId) return
    api(`/conversations/${activeConvId}/messages`).then(msgs => setMessages(msgs)).catch(console.error)
  }, [activeConvId])

  // Auto-scroll chat
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages, streamBuffer])

  async function createNewConversation() {
    try {
      setChatError('')
      const conv = await api('/conversations', { method: 'POST', body: { slug: projectScope, title: 'New Chat' } })
      if (!conv || !conv.id) throw new Error('Server returned an empty conversation. Try restarting the server.')
      setConversations(prev => [conv, ...prev.filter(c => c.id !== conv.id)])
      setActiveConvId(conv.id)
      setMessages([])
    } catch (e) {
      setChatError(`Could not create conversation: ${e.message}`)
    }
  }

  async function sendMessage() {
    if (!input.trim() || streaming) return
    if (!activeConvId) {
      setChatError('No active conversation. Click "+ New Chat" to start one.')
      return
    }
    const text = input.trim()
    setInput('')
    setChatError('')

    // Optimistic user message
    const tempId = 'temp-' + generateId()
    setMessages(prev => [...prev, { id: tempId, role: 'user', content: text, created_at: new Date().toISOString() }])
    setStreaming(true)
    setStreamBuffer('')

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
        body: JSON.stringify({ conversationId: activeConvId, message: text, projectSlug: projectScope === 'global' ? null : projectScope }),
        signal: controller.signal
      })

      if (!res.ok) throw new Error(`Chat API error ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let fullText = ''
      let sseLineBuffer = '' // accumulate partial SSE lines across TCP chunks
      let gotDone = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        sseLineBuffer += decoder.decode(value, { stream: true })
        const lines = sseLineBuffer.split('\n')
        sseLineBuffer = lines.pop() // keep incomplete last line buffered
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let data
          try { data = JSON.parse(line.slice(6)) } catch { continue }
          if (data.chunk) {
            fullText += data.chunk
            setStreamBuffer(fullText)
          }
          if (data.done) gotDone = true
        }
      }

      // Stream ended — reload persisted messages (includes AI response with parsed todos/tasks)
      if (gotDone || fullText) {
        try {
          const msgs = await api(`/conversations/${activeConvId}/messages`)
          if (Array.isArray(msgs) && msgs.length > 0) {
            setMessages(msgs)
          } else {
            // Server returned empty — construct messages from what we streamed
            setMessages(prev => [
              ...prev.filter(m => m.id !== tempId),
              { id: generateId(), role: 'user', content: text, created_at: new Date().toISOString() },
              { id: generateId(), role: 'assistant', content: fullText, agent_id: 'agentmajesty', created_at: new Date().toISOString() }
            ])
          }
        } catch {
          // Fetch failed — at minimum keep what was streamed visible
          setMessages(prev => [
            ...prev.filter(m => m.id !== tempId),
            { id: generateId(), role: 'user', content: text, created_at: new Date().toISOString() },
            { id: generateId(), role: 'assistant', content: fullText, agent_id: 'agentmajesty', created_at: new Date().toISOString() }
          ])
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setChatError(`Chat error: ${e.message}`)
        setMessages(prev => prev.filter(m => m.id !== tempId))
      }
    } finally {
      setStreaming(false)
      setStreamBuffer('')
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const projects = roster?.projects || []
  const activeConv = conversations.find(c => c.id === activeConvId)

  return (
    <div className="flex h-full overflow-hidden">
      {/* Conversation sidebar */}
      <div className="w-64 flex-shrink-0 bg-surface border-r border-surface-border flex flex-col">
        <div className="p-3 border-b border-surface-border">
          <button onClick={createNewConversation} className="btn-primary w-full justify-center text-sm">
            <span>＋</span> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => setActiveConvId(conv.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all group ${activeConvId === conv.id ? 'bg-brand/15 text-white' : 'text-gray-400 hover:text-white hover:bg-surface-lighter'}`}
            >
              <div className="flex items-center gap-2">
                <span className="text-base">{PROJECT_ICONS[conv.slug] || '💬'}</span>
                <span className="truncate flex-1">{conv.title || 'Untitled'}</span>
              </div>
              <div className="text-xs text-gray-600 mt-0.5 pl-6">{new Date(conv.updated_at).toLocaleDateString()}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-surface-border bg-surface-light flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-brand/20 flex items-center justify-center text-brand font-bold text-sm">AM</div>
          <div>
            <div className="font-semibold text-sm text-white">AgentMajesty</div>
            <div className="text-xs text-gray-500">Chief of Staff</div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <select
              value={projectScope}
              onChange={e => setProjectScope(e.target.value)}
              className="input text-xs py-1.5"
            >
              <option value="global">All Projects</option>
              {projects.map(p => (
                <option key={p.slug} value={p.slug}>
                  {PROJECT_ICONS[p.slug] || '📁'} {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Error banner */}
        {chatError && (
          <div className="px-5 py-2 bg-error/10 border-b border-error/20 text-error text-xs flex items-center gap-2 flex-shrink-0">
            ⚠️ {chatError}
            <button onClick={() => setChatError('')} className="ml-auto text-gray-500 hover:text-white">✕</button>
          </div>
        )}
        <div ref={chatRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && !streaming && (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-3">
              <div className="w-16 h-16 rounded-2xl bg-brand/10 flex items-center justify-center text-4xl">⭐</div>
              <div>
                <div className="text-lg font-semibold text-gray-300">AgentMajesty</div>
                <div className="text-sm mt-1">Your AI Chief of Staff. Ask me about any project,<br />or let me brief you on what needs attention today.</div>
              </div>
              <div className="flex gap-2 flex-wrap justify-center mt-4">
                {['Brief me on today\'s priorities', 'What\'s the XFTC status?', 'What grants are due soon?'].map(s => (
                  <button key={s} onClick={() => { setInput(s); inputRef.current?.focus() }}
                    className="text-xs px-3 py-1.5 rounded-full border border-surface-border hover:border-brand/50 hover:text-brand-light text-gray-400 transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={msg.role === 'user' ? 'chat-msg-user' : 'chat-msg-ai'}>
                {msg.role !== 'user' && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-brand-light">{msg.agent_id || 'AgentMajesty'}</span>
                    <span className="text-xs text-gray-600">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                )}
                <div className={`prose-dark text-sm ${msg.role === 'user' ? 'text-gray-100' : ''}`}
                  dangerouslySetInnerHTML={{ __html: marked(msg.content || '') }} />
              </div>
            </div>
          ))}

          {streaming && streamBuffer && (
            <div className="flex justify-start">
              <div className="chat-msg-ai">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-brand-light">AgentMajesty</span>
                </div>
                <div className="prose-dark text-sm" dangerouslySetInnerHTML={{ __html: marked(streamBuffer) }} />
              </div>
            </div>
          )}
          {streaming && !streamBuffer && (
            <div className="flex justify-start">
              <div className="chat-msg-ai">
                <div className="flex gap-1.5 items-center py-1">
                  <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-5 py-3 border-t border-surface-border flex-shrink-0 bg-surface">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message AgentMajesty... (Enter to send, Shift+Enter for new line)"
              rows={1}
              className="input flex-1 resize-none min-h-[44px] max-h-40 overflow-y-auto leading-relaxed"
              style={{ height: 'auto' }}
              onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px' }}
              disabled={streaming}
            />
            {streaming ? (
              <button onClick={() => abortRef.current?.abort()} className="btn-danger px-3 py-2.5 flex-shrink-0">⏹</button>
            ) : (
              <button onClick={sendMessage} disabled={!input.trim()} className="btn-primary px-3 py-2.5 flex-shrink-0 disabled:opacity-40">↑</button>
            )}
          </div>
          <div className="flex gap-1.5 mt-2 flex-wrap">
            {projects.slice(0, 6).map(p => (
              <button key={p.slug} onClick={() => setProjectScope(p.slug === projectScope ? 'global' : p.slug)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${projectScope === p.slug ? 'border-brand/50 bg-brand/10 text-brand-light' : 'border-surface-border text-gray-500 hover:border-gray-500'}`}>
                {PROJECT_ICONS[p.slug] || '📁'} {p.slug.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
