# AgentHarness Viewer — Copilot App Specification
**Version:** 1.0
**Date:** 2026-05-22
**Author:** AgentJames
**Repo:** dpoly2/AgentHarness
**Purpose:** Give this full document to GitHub Copilot (or any AI assistant) as the complete spec to build the AgentHarness Viewer app.

---

## 1. PROJECT OVERVIEW

Build a local web app called **AgentHarness Viewer** that reads the `.agents/` directory from the `dpoly2/AgentHarness` GitHub repository and renders it as a structured, browsable agent dashboard.

The app lets David (the owner) visually navigate all projects, agents, helper agents, and project documentation — without reading raw markdown files.

**Tech stack:** React + Vite (or Next.js), Tailwind CSS, GitHub REST API (public repo read — no auth required for public repo, or use a PAT stored in `.env.local` for private repo access).

---

## 2. DATA SOURCE

All data lives in the GitHub repo `dpoly2/AgentHarness` as markdown files. The app reads them via the GitHub Contents API:

```
GET https://api.github.com/repos/dpoly2/AgentHarness/contents/{path}
Authorization: token {GITHUB_PAT}   // stored in .env.local
```

### Key paths to load:
| Path | Purpose |
|------|---------|
| `.agents/agents/roster.md` | Master registry — source of truth for all projects + agents |
| `.agents/agents/projects/{project}/` | Per-project agent definition files |
| `.agents/agents/projects/{project}/helpers/` | Helper agent files per project |
| `.agents/agents/*.md` | Shared/cross-project agents (root level) |
| `.agents/projects/{project}/PROJECT.md` | Project overview doc |
| `.agents/projects/{project}/*.md` | All project documentation files |

### Markdown parsing:
- Use `gray-matter` to parse YAML frontmatter (if present)
- Use `marked` or `react-markdown` to render markdown body content
- Extract structured fields from the `## Identity` section of each agent file (see Section 4)

---

## 3. APP STRUCTURE

```
src/
├── components/
│   ├── Sidebar.tsx           // Project + agent navigation tree
│   ├── ProjectCard.tsx       // Project summary card
│   ├── AgentCard.tsx         // Individual agent tile
│   ├── AgentDetail.tsx       // Full agent markdown rendered view
│   ├── HelperBadge.tsx       // Small badge for helper agents
│   ├── RosterTable.tsx       // Tabular view of all agents from roster.md
│   ├── ProjectDocs.tsx       // Docs browser for a project's .md files
│   └── StatusBadge.tsx       // 🟢 🟡 🔴 ⬜ status indicator
├── pages/ (or routes/)
│   ├── Dashboard.tsx         // Overview — all projects as cards
│   ├── ProjectView.tsx       // Single project: lead + specialists + helpers + docs
│   ├── AgentView.tsx         // Single agent full detail
│   └── RosterView.tsx        // Full roster table view
├── lib/
│   ├── github.ts             // GitHub API fetcher (getFile, listDir, getTree)
│   ├── parseAgent.ts         // Extract Identity fields from agent markdown
│   ├── parseRoster.ts        // Parse roster.md into structured project/agent objects
│   └── types.ts              // TypeScript interfaces
└── .env.local
    VITE_GITHUB_PAT=ghp_...
    VITE_GITHUB_REPO=dpoly2/AgentHarness
    VITE_GITHUB_BRANCH=main
```

---

## 4. DATA MODEL (TypeScript Interfaces)

```typescript
// types.ts

export interface AgentIdentity {
  agentName: string;        // from "Agent Name:" field in ## Identity
  project: string;          // from "Project:" field
  role: string;             // from "Role:" field
  type: 'lead' | 'specialist' | 'helper' | 'shared';
  filePath: string;         // GitHub path to the .md file
  rawMarkdown: string;      // full markdown content
}

export interface HelperAgent {
  agentName: string;
  assignedBy: string;       // from "Assigned By:" field
  taskType: string;         // from "Role:" field
  filePath: string;
  rawMarkdown: string;
}

export interface Project {
  id: number;               // from roster.md project index
  name: string;             // e.g. "XFTC Website & Plugin"
  slug: string;             // e.g. "xftc"
  leadAgent: AgentIdentity;
  specialists: AgentIdentity[];
  helpers: HelperAgent[];
  status: 'active' | 'pending' | 'blocked' | 'complete';
  statusLabel: string;      // e.g. "Sprint 3", "LLC Pending"
  projectDocsPath: string;  // e.g. ".agents/projects/xftc-redevelopment/"
  projectDocs: ProjectDoc[];
}

export interface ProjectDoc {
  filename: string;         // e.g. "PROJECT.md"
  title: string;            // first H1 from the file
  filePath: string;
  rawMarkdown: string;
}

export interface SharedAgent {
  agentName: string;
  specialty: string;
  projectsServed: string[];
  filePath: string;
  rawMarkdown: string;
}

export interface RosterData {
  lastUpdated: string;
  coordinator: string;
  projects: Project[];
  sharedAgents: SharedAgent[];
  automations: Automation[];
  openItems: OpenItem[];
}

export interface Automation {
  name: string;
  schedule: string;
  status: 'active' | 'paused' | 'archived';
}

export interface OpenItem {
  priority: '🔴' | '🟡' | '🟢';
  item: string;
  project: string;
  deadline: string;
}
```

---

## 5. AGENT FILE PARSING

Every agent `.md` file follows this structure. Parse these fields from the markdown body:

```markdown
# [Project Name] — [Role Title]        ← page title

## Identity
- **Agent Name:** s2t-project-lead     ← extract agentName
- **Project:** S2T Designs Agency      ← extract project
- **Role:** Client intake, ...         ← extract role
- **Type:** Helper Agent               ← if present, type = 'helper'
- **Assigned By:** s2t-project-lead    ← helper only

## Responsibilities                    ← render as bullet list
## Delegation Rules                    ← render as bullet list
## Current Sprint / Priority Items     ← render as bullet list (if present)
## Key Files                           ← render as file path list
```

**Parsing logic (`parseAgent.ts`):**
```typescript
function parseAgent(markdown: string, filePath: string): AgentIdentity {
  // 1. Find ## Identity section
  // 2. Extract lines matching "- **Field:** Value" pattern
  // 3. Map to AgentIdentity fields
  // 4. Detect type: 'helper' if "Type: Helper Agent" present, else infer from filename
}
```

**Type inference from filename:**
- `*-project-lead.md` or `*-project-manager.md` → `lead`
- `*-helper.md` → `helper`
- Files in `agents/*.md` (root, not in projects/) → `shared`
- Everything else → `specialist`

---

## 6. ROSTER PARSING

`roster.md` is the master source. Parse it into the full `RosterData` object.

**Sections to parse:**
- `## 🗂️ PROJECT INDEX` table → array of `{ id, name, leadAgent, status, statusLabel }`
- `## PROJECT N — [NAME]` sections → full project details including specialist + helper tables
- `## 🤖 SHARED / CROSS-PROJECT AGENTS` table → `SharedAgent[]`
- `## ⚙️ ACTIVE AUTOMATIONS` table → `Automation[]`
- `## 🚨 OPEN ITEMS` table → `OpenItem[]`

---

## 7. UI PAGES & COMPONENTS

### 7.1 Dashboard (Home)
- Header: "AgentHarness" title + last updated date from roster.md
- **Open Items strip** (top): 🔴 red items shown as alert cards across the top
- **Project grid**: one `ProjectCard` per project (8 cards)
  - Shows: project name, status badge, lead agent name, specialist count, helper count
  - Click → navigates to ProjectView

### 7.2 ProjectView
Layout: 2-column
- **Left column:** Agent tree
  - Lead agent card (prominent, full width of left col)
  - Specialist agents grid (2-up cards)
  - Helper agents row (smaller badge-style cards)
- **Right column:** Project docs
  - Tabs across the top: one tab per `.md` file in the project docs folder
  - Rendered markdown in the tab body (use `react-markdown` + `remark-gfm` for table support)
  - Docs tabs: PROJECT.md always first, then alphabetical

### 7.3 AgentView (click any agent card)
- Full-width rendered markdown of the agent file
- Breadcrumb: Dashboard → ProjectName → AgentName
- Back button
- Shows: Identity fields as structured header, then full markdown below
- If agent has `## Delegation Rules`: render as a visual flow (from this agent → to named agents, each as a clickable chip that navigates to that agent's view)
- If agent has `## Key Files`: render each path as a code badge

### 7.4 RosterView (accessible from top nav)
- Full table view mirroring roster.md
- Sortable columns: Project, Agent Name, Role, Type, Status
- Search/filter bar: filter by project name, agent name, or role keyword
- Export button: download filtered list as CSV

### 7.5 Shared Agents Panel
- Accessible from sidebar or top nav "Shared Agents"
- Cards for: grants-research-agent, grant-writer-agent, wordpresspluginsagent, web-dev-researcher, github-sync-agent
- Shows which projects they serve as tags

---

## 8. COMPONENT DETAILS

### StatusBadge
```tsx
// Maps emoji status to colored pill
🟢 → green pill  "Active"
🟡 → yellow pill "In Progress"
🔴 → red pill    "Blocked" / "ASAP"
⬜ → gray pill   "Pending"
```

### AgentCard
```
┌─────────────────────────────┐
│ 🤖  s2t-project-lead        │
│     Project Lead             │
│     S2T Designs Agency       │
│                              │
│  [lead]  🟢 Active           │
└─────────────────────────────┘
```
- Clickable → navigates to AgentView
- Color-coded left border: lead=blue, specialist=teal, helper=gray, shared=purple

### HelperBadge (compact)
```
[s2t-devops-helper → devops]
```
Small pill, clickable

### ProjectCard
```
┌───────────────────────────────────┐
│ S2T Designs Agency          🟢    │
│ Lead: s2t-project-lead            │
│ 5 specialists · 4 helpers         │
│ Status: Active                    │
└───────────────────────────────────┘
```

---

## 9. GITHUB API LAYER (`github.ts`)

```typescript
const BASE = 'https://api.github.com'
const REPO = import.meta.env.VITE_GITHUB_REPO      // dpoly2/AgentHarness
const PAT  = import.meta.env.VITE_GITHUB_PAT
const BRANCH = import.meta.env.VITE_GITHUB_BRANCH  // main

const headers = {
  Authorization: `token ${PAT}`,
  Accept: 'application/vnd.github+json'
}

// Get a single file's decoded content
export async function getFile(path: string): Promise<string>

// List all files in a directory
export async function listDir(path: string): Promise<{ name: string; path: string; type: 'file' | 'dir' }[]>

// Get the full repo tree (for pre-loading all agent paths at startup)
export async function getRepoTree(): Promise<{ path: string; type: string }[]>
```

**Caching:** Cache all fetched file content in `localStorage` with a 15-minute TTL. Add a "Refresh" button in the top nav that clears the cache and re-fetches.

---

## 10. SIDEBAR NAVIGATION

```
AgentHarness Viewer
────────────────────
🏠 Dashboard
📋 Full Roster
🤖 Shared Agents
────────────────────
PROJECTS
  1. XFTC                 🟡
  2. YEPC                 🟡
  3. The Elevation        🟡
  4. PBS Foundation       🟡
  5. Nutrue Apparel       🟡
  6. Smith Capital        🟡
  7. S2T Designs          🟢
  8. Productivity         🟢
────────────────────
⚙️  Automations
🚨 Open Items (3)
```

- Sidebar is collapsible
- Active route highlighted
- Open Items shows count badge if any 🔴 items exist

---

## 11. STYLING

- **Framework:** Tailwind CSS
- **Theme:** Dark mode default (dark navy/slate background, white text)
- **Accent color:** Electric blue (#2563EB) for links and active states
- **Font:** Inter (Google Fonts)
- **Agent card border colors:**
  - Lead agent: blue-500 left border
  - Specialist: teal-500 left border
  - Helper: gray-400 left border
  - Shared: purple-500 left border
- **Status badge colors:**
  - 🟢 Active: green-500 bg
  - 🟡 In Progress: yellow-500 bg
  - 🔴 Blocked/ASAP: red-500 bg
  - ⬜ Pending: gray-500 bg

---

## 12. STARTUP & LOADING SEQUENCE

1. On app load → fetch `.agents/agents/roster.md` via GitHub API
2. Parse roster.md into `RosterData` (projects, agents, automations, open items)
3. For each project → fetch agent files from `.agents/agents/projects/{slug}/`
4. Render Dashboard with loaded data
5. Lazy-load project docs and individual agent markdown on-demand (when user navigates to that project/agent)
6. Show skeleton loaders while fetching

---

## 13. LOCAL SETUP INSTRUCTIONS (include in README)

```bash
# 1. Clone the repo
git clone https://github.com/dpoly2/AgentHarness.git
cd AgentHarness

# 2. Install deps
npm install

# 3. Create .env.local
echo "VITE_GITHUB_PAT=your_pat_here" >> .env.local
echo "VITE_GITHUB_REPO=dpoly2/AgentHarness" >> .env.local
echo "VITE_GITHUB_BRANCH=main" >> .env.local

# 4. Run dev server
npm run dev
# → http://localhost:5173
```

PAT needs scopes: `repo` (if private) or no auth needed (if public).

---

## 14. OUT OF SCOPE (v1)

- No editing of agent files from the UI (read-only viewer)
- No authentication/login (local tool, PAT in .env.local)
- No real-time sync (15-min cache + manual refresh is sufficient)
- No drag-and-drop reorganization
- No agent file creation from the UI

These are candidates for v2.

---

## 15. FILE TO DELIVER

Copilot should produce:
- `src/` directory with all components, pages, lib files
- `package.json` with: react, react-dom, vite, tailwindcss, react-router-dom, react-markdown, remark-gfm, gray-matter, marked
- `tailwind.config.js`
- `vite.config.ts`
- `README.md` with setup instructions (Section 13 above)
- `.env.local.example` with placeholder values
