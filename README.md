# AgentHarness

David Smith's personal AI agent system — built on Base44 Superagent.

**Last Updated:** May 20, 2026

---

## Architecture

```
AgentHarness/
├── agents/                        # Individual agent profiles and configs
├── rules/                         # Site-specific agent rules
├── projects/
│   ├── xftc-redevelopment/        # XFTC custom plugin (Sprint 2 complete ✅)
│   │   ├── plugin/
│   │   │   └── xftc-membership/   # Full WordPress membership plugin
│   │   │       ├── includes/      # Core PHP classes
│   │   │       ├── admin/views/   # WP Admin panels
│   │   │       ├── public/views/  # Parent/athlete portal views
│   │   │       └── api/           # REST API endpoints
│   │   ├── SPRINT-2.md            # Sprint 2 task tracking
│   │   ├── ARCHITECTURE.md
│   │   └── PROPOSAL.md
│   ├── wordpress-membership-plugin/
│   └── yepc/                      # Youth Elite Performance Complex
└── README.md
```

---

## Agent Lanes

### Personal Productivity
Each email identity has a dedicated agent profile:

| Agent | Account | Status |
|-------|---------|--------|
| `smithdaiiagent` | smithda.ii@gmail.com | ✅ Connected |
| `communicationsdirgcr` | communicationsdirgcr@gmail.com | ✅ Connected |
| `thesigmasignal` | thesigmasignal.1stvp1914@gmail.com | ✅ Connected |
| `smithcapitalproperties` | david.smith@smithcapitalproperties.com | 🔄 Authorizing |
| `xtremeforcetrackclub` | dsmith@xtremeforcetrackclub.org | ✅ Connected |
| `allensmithagent` | Outlook (personal) | 🔲 Pending |
| `nutrueapparel` | Nutrue Apparel custom domain | 🔲 Pending |
| `psibetasigma1914` | Psi Beta Sigma 1914 | 🔲 Pending |

### Web Development
| Agent | Role |
|-------|------|
| `wordpressagent` | WordPress maintenance, themes, plugins |
| `web_dev_researcher` | Site audits and prioritized fix reports |
| `wordpresspluginsagent` | Custom plugin architecture & development |

### Grant & Funding Research
| Agent | Role |
|-------|------|
| `grants_research_agent` | Weekly funding opportunity sweep (Mon 8AM CT) |
| `grant_writer_agent` | Application drafting — XFTC, Nutrue, Psi Beta Sigma |
| `yepc_grant_writer` | Capital infrastructure grants for YEPC/Smith Capital |

### YEPC Project Team (Smith Capital Properties)
| Agent | Role |
|-------|------|
| `yepc_project_manager` | Site development coordination, milestone tracking |
| `yepc_real_estate_research` | Zoning, Hutto Thoroughfare Plan, SH-130/FM 3349 tracking |
| `yepc_capital_fundraising` | EDA, HUD CDBG, TxDOT, OZ 2.0 funding pipeline |
| `yepc_government_relations` | Hutto City Council, Williamson County planning agendas |

---

## Active Sites

| Site | Status | Notes |
|------|--------|-------|
| xtremeforcetrackclub.org | ✅ Connected | REST API via dsmith app password |
| psibetasigma1914.org | ⚠️ Blocked | .htaccess Authorization header fix needed |
| nutrueapparel.com | ⚠️ Blocked | .htaccess Authorization header fix needed |
| smithcapitalproperties.com | 🔲 Pending | Credentials needed |
| staging.s2tdesigns.com | ✅ Active | XFTC plugin staging (agent_design) |

---

## XFTC Membership Plugin — Sprint Status

### Sprint 1 ✅ Complete
- Plugin scaffold, database schema (10 tables), custom user roles (5)
- Member registration, season management, base CRUD
- Deployed to staging.s2tdesigns.com

### Sprint 2 ✅ Complete — May 20, 2026
| Module | Files | Status |
|--------|-------|--------|
| Meet Management | `class-xftc-meets.php`, admin + public views | ✅ |
| Results & Records | `class-xftc-results.php`, admin + public views | ✅ |
| Travel & Logistics | `class-xftc-travel.php`, admin view | ✅ |
| Payroll System | `class-xftc-payroll.php`, admin view | ✅ |
| Stripe Payments | `class-xftc-payments.php`, checkout + receipts | ✅ (awaiting keys) |
| REST API | `class-xftc-rest-api.php` — 14 endpoints | ✅ |

**Remaining before full go-live:**
- Enter Stripe API keys in WP Admin → Xtreme Force → Payments
- Run `composer require stripe/stripe-php` on staging server
- Wire admin dashboard widgets (Sprint 3)

### Sprint 3 — Upcoming
- Admin dashboard live widgets
- Athlete portal tabs (stats, meet history, travel)
- Email notifications (class-xftc-emails.php)
- Reporting module
- Final staging QA + production deploy to xtremeforcetrackclub.org

---

## Automations

| Automation | Schedule | Purpose |
|------------|----------|---------|
| Daily Email Digest | 8:00 AM CT daily | All connected inboxes summary |
| XFTC Logger | Every 4 hours | Log new athlete signups & payments |
| Grant Research Sweep | Every Monday 8:00 AM CT | Funding opportunities for all 4 orgs |
| GitHub AgentHarness Sync | 2:00 AM CT nightly | Push agent configs to this repo |
| Sprint 2 Completion Check | Every 4 hours | Notify David when Sprint 2 is testing-ready |

---

## Organizations Managed

| Organization | Type | Focus |
|-------------|------|-------|
| Xtreme Force Track Club | 501(c)(3) nonprofit | Youth track & field, ages 6–18, Austin/Pflugerville TX |
| Smith Capital Properties | Real estate development | 110-acre YEPC site, Hutto CR 132 |
| Psi Beta Sigma 1914 | Nonprofit | Scholarships, mentorship, travel foundation |
| Nutrue Apparel | Minority-owned business | Apparel (LLC registration pending) |

---

## Key Projects

### Youth Elite Performance Complex (YEPC)
- 110-acre site at CR 132, Hutto TX (Smith Capital Properties)
- Aligned with Hutto Thoroughfare Plan, SH-130 widening (2027), FM 3349 upgrades
- Opportunity Zone 2.0 nomination deadline: **June 26, 2026**
- Funding targets: EDA, HUD CDBG, TxDOT, Williamson County EDC

### Psi Beta Sigma Travel Foundation
- 501(c)(3) foundation to subsidize collegiate conference travel
- In formation — mission statement and board recruitment phase

---

## Changelog

| Date | Change |
|------|--------|
| May 20, 2026 | Sprint 2 complete — Meets, Results, Travel, Payroll, REST API (15 files) |
| May 20, 2026 | Gmail delegated access setup — communicationsdirgcr, Sigma Signal authorized |
| May 20, 2026 | YEPC agent team initialized (5 agents) |
| May 20, 2026 | Grant Research + Grant Writer agents activated |
| May 19, 2026 | Sprint 1 complete — plugin scaffold, DB schema, roles, member registration |
| May 19, 2026 | AgentHarness repo initialized, nightly sync automation active |
| May 19, 2026 | XFTC site audit — 34 pages unpublished, 23 SEO meta descriptions deployed |
| May 19, 2026 | Multi-agent system initialized — 5 Gmail accounts, daily digest automation |
