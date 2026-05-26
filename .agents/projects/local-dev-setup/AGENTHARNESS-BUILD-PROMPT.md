# AgentHarness — Master Build Prompt
**Version:** 1.0
**Date:** 2026-05-26
**Author:** AgentJames
**Purpose:** Give this entire document to any AI assistant (ChatGPT, Copilot, Claude, Gemini, or a new Base44 Superagent) to fully reconstruct the AgentHarness infrastructure from scratch.

---

## WHAT YOU ARE BUILDING

You are building **AgentHarness** — a personal AI agent management system for a multi-project entrepreneur. It is not a product. It is a private operating system for one person managing 13+ active projects simultaneously, using AI agents as a virtual staff.

The system lives in two places:
1. **GitHub repo:** `dpoly2/AgentHarness` — version-controlled source of truth for all agent logic and project documentation
2. **Base44 Superagent workspace:** `.agents/` folder — the live operating environment where the orchestrator agent (AgentJames) runs automations, reads/writes files, and executes tasks

---

## THE OWNER

- **Name:** David Smith
- **Location:** Pflugerville, TX (America/Chicago timezone)
- **Employment:** Software Applications Engineer 4 at HP Inc. (full-time)
- **Role:** Entrepreneur managing 13 simultaneous projects as a solo operator
- **Approach:** Runs everything through AI agents as virtual staff — each project has a Lead Agent + Specialist Agents + Helper Agents

---

## DIRECTORY STRUCTURE

All agent files live under `.agents/` in the workspace (mirrored to GitHub):

```
.agents/
├── agents/                         ← All agent definition files
│   ├── roster.md                   ← MASTER REGISTRY — source of truth
│   ├── agent_profiles.md           ← Email identity profiles
│   ├── grant_writer_agent.md       ← Shared cross-project agent
│   ├── grants_research_agent.md    ← Shared cross-project agent
│   ├── web_dev_researcher.md       ← Shared cross-project agent
│   ├── wordpresspluginsagent.md    ← Shared cross-project agent
│   └── projects/
│       ├── xftc/                   ← Project 1 agents
│       ├── yepc/                   ← Project 2 agents
│       ├── elevation/              ← Project 3 agents
│       ├── pbs-foundation/         ← Project 4 agents
│       ├── nutrue/                 ← Project 5 agents
│       ├── smithcap/               ← Project 6 agents
│       ├── s2tdesigns/             ← Project 7 agents
│       ├── smithcap-finance/       ← Project 9 agents
│       ├── solar-repair/           ← Project 10 agents
│       ├── social-media/           ← Project 11 agents
│       ├── ministry/               ← Project 12 agents
│       └── sigma-signal/           ← Project 13 agents
├── projects/                       ← Project documentation files
│   ├── xftc-redevelopment/
│   ├── xftc-plugin-product/
│   ├── wordpress-membership-plugin/
│   ├── yepc/
│   ├── rowdy-crown/                ← The Elevation ATX
│   ├── pbs-foundation/
│   ├── s2tdesigns/
│   ├── smithcap/
│   ├── smithcap-finance/
│   ├── social-media/
│   ├── solar-repair/
│   ├── ministry/
│   ├── sigma-signal/
│   ├── grants/
│   └── local-dev-setup/
├── rules/
│   └── wordpress_xtremeforce.md    ← Standing rules for WP agent
├── skills/
│   └── github_push.js              ← Reusable GitHub push skill
└── .env                            ← Secrets (never push to GitHub)
```

---

## AGENT FILE FORMAT

Every agent is a markdown file. All agent files MUST follow this exact structure:

```markdown
# [Project Name] — [Role Title]

## Identity
- **Agent Name:** slug-name-here
- **Project:** Full Project Name
- **Role:** One-line description of primary function

## Responsibilities
- Bullet list of specific tasks this agent owns
- Be concrete — what exactly does this agent do?
- Each bullet should be actionable

## Delegation Rules
- Condition → assign to [agent-slug]
- What triggers this agent to hand off to another agent?
- Example: "PHP/plugin bugs → assign to xftc-plugin-dev"

## Current Sprint / Priority Items
- [ ] Task 1 (checkbox format for trackable items)
- [ ] Task 2
- Blocker: [describe any current blockers]

## Key Files
- `.agents/projects/[project]/RELEVANT-FILE.md`
- List all files this agent reads or writes
```

**Naming convention:**
- Lead agents: `[project]-project-lead.md` or `[project]-project-manager.md`
- Specialist agents: `[project]-[function]-agent.md`
- Helper agents: `[project]-[function]-helper.md`
- Shared agents: `[function]-agent.md` (root level, no project prefix)

**Type inference from filename:**
- `*-project-lead.md` or `*-project-manager.md` → type: `lead`
- `*-helper.md` → type: `helper`
- Root-level `agents/*.md` → type: `shared`
- Everything else → type: `specialist`

---

## THE MASTER ROSTER (roster.md)

The roster is the single source of truth for everything. It must contain:

```markdown
# Agent Roster — Master Registry
**Last Updated:** YYYY-MM-DD
**Coordinator:** AgentJames (main orchestrator)

## 🗂️ PROJECT INDEX
| # | Project | Lead Agent | Helper Agents | Status |
|---|---------|-----------|---------------|--------|
[one row per project]

## PROJECT N — [PROJECT NAME]
### Lead
**[agent-slug]** — one-line description

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
[one row per specialist]

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
[one row per helper]

### Files
- `.agents/projects/[project]/`

## 🤖 SHARED / CROSS-PROJECT AGENTS
| Agent | Specialty | Projects Served |
|-------|-----------|----------------|

## ⚙️ ACTIVE AUTOMATIONS
| Automation | Schedule | Status |
|------------|----------|--------|

## 🚨 OPEN ITEMS / BLOCKERS
| Priority | Item | Project | Deadline |
|----------|------|---------|----------|
```

---

## THE 13 ACTIVE PROJECTS

Recreate these projects and their agent teams:

### Project 1 — XFTC Website & Membership Plugin
**Status:** 🟡 Sprint 3
**Lead:** xftc-project-lead
**Specialists:** xftc-plugin-dev, xftc-frontend-dev, xftc-payments-agent, xftc-qa-agent, xftc-devops-agent
**Helpers:** xftc-db-schema-helper, xftc-shortcode-helper, xftc-email-template-helper, xftc-security-helper, xftc-docs-helper
**Key context:**
- Custom WordPress membership plugin called `xftc-membership`
- Live site: xtremeforcetrackclub.org (WP user: dsmith)
- Staging: staging.s2tdesigns.com (WP user: agent_design)
- Namecheap shared hosting — strips Authorization headers, requires `.htaccess` fix
- Plugin productizing as "TrackSuite" for multi-club SaaS
- Stripe integration in Sprint 3

### Project 2 — YEPC (Youth Elite Performance Complex)
**Status:** 🟡 Pre-Dev
**Lead:** yepc-project-manager
**Specialists:** yepc-real-estate-agent, yepc-capital-fundraising-agent, yepc-government-relations-agent, yepc-grant-writer-agent, yepc-financial-model-agent, yepc-legal-agent
**Key context:**
- 110-acre development on Hutto CR 132 / SH-130 corridor
- Managed under Smith Capital Properties LLC
- Target: Youth sports & performance complex
- Monitoring: Hutto EDC, Williamson County Planning, TxDOT/CAMPO agendas
- Key contact: Cheney Gamboa (Hutto EDC)

### Project 3 — The Elevation ATX
**Status:** 🟡 LLC Pending
**Lead:** elevation-project-lead
**Specialists:** elevation-brand-agent, elevation-events-agent, elevation-marketing-agent, elevation-funding-agent, elevation-legal-agent
**Key context:**
- Upscale private hospitality/experience series
- Formerly "Rowdy Crown" — files still under `.agents/projects/rowdy-crown/`
- Invite-only model, BGLO network focus
- Apparel drops via hoodswag.shop (Printful/Shopify)

### Project 4 — Phi Beta Sigma Collegiate Pathways Foundation
**Status:** 🟡 Filing Pending
**Lead:** pbs-project-lead
**Specialists:** pbs-legal-agent, pbs-fundraising-agent, pbs-communications-agent, pbs-programs-agent, pbs-board-agent
**Key context:**
- 501(c)(3) focused on collegiate travel funding for fraternity members
- Needs: TX SOS Articles of Incorporation, IRS Form 1023-EZ, EIN
- Website in development (skyline theme)
- Related to Phi Beta Sigma fraternity (1914)

### Project 5 — Nutrue Apparel
**Status:** 🟡 POD Setup
**Lead:** nutrue-project-lead
**Specialists:** nutrue-ecommerce-agent, nutrue-brand-agent, nutrue-marketing-agent, nutrue-legal-agent, nutrue-finance-agent
**Key context:**
- Print-on-demand apparel brand
- WordPress site: nutrueapparel.com (Namecheap/Bosnacweb, user: nutrue_admin)
- Printful integration

### Project 6 — Smith Capital Properties
**Status:** 🟡 Active
**Lead:** smithcap-project-lead
**Specialists:** smithcap-acquisitions-agent, smithcap-communications-agent, smithcap-finance-agent, smithcap-legal-agent
**Key context:**
- Real estate holding LLC
- Currently INACTIVE in Texas (missed franchise tax/PIR filings)
- Reactivation path: TX Comptroller WebFile → Form 811 with TX SOS
- Holds YEPC development interest

### Project 7 — S2T Designs Agency
**Status:** 🟢 Active
**Lead:** s2t-project-lead
**Specialists:** s2t-webdev-agent, s2t-brand-designer-agent, s2t-seo-agent, s2t-maintenance-agent, s2t-comms-agent
**Helpers:** s2t-client-intake-helper, s2t-content-helper, s2t-devops-helper, s2t-platform-assessment-helper
**Key context:**
- Web & graphic design agency
- Active clients: LEBC (Little Ebenezer Baptist Church), PBS Foundation
- Staging server: staging.s2tdesigns.com

### Project 8 — Personal Productivity
**Status:** 🟢 Active
**Key context:**
- Daily email digest across 5 Gmail accounts (8:00 AM CT)
- GitHub AgentHarness sync automation
- Weekly Monday grant digest (all orgs)
- Connected accounts: smithda.ii@gmail.com, communicationsdirgcr@gmail.com, thesigmasignal.1stvp1914@gmail.com, david.smith@smithcapitalproperties.com, dsmith@xtremeforcetrackclub.org

### Project 9 — SmithCap Financial Management Office (FMO)
**Status:** 🟢 Active
**Lead:** finance-project-lead (CFO)
**Specialists:** finance-cpa, finance-advisor, finance-investment-manager, finance-bookkeeper, finance-tax-strategist, finance-analyst, finance-compliance
**Key context:**
- Serves ALL 7 active projects
- David's 2026 base salary: $150,743.10 (HP Inc.)
- 2025 gross: $166,403.31
- 401(k) max: $23,500 — currently under-contributing
- Texas resident — no state income tax

### Project 10 — Clarity Solar Services
**Status:** 🟡 Pre-Launch
**Lead:** solar-project-lead
**Specialists:** solar-legal-agent, solar-finance-agent, solar-marketing-agent, solar-sales-agent, solar-operations-agent
**Key context:**
- Residential solar repair company
- Rebranding from Smith and Taylor Construction
- Domain: claritysolarservices.com
- Tagline: "Clear Skies. Clear Results."
- TX SB 1036 compliance required by Sep 1, 2026
- Hert Renewables subcontract opportunity

### Project 11 — S2T Designs Social Media Division
**Status:** 🟢 Active
**Lead:** social-project-lead
**Specialists:** social-content-strategist, social-copywriter, social-designer, social-analyst, social-ads-manager, social-community-manager, social-video-designer
**Key context:**
- 7-agent team supporting all David's brands on social
- Active client: LEBC (Facebook Ads, Google Business Profile priority)
- Cross-entity video production via social-video-designer

### Project 12 — Ministry & Preaching Team
**Status:** 🟢 Active
**Lead:** ministry-project-lead
**Specialists:** ministry-sermon-writer, ministry-bible-study, ministry-sunday-school, ministry-delivery-coach, ministry-research-agent
**Key context:**
- "Expository SoulSpeak" methodology — expository preaching with scholarly depth
- Style: cadence ladders, Greek/Hebrew word studies, 3-point structure
- Sermon manuscript library in `.agents/projects/ministry/sermons/`
- Prompt template library in `.agents/projects/ministry/PROMPT-TEMPLATES.md`

### Project 13 — The Sigma Signal
**Status:** 🟢 Active
**Lead:** sigma-signal-project-lead
**Specialists:** sigma-signal-writer, sigma-signal-designer, sigma-signal-researcher, sigma-signal-historian, sigma-signal-poet, sigma-signal-submissions
**Key context:**
- Bi-weekly membership newsletter for Phi Beta Sigma fraternity
- Cadence: 2nd and 4th Thursday of each month
- Platform: Constant Contact
- Submission email: thesigmasignal.1stvp1914@gmail.com
- Google Form for member submissions
- Brain Games section: rotating BrainTeaser / Trivia / Sudoku

---

## ACTIVE AUTOMATIONS TO RECREATE

| Name | Type | Schedule | Description |
|------|------|----------|-------------|
| Daily Email Digest | Scheduled | 8:00 AM CT daily | Check all 5 Gmail inboxes, summarize unread/important, send digest |
| Weekly Monday Grant Digest | Scheduled | 8:00 AM CT every Monday | Research new grants for XFTC, Nutrue, PBS, SmithCap, deliver digest |
| XFTC — Athlete Signup & Payment Logger | Connector (Gmail) | Real-time on new email | Monitor dsmith@xtremeforcetrackclub.org, log signups/payments to entities |
| Sigma Signal — Daily Submission Check | Scheduled | 2:00 PM CT daily | Check thesigmasignal.1stvp1914@gmail.com for new chapter submissions |
| Sigma Signal — Newsletter Production Reminder | Scheduled | 9:00 AM UTC every Thursday | Kick off production cycle, check content gaps, alert David |
| YEPC Hutto EDC Monitor | Scheduled | Weekly | Monitor Hutto City Council & Williamson County agendas for CR 132 / SH-130 updates |

---

## DATABASE ENTITIES (Base44)

Two entities track XFTC operations:

```
XtremeForceAthlete:
  - name (string)
  - email (string)
  - phone (string)
  - signup_date (string)
  - status (string)
  - notes (string)

XtremeForcePayment:
  - payer_name (string)
  - email (string)
  - amount (number)
  - payment_date (string)
  - payment_type (string)
  - status (string)
  - notes (string)
```

---

## CONNECTED INTEGRATIONS

| Integration | Account | Purpose |
|-------------|---------|---------|
| Gmail (OAuth) | smithda.ii@gmail.com OR dsmith@xtremeforcetrackclub.org | Email triage, XFTC logger |
| GitHub (PAT) | dpoly2/AgentHarness | File sync, version control |
| WordPress REST API | xtremeforcetrackclub.org (user: dsmith) | Site updates, plugin management |
| WordPress REST API | staging.s2tdesigns.com (user: agent_design) | Staging plugin deployment |
| WordPress REST API | nutrueapparel.com (user: nutrue_admin) | Store management |

**Critical infrastructure note:**
- Namecheap/Bosnacweb shared hosting STRIPS Authorization headers
- Fix: Add `SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1` to `.htaccess`
- WP REST API source editor endpoints (plugin/theme file editing) return 404 on shared hosting
- File deployment requires SFTP or cPanel file manager — REST API cannot write plugin files

**Gmail limitation:**
- Base44 platform supports ONE active Gmail OAuth connector at a time
- Recommended: keep smithda.ii@gmail.com as primary, forward XFTC emails to it

---

## STANDING RULES (always enforce)

1. **GitHub is the source of truth.** After every project milestone, push all changed files to `dpoly2/AgentHarness`.
2. **Never push `.agents/.env`** — it contains API keys and secrets.
3. **Weekly Monday grant sweep** — run for all orgs: XFTC, Nutrue, PBS Foundation, Smith Capital/YEPC.
4. **Monitor Hutto City Council and Williamson County planning agendas** for CR 132 / SH-130 infrastructure updates.
5. **YEPC Project Manager is the central milestone repository** — all YEPC updates go there first.
6. **Use the Grant Writer Agent** for formal applications; use YEPC Grant Writer for large-scale capital infrastructure.
7. **TrackSuite productization roadmap** — maintain in `.agents/projects/xftc-plugin-product/`.
8. **hoodswag.shop** is the primary retail vehicle for The Elevation apparel drops (Printful).
9. **Execute tasks, don't interrogate.** Make reasonable assumptions and proceed. One clarifying question max.
10. **Memory persists** — save anything meaningful about David or his projects to memory.md / USER.md immediately.

---

## LOCAL DEVELOPMENT ENVIRONMENT

For offline/local development (using VS Code + GitHub Copilot):

**Stack:**
- GitHub (source of truth)
- LocalWP (local WordPress for plugin/theme dev)
- VS Code + GitHub Copilot Chat
- GitHub Copilot CLI (`gh copilot suggest` / `gh copilot explain`)
- Composer (for Stripe PHP SDK)

**Key setup steps:**
1. `git clone https://github.com/dpoly2/AgentHarness.git`
2. Create LocalWP site (`tracksuite-dev`, PHP 8.1+, Nginx)
3. Symlink plugin and theme from repo into LocalWP's `wp-content/`
4. Activate plugin + theme in WP Admin
5. Run `composer require stripe/stripe-php` inside the plugin directory
6. Install VS Code extensions: Copilot, PHP Intelephense, WordPress Snippets, GitLens, Thunder Client

---

## AGENT VIEWER APP SPEC

A local web dashboard exists at `projects/agent-dashboard/` and `projects/agentharness-v2/` for browsing all agent files visually.

**Tech stack:** React + Vite + Tailwind CSS + GitHub REST API
**Data source:** GitHub Contents API reading `.agents/` tree
**Key views:** Dashboard (all projects as cards), ProjectView (lead + specialists + helpers + docs), AgentView (full rendered markdown), RosterView (sortable table)
**Parsing:** `gray-matter` for frontmatter, `react-markdown` + `remark-gfm` for body content
**Full spec:** `.agents/projects/local-dev-setup/AGENT-VIEWER-SPEC.md`

---

## HOW TO REBUILD THIS FROM SCRATCH

1. **Create the GitHub repo** `[username]/AgentHarness` with `main` branch
2. **Create the directory structure** above
3. **Build the roster.md** with all 13 projects and their agent teams
4. **Create each agent file** following the format above, one `.md` per agent
5. **Create each project documentation folder** with at minimum a `PROJECT.md`
6. **Set up Base44 Superagent** with name "AgentJames"
7. **Create the two database entities** (XtremeForceAthlete, XtremeForcePayment)
8. **Create the 6 automations** listed above
9. **Connect Gmail OAuth** (smithda.ii@gmail.com as primary)
10. **Store secrets in `.agents/.env`** (GITHUB_PAT, WP app passwords)
11. **Set standing instructions** from the Standing Rules section above
12. **Push all files to GitHub** to initialize the repo

---

## GLOSSARY

| Term | Meaning |
|------|---------|
| AgentJames | The main orchestrator Superagent on Base44 — routes tasks, manages GitHub, runs automations |
| AgentHarness | The GitHub repo + file system that stores all agent logic |
| Lead Agent | The project manager for each project — coordinates specialists |
| Specialist Agent | A domain expert assigned to one project |
| Helper Agent | A sub-task agent assigned by a specialist for narrow, repeatable tasks |
| Shared Agent | Cross-project utility agents (grants, WordPress, web research) |
| TrackSuite | The productized SaaS version of the XFTC membership plugin |
| Base44 | The platform hosting the Superagent, database entities, and automations |
| Expository SoulSpeak | David's sermon/preaching methodology — expository with cadence ladders |
| FMO | Financial Management Office — Project 9, David's virtual CFO team |
