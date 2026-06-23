# ArchonHub iOS & Watch App

**Version:** 3.0  
**Updated:** June 2026  
**Requires:** iOS 17+, watchOS 10+, Xcode 15+, ArchonHub Hub Server

SwiftUI client for the ArchonHub AI Agent Operating System. Connects to the Hub Server at `http://localhost:8765` (configurable in Settings). Full offline-capable UI with JWT authentication.

---

## Setup

1. Open `ArchonHub.xcodeproj` in Xcode
2. Select your target device / simulator
3. Build & run (⌘R)
4. Set your Hub Server URL in **Settings → Server URL**
5. Login (default: `admin` / `ArchonHub2024!`)

---

## Tab Structure

iOS enforces a maximum of 5 tab bar items. ArchonHub uses hub views with segmented pickers to expose all screens:

| Tab | Icon | Contents |
|-----|------|---------|
| **Dashboard** | house.fill | Live stats, agent status, quick actions |
| **Inez** | crown.fill | AI Chief of Staff chat with file uploads |
| **Activity** | chart.xyaxis.line | Runs · Reports · Briefing · Alerts |
| **Workspace** | square.grid.2x2.fill | Todos · Docs · Memory · Automations |
| **Settings** | gearshape.fill | Server URL, auth, preferences |

---

## Views

### Dashboard
- Live agent run counts, todo summary, pending dispatches
- Quick-launch agent runs
- Hub server connection status

### Inez (AI Chat)
- Full conversation UI with streaming responses
- File attachment support (upload documents for RAG context)
- Dispatch cards — Inez can create tasks, emails, reports
- Conversation history with search
- In-conversation memory of prior messages

### Activity Hub
**Runs** — Agent run history, status badges, detail drill-down  
**Reports** — Agent-generated reports and analysis  
**Briefing** — Daily AI morning brief (todos + markets + email highlights)  
**Alerts** — Proactive notifications from monitoring agents

### Workspace Hub
**Todos** — Create, complete, and manage todos; synced with Inez  
**Documents** — Document library with RAG search  
**Memory** — Browse, search, filter, create, edit, and delete Global Memory facts  
**Automations** — Scheduled agent automations

### Settings
- Hub Server URL configuration
- Authentication (login / logout)
- Agent list with status
- LLM model selection
- SerpAPI web search toggle

---

## Global Memory (iOS)

The Memory tab gives full CRUD access to the 160+ personal facts Inez uses in every response.

- **Browse** by category: projects, technical, preferences, people, finance, ministry, rules, deadlines
- **Search** full-text across keys and values
- **Add** custom facts with importance rating (1–10)
- **Edit** existing facts inline
- **Delete** via swipe
- Category icons and importance colour-coding

---

## Code Execution Sandbox (iOS)

Access from any screen via `RunCodeButton` or open `CodeExecutionView` directly.

- Inline Python code editor (monospaced)
- **▶ Run** → POST to `/api/sandbox/execute`
- Output: stdout (white), stderr (red), execution time, mode badge
- **Generated files** (charts, CSVs) previewed inline — images render full-screen, text/CSV shown as monospaced
- Security: blocked imports (`os`, `subprocess`, `socket`…) shown as blocked reason

---

## Apple Watch App

| Screen | Description |
|--------|-------------|
| **Main** | Hub status, active run count, pending todos |
| **Status** | Server ping, last sync time |
| **Quick Run** | One-tap agent dispatch from wrist |
| **Notifications** | Recent agent alerts |
| **Complication** | Active run count on watch face |

---

## Models (`Models.swift`)

Key types used across the app:

| Model | Purpose |
|-------|---------|
| `AgentRun` | Agent execution record |
| `InezChatRequest/Response` | Inez chat API |
| `Todo` | Task item |
| `GlobalMemoryFact` | Personal memory fact |
| `GlobalMemoryResponse` | Paginated memory list |
| `SandboxExecuteRequest` | Code execution input |
| `SandboxResult` | Code execution output + files |
| `SandboxGeneratedFile` | Base64-encoded output file |
| `PromptTemplate` | Agent prompt template |
| `EmailCleanupPlan` | Email cleanup approval |

---

## Network (`HubClient.swift`)

```swift
// All requests are async throws
HubClient.shared.get<T: Decodable>(_ path: String) async throws -> T
HubClient.shared.post<T, B: Encodable>(_ path: String, body: B) async throws -> T
HubClient.shared.put<T, B: Encodable>(_ path: String, body: B) async throws -> T
HubClient.shared.delete(_ path: String) async throws
```

Base URL and JWT token stored in `AppStorage`. Token auto-attached via `Authorization: Bearer` header.

---

## Default Credentials

```
URL:      http://localhost:8765
Username: admin
Password: ArchonHub2024!
```

Change password after first login in **Settings → Account**.

