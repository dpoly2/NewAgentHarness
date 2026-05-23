import React, { useState, useEffect, useRef } from 'react'
import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })
function renderMarkdown(text) {
  try { return marked(String(text || '')) } catch (e) { return String(text || '') }
}

function statusLabel(s) {
  const map = { queued: 'Queued', running: 'Running', completed: 'Done', 'completed-with-issues': 'Has Issues', 'needs-agent': 'Needs Agent', idle: 'Idle', error: 'Error', ready: 'Ready' }
  return map[s] || (s ? s.charAt(0).toUpperCase() + s.slice(1) : '—')
}

export default function App(){
  const [agents, setAgents] = useState([])
  const [tasks, setTasks] = useState([])
  const [todos, setTodos] = useState([])
  const [todoFilter, setTodoFilter] = useState('active')
  const [newTodo, setNewTodo] = useState({ title: '', description: '', priority: 'medium', dueDate: '', tags: '' })
  const [issues, setIssues] = useState([])
  const [profile, setProfile] = useState(null)
  const [contacts, setContacts] = useState([])
  const [connectors, setConnectors] = useState([])
  const [projects, setProjects] = useState([])
  const [selected, setSelected] = useState(null)
  const [selectedTaskId, setSelectedTaskId] = useState(null)
  const [activeTab, setActiveTab] = useState('command')
  const [busy, setBusy] = useState(false)
  const [newAgentName, setNewAgentName] = useState('')
  const [newAgentRole, setNewAgentRole] = useState('')
  const [profileDraft, setProfileDraft] = useState({})
  const [newContact, setNewContact] = useState({ name: '', email: '', group: '', notes: '' })
  const [newConnector, setNewConnector] = useState({
    name: '',
    type: 'gmail',
    email: '',
    host: '',
    port: '587',
    username: '',
    password: '',
    fromEmail: '',
    accountName: '',
    clientId: '',
    clientSecret: '',
    accessToken: '',
    refreshToken: '',
    expiresAt: ''
  })
  const [chatInput, setChatInput] = useState('')
  const [learningQuestion, setLearningQuestion] = useState(null)
  const [chatGptExportPath, setChatGptExportPath] = useState('')
  const [importSummary, setImportSummary] = useState(null)
  const [mobileBridge, setMobileBridge] = useState(null)
  const [mobileInfo, setMobileInfo] = useState(null)
  const [mobileTestText, setMobileTestText] = useState('')
  const [projectImportPath, setProjectImportPath] = useState('')
  const [aiConfig, setAiConfig] = useState(null)
  const [aiConfigDraft, setAiConfigDraft] = useState({
    provider: 'ollama', baseUrl: 'http://localhost:11434/v1', apiKey: '', model: 'llama3.2', enabled: false
  })
  const [aiTestResult, setAiTestResult] = useState(null)
  const [isTyping, setIsTyping] = useState(false)
  const chatRef = useRef(null)
  const aiDraftInitialized = useRef(false)
  const [chatMessages, setChatMessages] = useState([
    { id: 0, from: 'AgentMajesty', text: "I'm AgentMajesty - your chief of staff. Tell me what needs to get done, ask for a status, or pick a prompt below." }
  ])

  const queuedTasks = tasks.filter(task => task.status === 'queued' || task.status === 'running')
  const completedTasks = tasks.filter(task => task.status === 'completed' || task.status === 'completed-with-issues')
  const openIssues = issues.filter(issue => issue.status !== 'resolved')
  const pendingTodos = todos.filter(t => t.status !== 'done')
  const selectedTask = tasks.find(task => task.id === selectedTaskId) || tasks[0] || null
  const readyConnectors = connectors.filter(connector => connector.status === 'ready')
  const latestProject = projects[0] || null
  const recentMemory = Array.isArray(profile?.memory) ? profile.memory.slice(0, 3) : []
  const quickPrompts = [
    'Teach Majesty',
    'Check newsletter campaign health',
    'Find grant opportunities',
    'What do you know about me?',
    'Review WordPress plugin tasks',
    'Status'
  ]
  const learningQuestions = [
    {
      id: 'decision_style',
      question: 'When a project gets messy, do you prefer a short recommendation, options with tradeoffs, or the full context first?'
    },
    {
      id: 'priority_filter',
      question: 'What makes something urgent for you: deadline, people impacted, money, reputation, or momentum?'
    },
    {
      id: 'communication_style',
      question: 'When I brief you, should I be blunt and minimal, warm and explanatory, or somewhere in the middle?'
    },
    {
      id: 'delegation_style',
      question: 'What should I handle automatically, and what should I always bring back to you before acting?'
    }
  ]

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        if (window.electron && window.electron.getAgents) {
          const maybe = window.electron.getAgents()
          const data = (maybe && typeof maybe.then === 'function') ? await maybe : maybe
          if (!mounted) return
          setAgents(data || [])
          if (data && data.length) setSelected(current => current || data[0].id)
        }
        if (window.electron && window.electron.invoke) {
          const taskData = await window.electron.invoke('read-tasks')
          if (mounted) {
            setTasks(taskData || [])
            if ((taskData || []).length) setSelectedTaskId(current => current || taskData[0].id)
          }
          const todoData = await window.electron.invoke('read-todos')
          if (mounted) setTodos(todoData || [])
          const issueData = await window.electron.invoke('read-issues')
          if (mounted) setIssues(issueData || [])
          const profileData = await window.electron.invoke('read-profile')
          if (mounted) {
            setProfile(profileData || null)
            setProfileDraft(profileData || {})
          }
          const contactData = await window.electron.invoke('read-contacts')
          if (mounted) setContacts(contactData || [])
          const connectorData = await window.electron.invoke('read-connectors')
          if (mounted) setConnectors(connectorData || [])
          const projectData = await window.electron.invoke('read-projects')
          if (mounted) setProjects(projectData || [])
          const mobileData = await window.electron.invoke('read-mobile-bridge')
          if (mounted) {
            setMobileBridge(mobileData?.config || null)
            setMobileInfo(mobileData?.info || null)
          }
          const aiData = await window.electron.invoke('read-ai-config')
          if (mounted && aiData?.config) {
            setAiConfig(aiData.config)
            if (!aiDraftInitialized.current) {
              aiDraftInitialized.current = true
              setAiConfigDraft(d => ({ ...d, ...aiData.config }))
            }
          }
        }
      } catch (e) {
        console.error('Failed to load agents', e)
      }
    }
    load()
    const t = setInterval(load, 3000)
    // Listen for real-time updates
    if (window.electron && window.electron.on) {
      window.electron.on('agents-updated', (data) => { if (mounted) setAgents(data || []) })
      window.electron.on('tasks-updated', (data) => { if (mounted) setTasks(data || []) })
      window.electron.on('issues-updated', (data) => { if (mounted) setIssues(data || []) })
      window.electron.on('profile-updated', (data) => { if (mounted) { setProfile(data || null); setProfileDraft(data || {}) } })
      window.electron.on('contacts-updated', (data) => { if (mounted) setContacts(data || []) })
      window.electron.on('connectors-updated', (data) => { if (mounted) setConnectors(data || []) })
    }
    return () => { mounted = false; clearInterval(t) }
  }, [])

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [chatMessages])

  const selAgent = (Array.isArray(agents) ? agents.find(a => a.id === selected) : null) || (Array.isArray(agents) ? agents[0] : null)
  const selAgentIssues = selAgent ? openIssues.filter(issue => issue.agentId === selAgent.id) : []
  const selAgentLearning = Array.isArray(selAgent?.learning) ? selAgent.learning.slice(0, 5) : []

  async function commandAgent(id, action) {
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      await window.electron.invoke('agent-command', { id, action })
      // Refresh local copy
      const maybe = window.electron.getAgents()
      const data = (maybe && typeof maybe.then === 'function') ? await maybe : maybe
      setAgents(data || [])
    } catch (e) {
      console.error('agent command failed', e)
    } finally {
      setBusy(false)
    }
  }

  async function addAgent(event) {
    event.preventDefault()
    const name = newAgentName.trim()
    if (!name || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const agents = await window.electron.invoke('add-agent', {
        name,
        role: newAgentRole.trim()
      })
      setAgents(agents || [])
      const added = (agents || []).find(a => a.name.toLowerCase() === name.toLowerCase())
      if (added) setSelected(added.id)
      setNewAgentName('')
      setNewAgentRole('')
    } catch (e) {
      console.error('add agent failed', e)
    } finally {
      setBusy(false)
    }
  }

  function answerLocalMajestyPrompt(message) {
    const normalized = message.toLowerCase()
    if (['status', 'queue', 'task status'].includes(normalized)) {
      return `Queue status: ${queuedTasks.length} queued, ${completedTasks.length} completed, ${agents.length} agents available, ${readyConnectors.length} connectors ready.`
    }
    if (normalized.includes('teach majesty') || normalized.includes('learn how i think') || normalized.includes('learn me')) {
      const next = learningQuestions.find(q => !profile?.memory?.some(item => item.topic === q.id)) || learningQuestions[0]
      setLearningQuestion(next)
      return next.question
    }
    if (normalized.includes('what can you do') || normalized === 'help') {
      return `I can learn your priorities, create tasks, assign agents, track execution, and keep you oriented like a chief of staff. I will follow your approval rule: ${profile?.approvalRules || 'ask before external actions'}.`
    }
    if (normalized.includes('what do you know about me') || normalized.includes('what do you know')) {
      const memory = recentMemory.map(item => `- ${item.text}`).join('\n')
      return `I know you as ${profile?.name || 'David'}, ${profile?.role || 'Director of Communications'}.\nPriorities: ${profile?.priorities || 'not set'}.\nStyle: ${profile?.communicationStyle || 'not set'}.\nRecent memory:\n${memory || '- No saved notes yet.'}`
    }
    if (normalized.includes('email list') || normalized.includes('contacts')) {
      if (!contacts.length) return 'Your email list is empty. Add contacts in the Chief of Staff panel.'
      return contacts.slice(0, 8).map(contact => `${contact.name} <${contact.email}>${contact.group ? ` · ${contact.group}` : ''}`).join('\n')
    }
    if (normalized.includes('connector') || normalized.includes('gmail') || normalized.includes('outlook') || normalized.includes('constant contact') || normalized.includes('smtp')) {
      if (!connectors.length) return 'No connectors are configured yet. Add Gmail, Outlook, SMTP, or Constant Contact in the Connectors panel.'
      return connectors.map(connector => `${connector.name}: ${connector.type} · ${connector.status}`).join('\n')
    }
    if (normalized.includes('project import') || normalized.includes('project history')) {
      return projects.length
        ? `Imported projects: ${projects.slice(0, 5).map(project => project.name).join(', ')}.`
        : 'No project history has been imported yet. Use the Projects tab to import a folder.'
    }
    if (normalized.includes('who is available')) {
      const available = agents.filter(agent => agent.name !== 'AgentMajesty' && agent.status !== 'running').map(agent => agent.name)
      return available.length ? `Available agents: ${available.join(', ')}.` : 'No specialized agents are idle right now.'
    }
    return null
  }

  async function submitChatMessage(message) {
    if (!message || busy || !window.electron || !window.electron.invoke) return
    const userMsg = { id: Date.now(), from: 'You', text: message }
    setChatMessages(prev => [...prev, userMsg])

    const normalized = message.toLowerCase()
    if (normalized.includes('teach majesty') || normalized.includes('learn how i think') || normalized.includes('learn me')) {
      const next = learningQuestions.find(q => !profile?.memory?.some(item => item.topic === q.id)) || learningQuestions[0]
      setLearningQuestion(next)
      setChatMessages(prev => [...prev, { id: Date.now() + 1, from: 'AgentMajesty', text: next.question }])
      return
    }

    if (learningQuestion) {
      try {
        const updated = await window.electron.invoke('remember-note', { note: `${learningQuestion.id}: ${message}` })
        const memory = Array.isArray(updated.memory) ? updated.memory : []
        memory[0] = { ...(memory[0] || {}), topic: learningQuestion.id, question: learningQuestion.question }
        const saved = await window.electron.invoke('update-profile', { ...updated, memory })
        setProfile(saved); setProfileDraft(saved)
        const next = learningQuestions.find(q => !memory.some(item => item.topic === q.id))
        setLearningQuestion(next || null)
        setChatMessages(prev => [...prev, {
          id: Date.now(), from: 'AgentMajesty',
          text: next ? `Saved. ${next.question}` : 'Saved. I have a stronger read on how you think now.'
        }])
      } catch (e) {
        setChatMessages(prev => [...prev, { id: Date.now(), from: 'AgentMajesty', text: 'I could not save that learning answer yet.' }])
      }
      return
    }

    const rememberMatch = message.match(/^remember(?: that)?:?\s+(.+)/i)
    if (rememberMatch) {
      try {
        const updated = await window.electron.invoke('remember-note', { note: rememberMatch[1] })
        setProfile(updated); setProfileDraft(updated)
        setChatMessages(prev => [...prev, { id: Date.now(), from: 'AgentMajesty', text: 'Noted. Saved to memory.' }])
      } catch (e) {
        setChatMessages(prev => [...prev, { id: Date.now(), from: 'AgentMajesty', text: "I couldn't save that memory yet." }])
      }
      return
    }

    const preferenceMatch = message.match(/\b(i prefer|i like|i don't like|always ask me|do not|don't|my priority is|i usually)\b.+/i)
    if (preferenceMatch && !message.endsWith('?')) {
      try {
        const updated = await window.electron.invoke('remember-note', { note: message })
        setProfile(updated); setProfileDraft(updated)
        setChatMessages(prev => [...prev, { id: Date.now(), from: 'AgentMajesty', text: 'Preference noted and saved.' }])
      } catch (e) {
        setChatMessages(prev => [...prev, { id: Date.now(), from: 'AgentMajesty', text: "Noted that preference, but couldn't save it yet." }])
      }
      return
    }

    setBusy(true)
    const streamId = Date.now() + 1
    setChatMessages(prev => [...prev, { id: streamId, from: 'AgentMajesty', text: '', streaming: true }])
    setIsTyping(true)

    try {
      let fullText = ''
      let finalTaskId = null

      if (window.electron?.on) {
        window.electron.on('majesty-chunk', (data) => {
          if (data.type === 'chunk') {
            fullText += data.content
            const displayText = fullText.replace(/\[TASK:\{[^}]*\}\]/g, '').trimEnd()
            setChatMessages(prev => prev.map(m => m.id === streamId ? { ...m, text: displayText } : m))
          } else if (data.type === 'done') {
            finalTaskId = data.taskId || null
            const displayText = fullText.replace(/\[TASK:\{[^}]*\}\]/g, '').trim()
            setChatMessages(prev => prev.map(m =>
              m.id === streamId ? { ...m, text: displayText, streaming: false, taskId: finalTaskId } : m
            ))
            if (data.taskId) {
              window.electron.invoke('read-tasks').then(t => { if (t) setTasks(t) })
              window.electron.invoke('read-agents').then(d => { if (d) setAgents(Array.isArray(d) ? d : d.agents || []) })
            }
          }
        })
      }

      await window.electron.invoke('start-majesty-chat', {
        message,
        history: chatMessages.slice(-10).map(m => ({ from: m.from, text: m.text }))
      })

    } catch (e) {
      console.error('Majesty chat error', e)
      setChatMessages(prev => prev.map(m =>
        m.id === streamId ? { ...m, text: 'Something went wrong. Please try again.', streaming: false } : m
      ))
    } finally {
      window.electron?.offAll?.('majesty-chunk')
      setIsTyping(false)
      setBusy(false)
    }
  }

  async function sendChat(event) {
    event.preventDefault()
    const message = chatInput.trim()
    setChatInput('')
    await submitChatMessage(message)
  }

  function handleChatKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      const message = chatInput.trim()
      setChatInput('')
      submitChatMessage(message)
    }
  }

  function useQuickPrompt(prompt) {
    submitChatMessage(prompt)
  }

  async function executeTask(taskId) {
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('execute-task', { id: taskId })
      setAgents(result.agents || [])
      setTasks(result.tasks || [])
      if (result.issues) setIssues(result.issues || [])
      const task = result.task
      if (task && task.assignedAgentId) setSelected(task.assignedAgentId)
      if (task) setSelectedTaskId(task.id)
      setChatMessages(items => items.concat([{
        from: 'AgentMajesty',
        text: task ? `${task.id} is ${task.status}. ${task.result || ''}`.trim() : (result.error || 'Task execution finished.'),
        taskId: task ? task.id : null
      }]))
    } catch (e) {
      console.error('execute task failed', e)
    } finally {
      setBusy(false)
    }
  }

  async function saveProfile(event) {
    event.preventDefault()
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const updated = await window.electron.invoke('update-profile', profileDraft)
      setProfile(updated)
      setProfileDraft(updated)
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: 'Chief of Staff profile updated. I will use this context when helping you.' }]))
    } finally {
      setBusy(false)
    }
  }

  async function addTodo(event) {
    event.preventDefault()
    if (!newTodo.title.trim() || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const tags = newTodo.tags ? newTodo.tags.split(',').map(t => t.trim()).filter(Boolean) : []
      const updated = await window.electron.invoke('add-todo', { ...newTodo, tags })
      setTodos(updated || [])
      setNewTodo({ title: '', description: '', priority: 'medium', dueDate: '', tags: '' })
    } finally {
      setBusy(false)
    }
  }

  async function updateTodoStatus(id, status) {
    if (!window.electron || !window.electron.invoke) return
    try {
      const updated = await window.electron.invoke('update-todo', { id, patch: { status } })
      setTodos(updated || [])
    } catch (e) { console.error('update-todo failed', e) }
  }

  async function deleteTodo(id) {
    if (!window.electron || !window.electron.invoke) return
    try {
      const updated = await window.electron.invoke('delete-todo', { id })
      setTodos(updated || [])
    } catch (e) { console.error('delete-todo failed', e) }
  }

  async function addContact(event) {
    event.preventDefault()
    if (!newContact.name.trim() || !newContact.email.trim() || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const updated = await window.electron.invoke('add-contact', newContact)
      setContacts(updated || [])
      setNewContact({ name: '', email: '', group: '', notes: '' })
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: 'Contact added to your email list.' }]))
    } finally {
      setBusy(false)
    }
  }

  function connectorConfigFromDraft() {
    if (newConnector.type === 'smtp') {
      return {
        host: newConnector.host,
        port: newConnector.port,
        username: newConnector.username,
        password: newConnector.password,
        fromEmail: newConnector.fromEmail,
        secure: false
      }
    }
    if (newConnector.type === 'constant-contact') {
      return {
        accountName: newConnector.accountName,
        clientId: newConnector.clientId,
        clientSecret: newConnector.clientSecret
      }
    }
    return {
      email: newConnector.email,
      authMode: 'oauth',
      scopes: 'mail.read, mail.send',
      accessToken: newConnector.accessToken,
      refreshToken: newConnector.refreshToken,
      expiresAt: newConnector.expiresAt
    }
  }

  async function addConnector(event) {
    event.preventDefault()
    if (!newConnector.name.trim() || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const updated = await window.electron.invoke('add-connector', {
        name: newConnector.name,
        type: newConnector.type,
        config: connectorConfigFromDraft()
      })
      setConnectors(updated || [])
      setNewConnector({
        name: '',
        type: newConnector.type,
        email: '',
        host: '',
        port: '587',
        username: '',
        password: '',
        fromEmail: '',
        accountName: '',
        clientId: '',
        clientSecret: '',
        accessToken: '',
        refreshToken: '',
        expiresAt: ''
      })
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: 'Connector profile saved. Test it when the required fields are in place.' }]))
    } finally {
      setBusy(false)
    }
  }

  async function testConnector(id) {
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('test-connector', { id })
      if (result.connectors) setConnectors(result.connectors)
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: result.connector?.lastTest?.message || result.error || 'Connector test finished.' }]))
    } finally {
      setBusy(false)
    }
  }

  async function selectChatGptExport() {
    if (!window.electron || !window.electron.invoke) return
    const filePath = await window.electron.invoke('select-chatgpt-export')
    if (filePath) setChatGptExportPath(filePath)
  }

  async function importChatGptHistory() {
    if (!chatGptExportPath || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('import-chatgpt-history', { filePath: chatGptExportPath })
      if (result.error) {
        setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: result.error }]))
        return
      }
      setProfile(result.profile)
      setProfileDraft(result.profile)
      setImportSummary(result.summary)
      const themes = (result.summary.topics || []).map(topic => topic.name).join(', ') || 'no strong themes detected'
      setChatMessages(items => items.concat([{
        from: 'AgentMajesty',
        text: `I imported ${result.summary.count} ChatGPT user messages and added learning notes to memory. Strongest themes: ${themes}.`
      }]))
    } finally {
      setBusy(false)
    }
  }

  async function saveMobileBridge(update) {
    if (!window.electron || !window.electron.invoke) return
    const result = await window.electron.invoke('update-mobile-bridge', {
      ...(mobileBridge || {}),
      ...update
    })
    setMobileBridge(result?.config || null)
    setMobileInfo(result?.info || null)
  }

  async function sendMobileTest() {
    const text = mobileTestText.trim()
    if (!text || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('receive-mobile-message', { from: 'iPhone test', text })
      if (result.error) {
        setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: result.error }]))
        return
      }
      setAgents(result.agents || [])
      setTasks(result.tasks || [])
      if (result.issues) setIssues(result.issues || [])
      setMobileBridge(result.bridge || mobileBridge)
      setMobileTestText('')
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: result.reply || 'Mobile message received.' }]))
    } finally {
      setBusy(false)
    }
  }

  async function selectProjectFolder() {
    if (!window.electron || !window.electron.invoke) return
    const folderPath = await window.electron.invoke('select-project-folder')
    if (folderPath) setProjectImportPath(folderPath)
  }

  const AI_PROVIDER_PRESETS = {
    ollama: { baseUrl: 'http://localhost:11434/v1', model: 'llama3.2' },
    openai: { baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
    github: { baseUrl: 'https://models.inference.ai.azure.com', model: 'gpt-4o-mini' }
  }

  function handleAiProviderChange(provider) {
    const preset = AI_PROVIDER_PRESETS[provider]
    setAiConfigDraft(d => ({
      ...d,
      provider,
      ...(preset ? { baseUrl: preset.baseUrl, model: preset.model } : {})
    }))
  }

  async function saveAiConfig(event) {
    event.preventDefault()
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('save-ai-config', aiConfigDraft)
      if (result?.config) {
        setAiConfig(result.config)
        setAiConfigDraft(d => ({ ...d, ...result.config }))
      }
      setAiTestResult(null)
      setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: `AI settings saved. Provider: ${aiConfigDraft.provider}, Model: ${aiConfigDraft.model}. ${aiConfigDraft.enabled ? 'AI is now ENABLED.' : 'AI is disabled.'}` }]))
    } finally {
      setBusy(false)
    }
  }

  async function testAiConfig() {
    if (!window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      setAiTestResult(null)
      const result = await window.electron.invoke('test-ai-config', aiConfigDraft)
      setAiTestResult(result)
    } finally {
      setBusy(false)
    }
  }

  async function importProjectFolder() {
    if (!projectImportPath || !window.electron || !window.electron.invoke) return
    try {
      setBusy(true)
      const result = await window.electron.invoke('import-project-folder', { folderPath: projectImportPath })
      if (result.error) {
        setChatMessages(items => items.concat([{ from: 'AgentMajesty', text: result.error }]))
        return
      }
      setProjects(result.projects || [])
      setAgents(result.agents || [])
      setTasks(result.tasks || [])
      if (result.task) setSelectedTaskId(result.task.id)
      setActiveTab('projects')
      setChatMessages(items => items.concat([{
        from: 'AgentMajesty',
        text: `Imported ${result.project.name}: ${result.project.summary.filesScanned} files, ${result.project.summary.docsImported} docs, ${result.project.summary.commitsImported} commits. I created a planning task.`
      }]))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <strong>Agent Harness</strong>
          <small>v1</small>
        </div>
        <h2 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '.06em', color: '#6b7280', margin: '0 0 8px' }}>Agents</h2>
        <ul>
          {agents.map(a => (
            <li key={a.id} onClick={() => setSelected(a.id)} className={`agent-item${a.id === selected ? ' selected' : ''}`}>
              <div className="agent-item-row">
                <span className={`status-dot dot-${a.status || 'idle'}`}></span>
                <strong style={{ fontSize: 13 }}>{a.name}</strong>
              </div>
              <small className="agent-item-meta">{a.role || statusLabel(a.status)} · {a.progress ?? 0}%</small>
              {openIssues.filter(issue => issue.agentId === a.id).length > 0 && (
                <span className="sidebar-alert">{openIssues.filter(issue => issue.agentId === a.id).length} issue(s)</span>
              )}
            </li>
          ))}
        </ul>
        <button className="full-button" onClick={() => { if (window.electron && window.electron.getAgents) { const m = window.electron.getAgents(); if (m && typeof m.then === 'function') { m.then(d => setAgents(d||[])) } else { setAgents(m||[]) } } }}>Refresh</button>

        <details className="add-agent">
          <summary>Add agent</summary>
          <form onSubmit={addAgent} style={{ marginTop: 10 }}>
            <label>
              Name
              <input value={newAgentName} onChange={e => setNewAgentName(e.target.value)} placeholder="newagent" />
            </label>
            <label>
              Specialty
              <input value={newAgentRole} onChange={e => setNewAgentRole(e.target.value)} placeholder="What they handle" />
            </label>
            <button className="full-button" disabled={busy || !newAgentName.trim()}>Add</button>
          </form>
        </details>

        {activeTab === 'profile' && <section className="chief-panel">
          <h3>Chief of Staff</h3>
          <form onSubmit={saveProfile}>
            <label>
              Name
              <input value={profileDraft.name || ''} onChange={e => setProfileDraft({ ...profileDraft, name: e.target.value })} />
            </label>
            <label>
              Role
              <input value={profileDraft.role || ''} onChange={e => setProfileDraft({ ...profileDraft, role: e.target.value })} />
            </label>
            <label>
              Priorities
              <textarea value={profileDraft.priorities || ''} onChange={e => setProfileDraft({ ...profileDraft, priorities: e.target.value })} />
            </label>
            <label>
              Style
              <input value={profileDraft.communicationStyle || ''} onChange={e => setProfileDraft({ ...profileDraft, communicationStyle: e.target.value })} />
            </label>
            <label>
              Approval rules
              <textarea value={profileDraft.approvalRules || ''} onChange={e => setProfileDraft({ ...profileDraft, approvalRules: e.target.value })} />
            </label>
            <button className="full-button" disabled={busy}>Save profile</button>
          </form>

          <div className="memory-list">
            <h4>Memory</h4>
            {recentMemory.length ? recentMemory.map((item, i) => <small key={i}>{item.text}</small>) : <small>No notes saved yet.</small>}
          </div>

          <div className="history-import">
            <h4>ChatGPT history</h4>
            <small>Import an exported <code>conversations.json</code> file so Majesty can learn recurring themes and preferences locally.</small>
            <button className="full-button subtle-button" disabled={busy} onClick={selectChatGptExport}>Select export file</button>
            {chatGptExportPath && <small className="file-path">{chatGptExportPath}</small>}
            <button className="full-button" disabled={busy || !chatGptExportPath} onClick={importChatGptHistory}>Import for learning</button>
            {importSummary && <small>{importSummary.count} messages imported.</small>}
          </div>

        </section>}

        {activeTab === 'connectors' && <section className="chief-panel">
          <details className="connectors-panel" open>
            <summary>Connectors</summary>
            <form className="connector-form" onSubmit={addConnector}>
              <label>
                Type
                <select value={newConnector.type} onChange={e => setNewConnector({ ...newConnector, type: e.target.value })}>
                  <option value="gmail">Gmail</option>
                  <option value="outlook">Outlook</option>
                  <option value="smtp">Custom email (SMTP)</option>
                  <option value="constant-contact">Constant Contact</option>
                </select>
              </label>
              <label>
                Name
                <input value={newConnector.name} onChange={e => setNewConnector({ ...newConnector, name: e.target.value })} placeholder="Primary Gmail" />
              </label>
              {(newConnector.type === 'gmail' || newConnector.type === 'outlook') && (
                <>
                  <label>
                    Email
                    <input value={newConnector.email} onChange={e => setNewConnector({ ...newConnector, email: e.target.value })} placeholder="you@example.com" />
                  </label>
                  <label>
                    Access token
                    <textarea value={newConnector.accessToken} onChange={e => setNewConnector({ ...newConnector, accessToken: e.target.value })} placeholder="Paste OAuth access token" />
                  </label>
                  <label>
                    Refresh token
                    <textarea value={newConnector.refreshToken} onChange={e => setNewConnector({ ...newConnector, refreshToken: e.target.value })} placeholder="Paste OAuth refresh token" />
                  </label>
                  <label>
                    Expires at
                    <input value={newConnector.expiresAt} onChange={e => setNewConnector({ ...newConnector, expiresAt: e.target.value })} placeholder="2026-05-21T23:00:00Z" />
                  </label>
                </>
              )}
              {newConnector.type === 'smtp' && (
                <>
                  <label>
                    Host
                    <input value={newConnector.host} onChange={e => setNewConnector({ ...newConnector, host: e.target.value })} placeholder="smtp.example.com" />
                  </label>
                  <label>
                    Port
                    <input value={newConnector.port} onChange={e => setNewConnector({ ...newConnector, port: e.target.value })} placeholder="587" />
                  </label>
                  <label>
                    Username
                    <input value={newConnector.username} onChange={e => setNewConnector({ ...newConnector, username: e.target.value })} />
                  </label>
                  <label>
                    Password
                    <input type="password" value={newConnector.password} onChange={e => setNewConnector({ ...newConnector, password: e.target.value })} />
                  </label>
                  <label>
                    From email
                    <input value={newConnector.fromEmail} onChange={e => setNewConnector({ ...newConnector, fromEmail: e.target.value })} />
                  </label>
                </>
              )}
              {newConnector.type === 'constant-contact' && (
                <>
                  <label>
                    Account
                    <input value={newConnector.accountName} onChange={e => setNewConnector({ ...newConnector, accountName: e.target.value })} placeholder="Sigma Signal" />
                  </label>
                  <label>
                    Client ID
                    <input value={newConnector.clientId} onChange={e => setNewConnector({ ...newConnector, clientId: e.target.value })} />
                  </label>
                  <label>
                    Client secret
                    <input type="password" value={newConnector.clientSecret} onChange={e => setNewConnector({ ...newConnector, clientSecret: e.target.value })} />
                  </label>
                </>
              )}
              <button className="full-button" disabled={busy || !newConnector.name.trim()}>Add connector</button>
            </form>
            <div className="connector-list">
              {connectors.map(connector => (
                <div className="connector-row" key={connector.id}>
                  <div>
                    <strong>{connector.name}</strong>
                    <small>{connector.type} · {connector.status}</small>
                  </div>
                  <button disabled={busy} onClick={() => testConnector(connector.id)}>Test</button>
                  {connector.lastTest && <small>{connector.lastTest.message}</small>}
                </div>
              ))}
              {!connectors.length && <small>No connectors yet.</small>}
            </div>
          </details>

          <details className="mobile-bridge">
            <summary>iPhone bridge</summary>
            <small>Use iPhone Shortcuts to POST a note or task into AgentMajesty. This is the practical Apple path; direct iMessage automation is not available from this Windows app.</small>
            <label>
              Channel
              <select value={mobileBridge?.channel || 'iPhone Shortcuts'} onChange={e => saveMobileBridge({ channel: e.target.value })}>
                <option>iPhone Shortcuts</option>
                <option>Manual iMessage copy</option>
                <option>Email fallback</option>
              </select>
            </label>
            <label>
              Trusted sender
              <input value={mobileBridge?.trustedSender || ''} onChange={e => saveMobileBridge({ trustedSender: e.target.value })} placeholder="Your iPhone name or number" />
            </label>
            <small>Shortcut POST URL</small>
            <code className="bridge-code">{mobileInfo?.lanEndpoint || 'Start the runtime server to get a LAN endpoint.'}</code>
            <small>Shortcut JSON body</small>
            <code className="bridge-code">{mobileInfo?.shortcutBody || '{}'}</code>
            <textarea value={mobileTestText} onChange={e => setMobileTestText(e.target.value)} placeholder="Test an incoming iPhone message" />
            <button className="full-button" disabled={busy || !mobileTestText.trim()} onClick={sendMobileTest}>Send test to Majesty</button>
            <div className="mobile-message-list">
              {(mobileBridge?.messages || []).slice(0, 3).map(message => (
                <small key={message.id}>{message.from}: {message.text}</small>
              ))}
            </div>
          </details>

        </section>}

        {activeTab === 'profile' && <section className="chief-panel">
          <details className="contact-drawer" open>
            <summary>Optional contacts</summary>
            <form className="contact-form" onSubmit={addContact}>
              <label>
                Name
                <input value={newContact.name} onChange={e => setNewContact({ ...newContact, name: e.target.value })} />
              </label>
              <label>
                Email
                <input value={newContact.email} onChange={e => setNewContact({ ...newContact, email: e.target.value })} />
              </label>
              <label>
                Group
                <input value={newContact.group} onChange={e => setNewContact({ ...newContact, group: e.target.value })} />
              </label>
              <label>
                Notes
                <input value={newContact.notes} onChange={e => setNewContact({ ...newContact, notes: e.target.value })} />
              </label>
              <button className="full-button" disabled={busy || !newContact.name.trim() || !newContact.email.trim()}>Add contact</button>
            </form>

            <div className="contact-list">
              {contacts.slice(0, 4).map(contact => (
                <div className="contact-row" key={contact.id}>
                  <strong>{contact.name}</strong>
                  <small>{contact.email}</small>
                  {contact.group && <small>{contact.group}</small>}
                </div>
              ))}
              {!contacts.length && <small>No contacts yet.</small>}
            </div>
          </details>
        </section>}
      </aside>

      <main className="main">
        <header className="timeline">
          {agents.filter(a => a.status === 'running').length > 0
            ? <span>🟢 {agents.filter(a => a.status === 'running').length} agent{agents.filter(a => a.status === 'running').length !== 1 ? 's' : ''} running</span>
            : queuedTasks.length > 0
            ? <span>⏳ {queuedTasks.length} task{queuedTasks.length !== 1 ? 's' : ''} queued</span>
            : completedTasks.length > 0
            ? <span>✅ {completedTasks.length} completed · {openIssues.length} issue{openIssues.length !== 1 ? 's' : ''} open</span>
            : <span style={{ color: '#9ca3af' }}>Ready — no active tasks</span>}
        </header>
        <nav className="tab-bar">
          {[
            ['command', 'Command'],
            ['todos', 'Todos'],
            ['tasks', 'Tasks'],
            ['projects', 'Projects'],
            ['connectors', 'Connectors'],
            ['profile', 'Profile'],
            ['ai', 'AI Settings'],
            ['raw', 'Raw']
          ].map(([id, label]) => (
            <button key={id} className={activeTab === id ? 'active-tab' : ''} onClick={() => setActiveTab(id)}>
              {label}
              {id === 'todos' && pendingTodos.length > 0 && <span className="tab-badge">{pendingTodos.length}</span>}
            </button>
          ))}
        </nav>
        <section className="status-strip">
          <div><strong>{agents.filter(agent => agent.status === 'running').length}</strong><span>Running</span></div>
          <div><strong>{queuedTasks.length}</strong><span>Queued</span></div>
          <div><strong>{completedTasks.length}</strong><span>Completed</span></div>
          <div className={pendingTodos.length > 0 ? 'strip-alert' : ''}><strong>{pendingTodos.length}</strong><span>Todos</span></div>
          <div><strong>{openIssues.length}</strong><span>Issues</span></div>
          <div className={aiConfig?.enabled ? 'ai-active-strip' : ''}><strong>{aiConfig?.enabled ? '✓' : '—'}</strong><span>{aiConfig?.enabled ? `AI · ${aiConfig.provider}` : 'AI off'}</span></div>
        </section>
        {activeTab === 'command' && <section className="command-chat">
          {selAgent && (
            <div className="agent-status-bar">
              <span className={`status-dot dot-${selAgent.status || 'idle'}`}></span>
              <strong>{selAgent.name}</strong>
              {selAgent.role && <span className="agent-role-badge">{selAgent.role}</span>}
              <span className={`status-pill status-${selAgent.status}`} style={{ fontSize: 11 }}>{statusLabel(selAgent.status)}</span>
              <div className="progress-mini">
                <div className="progress-inner" style={{ width: `${Math.max(0, Math.min(100, selAgent.progress || 0))}%` }} />
              </div>
              <small style={{ color: '#6b7280', fontSize: 11 }}>{selAgent.progress ?? 0}%</small>
              <div className="agent-bar-actions">
                <button disabled={!selAgent || busy || selAgent.status === 'running'} onClick={() => commandAgent(selAgent.id, 'start')}>{busy ? '…' : 'Start'}</button>
                <button disabled={!selAgent || busy || selAgent.status !== 'running'} onClick={() => commandAgent(selAgent.id, 'stop')}>{busy ? '…' : 'Stop'}</button>
                <button disabled={!selAgent || busy} onClick={() => commandAgent(selAgent.id, 'ping')}>{busy ? '…' : 'Ping'}</button>
              </div>
            </div>
          )}
          <div className="majesty-full">
            <div className="majesty-header">
              <div>
                <h3>AgentMajesty</h3>
                <small>{queuedTasks.length} queued · {completedTasks.length} completed · <button style={{ background: 'none', border: 'none', padding: 0, color: '#2563eb', cursor: 'pointer', fontSize: 12 }} onClick={() => setActiveTab('tasks')}>view tasks →</button></small>
              </div>
              <span className={busy ? 'majesty-state busy-state' : 'majesty-state'}>{busy ? 'Working…' : 'Ready'}</span>
            </div>
            <div className="prompt-chips">
              {quickPrompts.map(prompt => (
                <button key={prompt} disabled={busy} onClick={() => useQuickPrompt(prompt)}>{prompt}</button>
              ))}
            </div>
            {learningQuestion && <div className="learning-banner">Learning mode active. Answer naturally, and I will save what matters.</div>}
            {chatMessages.length === 1 && (
              <div className="welcome-cards">
                {[
                  { icon: '📋', label: 'Create a task', prompt: 'Create a task to research grant opportunities for YEPC' },
                  { icon: '🔍', label: 'Check status', prompt: 'Status' },
                  { icon: '🧠', label: 'Teach Majesty', prompt: 'Teach Majesty' },
                  { icon: '📰', label: 'Newsletter health', prompt: 'Check newsletter campaign health' },
                ].map(({ icon, label, prompt }) => (
                  <button key={label} className="welcome-card" disabled={busy} onClick={() => { setChatInput(''); submitChatMessage(prompt) }}>
                    <span className="welcome-card-icon">{icon}</span>
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            )}
            <div className="chat-stream" ref={chatRef}>
              {chatMessages.map((m) => (
                m.from === 'You' ? (
                  <div key={m.id ?? m.text} className="msg-row msg-row-user">
                    <div className="bubble bubble-user">{m.text}</div>
                  </div>
                ) : (
                  <div key={m.id ?? m.text} className="msg-row msg-row-agent">
                    <div className="agent-avatar">M</div>
                    <div className="bubble bubble-agent">
                      {m.text === '' && m.streaming ? (
                        <div className="typing-dots"><span/><span/><span/></div>
                      ) : (
                        <div className="markdown-body" dangerouslySetInnerHTML={{ __html: renderMarkdown(m.text) }} />
                      )}
                      {m.streaming && m.text && <span className="streaming-cursor">▋</span>}
                      {m.taskId && tasks.find(t => t.id === m.taskId && t.status === 'queued') && (
                        <button className="inline-action" style={{ marginTop: 8 }} disabled={busy} onClick={() => { executeTask(m.taskId); setActiveTab('tasks') }}>
                          ▶ Execute task
                        </button>
                      )}
                    </div>
                  </div>
                )
              ))}
              {isTyping && chatMessages[chatMessages.length - 1]?.streaming === false && (
                <div className="msg-row msg-row-agent">
                  <div className="agent-avatar">M</div>
                  <div className="bubble bubble-agent"><div className="typing-dots"><span/><span/><span/></div></div>
                </div>
              )}
            </div>
            <form className="chat-input" onSubmit={sendChat}>
              <textarea
                value={chatInput}
                onChange={e => { setChatInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px' }}
                onKeyDown={handleChatKeyDown}
                placeholder="Message AgentMajesty…"
                style={{ minHeight: 44, maxHeight: 160, resize: 'none', overflowY: 'auto' }}
              />
              <button disabled={busy || !chatInput.trim()} style={{ background: '#2563eb', color: '#fff', border: 0, borderRadius: 6, padding: '8px 14px', fontWeight: 500, alignSelf: 'stretch' }}>Send</button>
            </form>
          </div>
        </section>}

        {activeTab === 'todos' && <section className="todos-view">
          <div className="todos-header">
            <div>
              <h3>Todos &amp; Pending Items</h3>
              <small>{pendingTodos.length} outstanding · {todos.filter(t => t.status === 'done').length} done</small>
            </div>
            <div className="todo-filter-bar">
              {[['active', 'Active'], ['all', 'All'], ['pending', 'Pending'], ['in_progress', 'In Progress'], ['blocked', 'Blocked'], ['done', 'Done']].map(([key, label]) => (
                <button key={key} className={todoFilter === key ? 'todo-filter-btn active' : 'todo-filter-btn'} onClick={() => setTodoFilter(key)}>{label}</button>
              ))}
            </div>
          </div>

          <form className="todo-add-form" onSubmit={addTodo}>
            <input
              className="todo-title-input"
              value={newTodo.title}
              onChange={e => setNewTodo({ ...newTodo, title: e.target.value })}
              placeholder="Add a todo or outstanding item…"
            />
            <select value={newTodo.priority} onChange={e => setNewTodo({ ...newTodo, priority: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            <input
              type="date"
              value={newTodo.dueDate}
              onChange={e => setNewTodo({ ...newTodo, dueDate: e.target.value })}
              title="Due date (optional)"
            />
            <button className="todo-add-btn" disabled={busy || !newTodo.title.trim()}>Add</button>
          </form>

          {newTodo.title && (
            <div className="todo-detail-row">
              <input
                value={newTodo.description}
                onChange={e => setNewTodo({ ...newTodo, description: e.target.value })}
                placeholder="Description (optional)"
              />
              <input
                value={newTodo.tags}
                onChange={e => setNewTodo({ ...newTodo, tags: e.target.value })}
                placeholder="Tags (comma separated)"
              />
            </div>
          )}

          {todos.length === 0 ? (
            <p className="empty-state">No todos yet — add one above or ask AgentMajesty to create outstanding items for you.</p>
          ) : (
            <div className="todo-list">
              {todos
                .filter(t => {
                  if (todoFilter === 'active') return t.status !== 'done'
                  if (todoFilter === 'all') return true
                  return t.status === todoFilter
                })
                .sort((a, b) => {
                  const pri = { urgent: 0, high: 1, medium: 2, low: 3 }
                  return (pri[a.priority] ?? 2) - (pri[b.priority] ?? 2) || new Date(b.createdAt) - new Date(a.createdAt)
                })
                .map(todo => (
                  <div key={todo.id} className={`todo-item todo-status-${todo.status} todo-pri-${todo.priority}`}>
                    <button
                      className={`todo-check ${todo.status === 'done' ? 'checked' : ''}`}
                      title={todo.status === 'done' ? 'Mark pending' : 'Mark done'}
                      onClick={() => updateTodoStatus(todo.id, todo.status === 'done' ? 'pending' : 'done')}
                    >
                      {todo.status === 'done' ? '✓' : ''}
                    </button>
                    <div className="todo-body">
                      <div className="todo-title-row">
                        <strong className={todo.status === 'done' ? 'todo-done-text' : ''}>{todo.title}</strong>
                        <span className={`todo-priority-badge pri-${todo.priority}`}>{todo.priority}</span>
                        {todo.dueDate && <span className={`todo-due ${new Date(todo.dueDate) < new Date() && todo.status !== 'done' ? 'overdue' : ''}`}>📅 {todo.dueDate}</span>}
                      </div>
                      {todo.description && <p className="todo-desc">{todo.description}</p>}
                      {todo.tags?.length > 0 && (
                        <div className="todo-tags">{todo.tags.map(tag => <span key={tag} className="todo-tag">{tag}</span>)}</div>
                      )}
                    </div>
                    <div className="todo-actions">
                      {todo.status !== 'in_progress' && todo.status !== 'done' && (
                        <button className="todo-action-btn" onClick={() => updateTodoStatus(todo.id, 'in_progress')} title="Start">▶</button>
                      )}
                      {todo.status === 'in_progress' && (
                        <button className="todo-action-btn" onClick={() => updateTodoStatus(todo.id, 'pending')} title="Pause">⏸</button>
                      )}
                      {todo.status !== 'blocked' && todo.status !== 'done' && (
                        <button className="todo-action-btn" onClick={() => updateTodoStatus(todo.id, 'blocked')} title="Block">🚫</button>
                      )}
                      <button className="todo-action-btn todo-delete-btn" onClick={() => deleteTodo(todo.id)} title="Delete">✕</button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </section>}

        {activeTab === 'tasks' && <section className="task-queue">
          <div className="section-heading">
            <h3>Task queue</h3>
            {selectedTask && <small>Selected: {selectedTask.id}</small>}
          </div>
          {tasks.length === 0 ? (
            <p className="empty-state">No tasks yet — go to the Command tab and tell AgentMajesty what needs to get done.</p>
          ) : (
            <div className="task-list">
              {tasks.map(task => (
                <article className={task.id === selectedTask?.id ? 'task-card selected-task-card' : 'task-card'} key={task.id} onClick={() => setSelectedTaskId(task.id)}>
                  <div className="task-head">
                    <div>
                      <strong>{task.title}</strong>
                      <div><small>{task.id} · {task.assignedAgentName || 'Unassigned'}</small></div>
                    </div>
                    <span className={`status-pill status-${task.status}`}>{statusLabel(task.status)}</span>
                  </div>
                  <p>{task.description}</p>
                  {task.responseData?.summary && <small className="task-summary">{task.responseData.summary}</small>}
                  {(task.issueIds || []).length > 0 && <small className="issue-link">{task.issueIds.length} linked issue(s)</small>}
                  <div className="task-actions">
                    <button disabled={busy || task.status === 'completed' || task.status === 'completed-with-issues' || task.status === 'needs-agent'} onClick={(event) => { event.stopPropagation(); executeTask(task.id) }}>
                      Execute
                    </button>
                  </div>
                  <div className="task-log">
                    {(task.logs || []).slice(-4).map((line, i) => <div key={i}><small>{line}</small></div>)}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>}

        {activeTab === 'tasks' && <section className="response-grid">
          <article className="response-panel">
            <div className="section-heading">
              <h3>Response data</h3>
              {selectedTask && <span className={`status-pill status-${selectedTask.status}`}>{selectedTask.status}</span>}
            </div>
            {!selectedTask ? (
              <p className="empty-state">Select a task to inspect its response.</p>
            ) : (
              <>
                <strong>{selectedTask.title}</strong>
                {(() => {
                  const llmAdapter = selectedTask.responseData?.adapters?.find(a => a.name === 'llm-adapter')
                  const aiText = llmAdapter?.status === 'completed' ? llmAdapter.data?.response : null
                  if (aiText) return (
                    <div className="ai-response-box">
                      <small className="ai-response-label">AI response · {llmAdapter.data?.model}</small>
                      <div className="ai-response-text">{aiText}</div>
                    </div>
                  )
                  return <p>{selectedTask.responseData?.recommendation || selectedTask.result || 'No response data yet. Click Execute when the task is ready.'}</p>
                })()}
                {selectedTask.responseData?.nextActions?.length > 0 && (
                  <div className="next-actions">
                    {selectedTask.responseData.nextActions.map(action => <small key={action}>{action}</small>)}
                  </div>
                )}
                {selectedTask.responseData?.adapters?.length > 0 && (
                  <div className="adapter-results">
                    {selectedTask.responseData.adapters.map(adapter => (
                      <div className="adapter-card" key={adapter.name}>
                        <strong>{adapter.name}</strong>
                        <span>{adapter.status}</span>
                        <small>{adapter.summary}</small>
                      </div>
                    ))}
                  </div>
                )}
                <details style={{ marginTop: 8 }}>
                  <summary style={{ fontSize: 12, cursor: 'pointer', color: '#9ca3af' }}>Raw data</summary>
                  <pre>{JSON.stringify(selectedTask.responseData?.data || { assignedAgentName: selectedTask.assignedAgentName, logs: selectedTask.logs?.slice(-3) || [] }, null, 2)}</pre>
                </details>
              </>
            )}
          </article>

          <article className="issues-panel">
            <div className="section-heading">
              <h3>Issues</h3>
              <small>{openIssues.length} open</small>
            </div>
            {issues.length === 0 ? (
              <p className="empty-state">No issues logged yet.</p>
            ) : (
              <div className="issue-list">
                {issues.slice(0, 8).map(issue => (
                  <div className={`issue-card severity-${issue.severity}`} key={issue.id}>
                    <div className="issue-title">
                      <strong>{issue.title}</strong>
                      <span>{issue.status}</span>
                    </div>
                    <small>{issue.agentName || issue.agentId || 'Unknown agent'} · {issue.severity}</small>
                    <p>{issue.detail}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>}

        {activeTab === 'projects' && <section className="projects-view">
          <div className="section-heading">
            <h3>Project import</h3>
            <small>{projects.length} imported</small>
          </div>
          <div className="import-panel">
            <button className="full-button subtle-button" disabled={busy} onClick={selectProjectFolder}>Choose project folder</button>
            {projectImportPath && <small className="file-path">{projectImportPath}</small>}
            <button className="full-button" disabled={busy || !projectImportPath} onClick={importProjectFolder}>Import project history</button>
          </div>
          {latestProject && (
            <article className="project-hero">
              <div>
                <h3>{latestProject.name}</h3>
                <small>{latestProject.path}</small>
              </div>
              <div className="project-stats">
                <span>{latestProject.summary.filesScanned} files</span>
                <span>{latestProject.summary.docsImported} docs</span>
                <span>{latestProject.summary.commitsImported} commits</span>
              </div>
            </article>
          )}
          <div className="project-grid">
            {projects.map(project => (
              <article className="project-card" key={project.id}>
                <div className="task-head">
                  <div>
                    <strong>{project.name}</strong>
                    <div><small>{project.path}</small></div>
                  </div>
                  <span className="status-pill">{project.status}</span>
                </div>
                <div className="project-stats">
                  <span>{project.summary.filesScanned} files</span>
                  <span>{project.summary.docsImported} docs</span>
                  <span>{project.summary.commitsImported} commits</span>
                </div>
                {project.summary.suggestedAgents?.length > 0 && <small>Suggested agents: {project.summary.suggestedAgents.join(', ')}</small>}
                <div className="timeline-list">
                  {(project.timeline || []).slice(0, 5).map(item => (
                    <small key={`${item.ref}-${item.date}`}>{item.date} - {item.title}</small>
                  ))}
                </div>
              </article>
            ))}
            {!projects.length && <p className="empty-state">No projects imported yet.</p>}
          </div>
        </section>}

        {activeTab === 'ai' && <section className="projects-view">
          <div className="section-heading">
            <h3>AI Settings</h3>
            <small>{aiConfig?.enabled ? `Enabled · ${aiConfig.provider} · ${aiConfig.model}` : 'Disabled'}</small>
          </div>
          <form className="ai-settings-form" onSubmit={saveAiConfig}>
            <label>
              Provider
              <select
                value={aiConfigDraft.provider || 'ollama'}
                onChange={e => handleAiProviderChange(e.target.value)}
              >
                <option value="ollama">Ollama (local / offline)</option>
                <option value="openai">OpenAI (GPT-4o, GPT-4o-mini…)</option>
                <option value="github">GitHub Models (login required)</option>
                <option value="custom">Custom (any OpenAI-compatible)</option>
              </select>
            </label>
            <label>
              Base URL
              <input
                value={aiConfigDraft.baseUrl || ''}
                onChange={e => setAiConfigDraft(d => ({ ...d, baseUrl: e.target.value }))}
                placeholder="http://localhost:11434/v1"
              />
            </label>
            <label>
              Model
              <input
                value={aiConfigDraft.model || ''}
                onChange={e => setAiConfigDraft(d => ({ ...d, model: e.target.value }))}
                placeholder="llama3.2"
              />
            </label>
            <label>
              API Key / Token
              <input
                type="password"
                value={aiConfigDraft.apiKey || ''}
                onChange={e => setAiConfigDraft(d => ({ ...d, apiKey: e.target.value }))}
                placeholder="Leave blank for Ollama · paste token for OpenAI / GitHub"
              />
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={Boolean(aiConfigDraft.enabled)}
                onChange={e => setAiConfigDraft(d => ({ ...d, enabled: e.target.checked }))}
              />
              Enable AI for task execution
            </label>
            <div className="button-row">
              <button type="button" className="full-button subtle-button" disabled={busy} onClick={testAiConfig}>Test connection</button>
              <button type="submit" className="full-button" disabled={busy}>Save settings</button>
            </div>
          </form>
          {aiTestResult && (
            <div className={`ai-test-result ${aiTestResult.ok ? 'test-ok' : 'test-fail'}`}>
              {aiTestResult.ok ? '✓' : '✗'} {aiTestResult.message}
            </div>
          )}
          <div className="section-heading" style={{ marginTop: 24 }}>
            <h4>How it works</h4>
          </div>
          <div className="ai-help">
            <p>When enabled, each agent's <code>/agents/*.md</code> profile becomes the AI system prompt. When you execute a task, the agent uses its profile + research context + your Chief of Staff profile to generate a real AI response.</p>
            <ul>
              <li><strong>Ollama:</strong> Install from <a href="https://ollama.com" target="_blank" rel="noreferrer">ollama.com</a>, run <code>ollama pull llama3.2</code>, then start the server. No API key needed.</li>
              <li><strong>OpenAI:</strong> Get an API key from platform.openai.com. Use model <code>gpt-4o-mini</code> for cost efficiency.</li>
              <li><strong>GitHub Models:</strong> Use your GitHub token (from <code>gh auth token</code>). Use model <code>gpt-4o-mini</code>.</li>
            </ul>
          </div>
        </section>}

        {activeTab === 'raw' && <section className="logs raw-view">
          <h4>All agents (raw)</h4>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(agents, null, 2)}</pre>
        </section>}
      </main>
    </div>
  )
}
