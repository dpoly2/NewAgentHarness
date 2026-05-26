# AgentHarness — Universal Build Prompt
**Version:** 1.0
**Date:** 2026-05-26
**Purpose:** Give this document to any AI assistant (ChatGPT, Claude, Gemini, GitHub Copilot, or a Base44 Superagent) to build a personal AI agent management system from scratch — customized to YOUR life and projects.

---

## WHAT THIS BUILDS

**AgentHarness** is a personal AI agent operating system for someone managing multiple projects simultaneously with limited time. Instead of one AI doing everything, you organize specialized AI agents like a virtual staff — each one owns a domain, knows its responsibilities, and delegates properly.

It is NOT a product. It is your private infrastructure.

It runs in two places:
1. **A GitHub repo** — version-controlled source of truth for all agent logic and project documentation
2. **A Base44 Superagent workspace** (or any persistent AI environment) — the live operating layer where your orchestrator agent runs automations, reads/writes files, and executes tasks

---

## STEP 1 — DEFINE YOUR PROFILE

Tell the AI building this system the following about yourself:

```
Name: [Your name]
Location / Timezone: [City, State — e.g. Austin, TX / America/Chicago]
Primary employment: [Your day job, if any]
Role: [How you see yourself — entrepreneur, creator, nonprofit director, etc.]
How many projects are you actively managing right now? [Number]
What is your biggest bottleneck? [Time / organization / delegation / communication / all of the above]
What tools do you already use? [Gmail, Notion, GitHub, Shopify, WordPress, etc.]
```

---

## STEP 2 — DEFINE YOUR PROJECTS

For each active project, provide:

```
Project Name: [Name]
Type: [Business / Nonprofit / Real Estate / Creative / Personal / Other]
Status: [Active / Pre-launch / In development / Blocked]
What is the goal of this project? [One sentence]
What are the 3 biggest tasks happening right now?
Who else is involved? [Just you / small team / contractors / board]
What tools/platforms does this project use? [WordPress, Shopify, Stripe, etc.]
Does it have its own email, website, or social accounts? [Yes/No + details]
```

Repeat for every project. There is no limit — the system scales.

---

## STEP 3 — UNDERSTAND THE AGENT HIERARCHY

Every project gets three tiers of agents:

```
TIER 1 — LEAD AGENT (1 per project)
  - The project manager
  - Tracks milestones, coordinates specialists, flags blockers
  - Named: [project]-project-lead

TIER 2 — SPECIALIST AGENTS (3–6 per project)
  - Domain experts (legal, finance, marketing, dev, ops, etc.)
  - Each owns a specific function within the project
  - Named: [project]-[function]-agent

TIER 3 — HELPER AGENTS (as needed)
  - Sub-task specialists assigned by specialists
  - Handle narrow, repeatable work (templates, research, formatting)
  - Named: [project]-[function]-helper

SHARED AGENTS (cross-project, no project prefix)
  - Utility agents that serve multiple projects
  - Examples: grants-research-agent, legal-research-agent, web-dev-agent
  - Named: [function]-agent
```

---

## STEP 4 — AGENT FILE FORMAT

Every agent is a markdown file saved to `.agents/agents/projects/[project]/[agent-slug].md`

Use this exact template for every agent you create:

```markdown
# [Project Name] — [Role Title]

## Identity
- **Agent Name:** [slug-name-here]
- **Project:** [Full Project Name]
- **Role:** [One-line description of primary function]

## Responsibilities
- [Specific task this agent owns]
- [Another specific task]
- [Be concrete — what does this agent actually do?]

## Delegation Rules
- [Condition] → assign to [other-agent-slug]
- [What triggers a handoff to another agent?]

## Current Sprint / Priority Items
- [ ] [Active task 1]
- [ ] [Active task 2]
- Blocker: [Any current blocker, or "None"]

## Key Files
- `.agents/projects/[project]/RELEVANT-FILE.md`
- [List all files this agent reads or writes]
```

**Naming rules:**
- Lead agents: `[project]-project-lead.md`
- Specialist agents: `[project]-[function]-agent.md`
- Helper agents: `[project]-[function]-helper.md`
- Shared agents: `[function]-agent.md` (root level)

---

## STEP 5 — THE MASTER ROSTER

Create one file: `.agents/agents/roster.md`

This is your single source of truth. Every project, every agent, every automation, every open item lives here.

```markdown
# Agent Roster — Master Registry
**Last Updated:** [DATE]
**Coordinator:** [Your orchestrator agent name]

## 🗂️ PROJECT INDEX
| # | Project | Lead Agent | Specialists | Status |
|---|---------|-----------|-------------|--------|
| 1 | [Project Name] | [lead-agent-slug] | [count] specialists | 🟢 Active |
| 2 | [Project Name] | [lead-agent-slug] | [count] specialists | 🟡 In Progress |

## PROJECT 1 — [PROJECT NAME]
### Lead
**[agent-slug]** — [one-line description]

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| [slug] | [Role Title] | [Key tasks] |

### Helper Agents
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| [slug] | [parent-agent] | [Task type] |

### Files
- `.agents/projects/[project]/`

[Repeat for each project]

## 🤖 SHARED / CROSS-PROJECT AGENTS
| Agent | Specialty | Projects Served |
|-------|-----------|----------------|
| [slug] | [function] | [Project 1, Project 3] |

## ⚙️ ACTIVE AUTOMATIONS
| Automation Name | Schedule | Status |
|----------------|----------|--------|
| [Name] | [Daily 8am / Weekly Monday / Real-time] | 🟢 Active |

## 🚨 OPEN ITEMS / BLOCKERS
| Priority | Item | Project | Deadline |
|----------|------|---------|----------|
| 🔴 | [Urgent item] | [Project] | [Date] |
| 🟡 | [Normal item] | [Project] | [Date] |
```

---

## STEP 6 — DIRECTORY STRUCTURE

Create this folder structure in your workspace and GitHub repo:

```
.agents/
├── agents/
│   ├── roster.md                    ← MASTER REGISTRY
│   ├── agent_profiles.md            ← Email/identity profiles per account
│   ├── [shared-agent-1].md          ← Cross-project shared agents
│   ├── [shared-agent-2].md
│   └── projects/
│       ├── [project-1]/
│       │   ├── [project-1]-project-lead.md
│       │   ├── [project-1]-[function]-agent.md
│       │   └── helpers/
│       │       └── [project-1]-[task]-helper.md
│       └── [project-2]/
│           └── ...
├── projects/
│   ├── [project-1]/
│   │   ├── PROJECT.md               ← Project overview and goals
│   │   ├── SPRINT-1.md              ← Current work (if technical)
│   │   └── [other-docs].md
│   └── [project-2]/
│       └── ...
├── rules/
│   └── [any-standing-rules].md      ← Always-on instructions
├── skills/
│   └── [reusable-scripts].js        ← Reusable automations/scripts
└── .env                             ← Secrets — NEVER push to GitHub
```

---

## STEP 7 — AUTOMATIONS TO SET UP

Automations trigger your orchestrator agent automatically. Design them around your recurring needs:

**Common automation patterns:**

```
DAILY DIGEST
  Type: Scheduled — every day at [your wake time]
  Task: Check all connected inboxes/channels, summarize important items, alert me

WEEKLY RESEARCH SWEEP
  Type: Scheduled — every Monday morning
  Task: Research new grants/funding/news relevant to [your organizations], compile digest

REAL-TIME INBOX MONITOR
  Type: Connector (Gmail webhook)
  Task: When new email arrives matching [criteria], extract data and log to database

CONTENT PRODUCTION REMINDER
  Type: Scheduled — [your cadence, e.g. every other Thursday]
  Task: Check submission status for [newsletter/publication], identify content gaps, alert me

AGENDA / NEWS MONITOR
  Type: Scheduled — weekly
  Task: Check [government body / news source] for updates relevant to [your project]
```

For each automation, define:
- **Trigger:** When does it run?
- **Task:** What exactly should the agent do when it fires?
- **Output:** Where should results go? (message, database, file, email)

---

## STEP 8 — DATABASE ENTITIES

If your projects involve tracking people, payments, leads, or inventory — create entities:

```
Entity name: [PascalCase, e.g. ClientLead]
Fields:
  - name (string)
  - email (string)
  - phone (string)
  - status (string — e.g. "Active", "Pending", "Inactive")
  - date (string)
  - notes (string)
  - amount (number — if tracking payments)
```

**Examples by project type:**
- Nonprofit: `AthleteRecord`, `DonorRecord`, `EventAttendee`
- Real estate: `DealPipeline`, `PropertyLead`, `TenantRecord`
- Agency: `ClientProject`, `InvoiceRecord`, `LeadInquiry`
- E-commerce: `CustomerOrder`, `ProductInventory`, `ReturnRequest`
- Newsletter: `SubscriberRecord`, `ContentSubmission`, `IssueLog`

---

## STEP 9 — CONNECTED INTEGRATIONS

Map out what you need to connect:

```
Gmail / Email
  → Which accounts? (list all email addresses)
  → Primary use: inbox monitoring, sending, digests

GitHub
  → Repo name: [username]/AgentHarness
  → Use: version control for all agent files

WordPress (if applicable)
  → Site URL(s):
  → Admin username(s):
  → Use: site updates, plugin management, content publishing

Payments (if applicable)
  → Provider: Stripe / PayPal / Wix Payments
  → Use: subscriptions, event tickets, donations

Social Media (if applicable)
  → Platforms: Instagram / LinkedIn / TikTok / Facebook
  → Use: post scheduling, analytics, ad management

Calendar
  → Google Calendar / Outlook
  → Use: meeting scheduling, deadline tracking, reminders
```

**Shared hosting note (WordPress sites):**
If your WordPress site is on Namecheap, Bluehost, or other shared hosting — the server may strip Authorization headers. Fix this by adding to `.htaccess`:
```
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
```

---

## STEP 10 — STANDING RULES (ALWAYS-ON INSTRUCTIONS)

Tell your orchestrator agent these rules once — they apply to every session forever:

```
1. GitHub is the source of truth. After every milestone, push all changed files to [repo].
2. Never push .agents/.env — it contains secrets.
3. [Your recurring research task] — run every [frequency] for [your organizations].
4. Monitor [government body / news source] for updates on [your key project].
5. [Your central project manager] is the canonical milestone repository — all updates go there first.
6. Use [agent name] for [specific task type].
7. Execute tasks, don't interrogate. Make reasonable assumptions. One clarifying question max.
8. Save anything meaningful about me or my projects to memory immediately.
9. [Any other always-on rule specific to your situation]
```

---

## STEP 11 — ORCHESTRATOR AGENT IDENTITY

Your main agent needs an identity. Define:

```
Agent name: [What do you want to call it? e.g. "James", "Atlas", "Max", "Nova"]
Personality vibe: [Sharp & direct / Warm & encouraging / Analytical / Creative / Balanced]
Primary job: [What is the ONE thing you most need this agent for?]
Tone: [Professional / Casual / Somewhere in between]
```

The orchestrator agent:
- Routes tasks to the right specialist
- Manages GitHub syncs
- Runs all automations
- Is your first point of contact for every task
- Remembers everything across sessions via memory files

---

## STEP 12 — BUILD CHECKLIST

Work through these in order:

```
[ ] 1. Create GitHub repo: [username]/AgentHarness
[ ] 2. Create .agents/ directory structure (clone or build manually)
[ ] 3. Set up orchestrator agent on Base44 (or your chosen platform)
[ ] 4. Build roster.md with all your projects and agent teams
[ ] 5. Create each agent .md file (lead → specialists → helpers)
[ ] 6. Create each project folder with at minimum a PROJECT.md
[ ] 7. Create database entities for any tracking needs
[ ] 8. Create automations (start with daily digest + weekly research sweep)
[ ] 9. Connect Gmail OAuth (primary account first)
[ ] 10. Store all secrets in .agents/.env
[ ] 11. Set standing instructions in your orchestrator agent
[ ] 12. Push all files to GitHub
[ ] 13. Test: ask your orchestrator agent to read the roster and describe your projects
[ ] 14. Test: trigger one automation manually and confirm it runs correctly
[ ] 15. Iterate — add agents as you identify gaps
```

---

## COMMON SPECIALIST AGENT ARCHETYPES

Use these as starting points. Mix and match for your projects:

| Function | Agent Name Pattern | Best For |
|----------|-------------------|----------|
| Project Manager | `[project]-project-lead` | Every project |
| Legal & Compliance | `[project]-legal-agent` | LLCs, nonprofits, contracts |
| Finance & Bookkeeping | `[project]-finance-agent` | Any revenue-generating project |
| Marketing & Growth | `[project]-marketing-agent` | E-commerce, events, brands |
| Content & Copywriting | `[project]-content-agent` | Newsletters, blogs, social |
| Web Development | `[project]-webdev-agent` | WordPress, Shopify, custom sites |
| Operations | `[project]-operations-agent` | Service businesses, logistics |
| Fundraising & Grants | `[project]-fundraising-agent` | Nonprofits, foundations |
| Sales & Outreach | `[project]-sales-agent` | B2B, lead generation |
| Research | `[project]-research-agent` | Any project needing intel |
| Community & Relations | `[project]-community-agent` | Member orgs, churches, clubs |
| Design | `[project]-brand-agent` | Brand identity, visual creative |

---

## COMMON SHARED AGENT ARCHETYPES

These serve ALL your projects without being tied to one:

| Agent Slug | What It Does |
|------------|-------------|
| `grants-research-agent` | Sweeps grant databases weekly for all your orgs |
| `grant-writer-agent` | Drafts formal funding applications |
| `legal-research-agent` | Researches regulations, filings, compliance across projects |
| `web-dev-agent` | Handles WordPress/site tasks across multiple domains |
| `financial-advisor-agent` | Cross-entity financial planning and tax strategy |
| `social-media-agent` | Content creation and scheduling across all brands |
| `email-manager-agent` | Inbox triage across multiple email identities |

---

## GLOSSARY

| Term | Meaning |
|------|---------|
| AgentHarness | The GitHub repo + file system that stores all agent logic |
| Orchestrator | Your main agent — routes tasks, manages memory, runs automations |
| Lead Agent | The project manager for a specific project |
| Specialist Agent | A domain expert assigned to one project |
| Helper Agent | A sub-task agent for narrow, repeatable tasks within a specialty |
| Shared Agent | A cross-project utility agent (grants, legal, web, etc.) |
| Roster | The master registry file — source of truth for all projects and agents |
| Standing Rules | Always-on instructions your orchestrator follows in every session |
| Entity | A database table for structured data (athletes, payments, leads, etc.) |
| Automation | A scheduled or event-triggered task your orchestrator runs automatically |
| `.env` | A file storing secrets/API keys — NEVER commit to GitHub |

---

## TIPS FROM PRODUCTION USE

- **Start with 2–3 projects max.** Get the pattern right, then scale.
- **The roster.md is everything.** Keep it updated — it's what your agent reads to understand your world.
- **Automations compound.** A daily digest + weekly research sweep covers 80% of your information needs automatically.
- **Name agents descriptively.** `xftc-plugin-dev` is better than `developer-1` — you need to know at a glance who does what.
- **Helper agents are underrated.** Breaking a specialist into a specialist + helper for narrow tasks keeps each agent focused and reusable.
- **Push to GitHub after every meaningful change.** Your repo is your backup and your history.
- **One Gmail connector at a time** (Base44 limitation). Use email forwarding to route multiple inboxes through one primary account if needed.
- **Memory is manual.** Tell your orchestrator agent to save important decisions, preferences, and project context explicitly — don't assume it remembers.
- **Standing rules beat repeating yourself.** If you say the same thing more than twice, make it a standing rule.
