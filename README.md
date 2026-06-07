# AgentHarness

**David Smith's personal AI agent system — built on Base44 Superagent.**

> *"We invest with discipline, operate with integrity, and build lasting value across generations."*

**Last Updated:** June 7, 2026
**Version:** 3.0 — Legacy Alpha Capital AI + Full Portfolio Architecture

---

## 🏛️ System Overview

AgentHarness is a multi-agent AI operating system managing 15+ active projects across David Smith's full portfolio: investment/finance, web development, nonprofit, real estate, social media, ministry, and apparel.

```
AgentHarness/
├── .agents/
│   ├── agents/projects/         # All agent config files by project
│   ├── projects/                # Project documentation & specs
│   ├── rules/                   # Standing agent rules (auto-loaded)
│   ├── skills/                  # Reusable agent scripts
│   └── .memory/                 # Agent memory & conversation logs
├── .github/
│   └── workflows/
│       └── deploy-agent-dashboard.yml  # CI/CD — Agent Dashboard
├── projects/                    # Legacy project files
│   ├── xftc-redevelopment/      # XFTC Plugin & Theme
│   └── wordpress-membership-plugin/
└── README.md
```

---

## 🤖 Agent Roster — 35 Active Agents

### 💼 Markets Division — Legacy Alpha Capital AI (v6.0)
| Agent ID | Role |
|----------|------|
| `markets-project-lead` | CIO / Command Center (v7) — full institutional hierarchy |
| `markets-cio` | Portfolio Manager / CIO — master thesis, capital allocation |
| `markets-cro` | Chief Risk Officer — risk mandate, trade veto authority |
| `markets-quant` | Quant Research Desk — mathematical validation |
| `markets-intelligence-desk` | Market Intelligence & Sentiment — catalyst detection |
| `markets-options-strategist` | Legacy Capital Analyst + Options Strategy |
| `markets-tactical-alpha` | Tactical Alpha / Speculation Desk |
| `markets-equity-analyst` | Equity Research |
| `markets-macro-analyst` | Macro & Economic Research |
| `markets-technical-analyst` | Technical Analysis |

### 🏗️ XFTC — Xtreme Force Track Club
| Agent ID | Role |
|----------|------|
| `xftc-project-lead` | Project Lead |
| `xftc-plugin-dev` | WordPress Plugin Developer |
| `xftc-frontend-dev` | Frontend Developer |
| `xftc-payments-agent` | Payments Integration |
| `xftc-qa-agent` | QA Testing |
| `wordpress-agent-xftc` | XFTC WordPress Site Manager |

### 🎨 S2T Designs
| Agent ID | Role |
|----------|------|
| `s2t-project-lead` | Project Lead |
| `s2t-webdev-agent` | Web Development |
| `s2t-seo-agent` | SEO Strategy |

### 🏛️ PBS / Psi Beta Sigma
| Agent ID | Role |
|----------|------|
| `pbs-project-lead` | Project Lead |
| `pbs-fundraising-agent` | Fundraising |
| `pbs-communications-agent` | Communications |
| `wordpress-agent-pbs` | PBS WordPress Site Manager |

### 📈 SmithCap Finance
| Agent ID | Role |
|----------|------|
| `finance-cfo` | CFO / Lead |
| `finance-cpa` | CPA / Accounting |
| `finance-tax-strategist` | Tax Strategy |

### 🌱 Grants Division
| Agent ID | Role |
|----------|------|
| `grant-writer-agent` | Grant Writer |
| `grants-research-agent` | Grants Researcher |
| `yepc-grant-writer-agent` | YEPC Grant Writer |
| `yepc-real-estate-research-agent` | YEPC Real Estate Research |
| `yepc-project-manager` | YEPC Project Manager |

### 📣 Social Media Division
| Agent ID | Role |
|----------|------|
| `social-project-lead` | Project Lead |
| `social-content-strategist` | Content Strategy |
| `social-copywriter` | Copywriting |
| `social-ads-manager` | Paid Ads |
| `social-analyst` | Analytics |

### ⚡ Other Divisions
| Agent ID | Project |
|----------|---------|
| `ministry-project-lead` | Ministry / SoulSpeak |
| `ministry-sermon-writer` | Sermon Writing |
| `sigma-signal-project-lead` | The Sigma Signal Newsletter |
| `sigma-signal-writer` | Newsletter Writing |
| `solar-project-lead` | Clarity Solar Services |
| `elevation-project-lead` | The Elevation ATX |
| `nutrue-project-lead` | Nutrue Apparel |
| `travel-project-lead` | Travel Division |
| `smithcap-acquisitions-agent` | SmithCap Acquisitions |

---

## 📁 Active Projects — 15+

| # | Project | Type | Status |
|---|---------|------|--------|
| 1 | **XFTC Redevelopment** | WordPress Plugin + Theme | 🟡 Sprint 3 Pending |
| 2 | **TrackClub Pro** | Multi-tenant SaaS plugin product | 🔵 Planning |
| 3 | **PBS Foundation** | 501(c)(3) + WordPress site | 🟡 Site live, 501c3 pending |
| 4 | **YEPC** | 110-acre real estate development | 🟡 OZ 2.0 nomination active |
| 5 | **S2T Designs** | Web & design agency | 🟢 Active — 5 clients |
| 6 | **Legacy Alpha Capital AI** | AI hedge fund system | 🟢 Live — 6 agents deployed |
| 7 | **Smith Cap Group** | Holding company | 🟡 Brand guide complete, entity filing pending |
| 8 | **SmithCap Finance** | Virtual CFO system | 🟢 Active |
| 9 | **The Sigma Signal** | Bimonthly newsletter | 🟢 Active |
| 10 | **Clarity Solar Services** | Solar repair company | 🔵 Formation pending |
| 11 | **The Elevation ATX** | Private events | 🔵 Planning |
| 12 | **Nutrue Apparel** | POD apparel | 🟡 Active (hoodswag.shop) |
| 13 | **Ministry / SoulSpeak** | Expository preaching content | 🟢 Active |
| 14 | **Social Media Division** | Multi-brand social | 🟢 Active |
| 15 | **Project Night King** | Custom automotive build | 🔵 Planning |
| 16 | **LEBC (S2T Client)** | Little Ebenezer Baptist Church | 🟡 Discovery pending |

---

## ⚙️ Automations — Base44 Scheduled

| Automation | Schedule | Status | Notes |
|-----------|----------|--------|-------|
| Daily Agent Reflexion Report | 7:00 AM CT daily | ✅ Active | Queries AgentRunLog + AgentSkillVersion |
| Daily Email Digest | 8:00 AM CT daily | ⚠️ Auth issue | Gmail OAuth — smithda.ii@gmail.com |
| XFTC Signup/Payment Logger | Every 6 hours | ⚠️ Blocked | Needs Gmail forward dsmith@xftc.org → smithda.ii |
| Sigma Signal Submission Check | Daily | ⚠️ Blocked | Same Gmail connector limitation |
| LEBC 501(c)(3) Monitor | Weekly | ✅ Active | IRS Tax Exempt Search monitor |
| Markets Weekly Brief | Mon 6:30 AM CT | ✅ Active | Legacy Alpha Capital AI CIO report |
| AGP Event Monitor | Daily (temporary) | ✅ Active | Expires post-AGP weekend |

---

## 🗄️ Data Entities (Base44)

| Entity | Purpose |
|--------|---------|
| `AgentRunLog` | Per-run agent performance logging (score, critique, status) |
| `AgentSkillVersion` | Skill file version history and improvement tracking |
| `XtremeForceAthlete` | XFTC athlete registration records |
| `XtremeForcePayment` | XFTC payment tracking |
| `Task` | Cross-project task management |
| `MarketPick` | Weekly market picks — Legacy Alpha Capital AI |

---

## 🚀 CI/CD — GitHub Actions

### deploy-agent-dashboard.yml
Triggered on every push to `main`.

```
Push to main
  → Checkout code
  → Build agent dashboard (Node 18)
  → SCP deploy to production server
  → PM2 reload with healthcheck
  → Rollback on failure
```

**Required GitHub Secrets:**
| Secret | Purpose |
|--------|---------|
| `DEPLOY_HOST` | Production server IP/hostname |
| `DEPLOY_USER` | SSH username |
| `SSH_PRIVATE_KEY` | SSH private key |
| `DEPLOY_PORT` | SSH port (default: 22) |
| `DEPLOY_PATH` | Deployment directory path |
| `AGENT_SERVER_PORT` | Agent dashboard port (default: 4000) |

---

## 🔌 Integrations

| Service | Status | Purpose |
|---------|--------|---------|
| Gmail (smithda.ii@gmail.com) | ✅ Connected | Primary email connector |
| Google Drive | ✅ Connected | File storage |
| GitHub | ✅ Connected | Version control |
| Outlook | ✅ Connected | davidallensmith77@outlook.com |
| Gmail (dsmith@xftc.org) | ⚠️ Forward needed | XFTC — forward to primary Gmail |
| Gmail (thesigmasignal@gmail.com) | ⚠️ Forward needed | Sigma Signal — forward to primary Gmail |

> **Note:** Base44 supports one active Gmail OAuth connector at a time. Secondary Gmail accounts must forward to `smithda.ii@gmail.com`.

---

## 🏦 Smith Cap Group — Portfolio Entities

| Entity | Type | Status |
|--------|------|--------|
| Smith Cap Group LLC | Parent Holding | 🔴 File TX SOS Form 205 |
| S2T Designs LLC | Operating — S-Corp | 🔴 Pending formation |
| Clarity Solar Services LLC | Operating — S-Corp | 🔴 Pending formation |
| The Elevation ATX LLC | Operating | 🔴 Pending formation |
| Nutrue Apparel LLC | Operating | 🔴 Pending formation |
| YEPC LLC | For-Profit Development | 🔴 Pending formation |
| SmithCap FMO | Financial | 🟡 Active (informal) |
| XFTC | 501(c)(3) Affiliate | ✅ Active |
| Elevate Scholars Foundation | 501(c)(3) Affiliate | 🟡 Formation pending |

> **Critical:** Form 2553 (S-Corp election) must be filed within 75 days of Holdings LLC formation.

---

## 📊 Reflexion Scoring System

All agents are scored on every run using this rubric:

| Score | Grade | Action |
|-------|-------|--------|
| 0.90–1.00 | ✅ Excellent | No action |
| 0.75–0.89 | ✅ Good | Minor note |
| 0.60–0.74 | ⚠️ Acceptable | Flag for review |
| < 0.60 | 🔴 Poor | Revise skill file, log to AgentSkillVersion |

**Formula:** `overall = completion×0.5 + quality×0.35 + efficiency×0.15`

---

## 🌐 Key URLs

| Resource | URL |
|----------|-----|
| XFTC Site | xtremeforcetrackclub.org |
| PBS Site | psibetasigma1914.org |
| S2T Staging | staging.s2tdesigns.com |
| Nutrue Shop | hoodswag.shop |
| Base44 Agent | app.base44.com/superagent/6a0bce17b730c0de488b80fb |

---

## 🔗 AcronHub Integration

The AgentHarness nightly automation sync integrates with **AcronHub** for cron job monitoring and uptime tracking of all scheduled Base44 automations.

**Setup:**
1. Each Base44 automation pings its AcronHub check URL on completion
2. AcronHub alerts David if any automation misses its expected window
3. Dashboard: monitor all 13 active automations from a single view

**Monitored Automations:**
| Automation | Expected Interval | AcronHub Check |
|-----------|------------------|----------------|
| Daily Reflexion Report | 24h | ✅ Configured |
| Daily Email Digest | 24h | ✅ Configured |
| XFTC Logger | 6h | ✅ Configured |
| Markets Weekly Brief | 7 days | ✅ Configured |
| LEBC Monitor | 7 days | ✅ Configured |

> To add a new automation to monitoring: create a new check in AcronHub dashboard, copy the ping URL, and add it to the automation's task description so the agent pings it on completion.

---

*AgentHarness v3.0 — Built by David Smith on Base44 Superagent*
*Last updated: June 7, 2026*
