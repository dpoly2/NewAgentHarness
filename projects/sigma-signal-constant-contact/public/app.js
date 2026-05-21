const els = {
  health: document.querySelector('#health'),
  openCount: document.querySelector('#open-count'),
  nextIssue: document.querySelector('#next-issue'),
  watchAddress: document.querySelector('#watch-address'),
  lastCheck: document.querySelector('#last-check'),
  requests: document.querySelector('#requests'),
  cadence: document.querySelector('#cadence'),
  sendWindow: document.querySelector('#send-window'),
  mode: document.querySelector('#mode'),
  setup: document.querySelector('#setup'),
  refresh: document.querySelector('#refresh')
}

function formatDate(value) {
  if (!value) return 'No successful check yet'
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

function renderRequests(requests) {
  if (!requests.length) {
    els.requests.innerHTML = '<p class="empty">No requests are currently tracked.</p>'
    return
  }

  els.requests.innerHTML = requests.map((request) => `
    <article class="request-card priority-${request.priority || 'normal'}">
      <div>
        <span class="pill">${request.type || 'general'}</span>
        <span class="pill muted">${request.status || 'open'}</span>
      </div>
      <h3>${request.subject || 'Untitled request'}</h3>
      <p>${request.snippet || ''}</p>
      <footer>
        <span>${request.from || 'unknown sender'}</span>
        <time>${formatDate(request.receivedAt)}</time>
      </footer>
    </article>
  `).join('')
}

async function loadStatus() {
  const res = await fetch('/api/status', { cache: 'no-store' })
  const { config, state, requests } = await res.json()
  const summary = state.summary || {}

  els.health.textContent = summary.health || 'unknown'
  els.health.dataset.health = summary.health || 'unknown'
  els.openCount.textContent = summary.openRequestCount ?? requests.length
  els.nextIssue.textContent = config.newsletter?.nextIssueTargetDate || 'TBD'
  els.watchAddress.textContent = config.gmail?.watchAddress || 'not configured'
  els.lastCheck.textContent = `Last check: ${formatDate(state.lastSuccessfulCheckAt || state.lastLocalCheckAt)}`
  els.cadence.textContent = `Every ${config.newsletter?.cadenceDays || 14} days`
  els.sendWindow.textContent = config.newsletter?.nextIssueWindow || 'TBD'
  els.mode.textContent = state.monitorMode || 'local-app'
  els.setup.textContent = state.setupStatus || 'Ready'
  renderRequests(requests)
}

els.refresh.addEventListener('click', loadStatus)
loadStatus().catch((error) => {
  els.requests.innerHTML = `<p class="empty">Unable to load monitor status: ${error.message}</p>`
})
