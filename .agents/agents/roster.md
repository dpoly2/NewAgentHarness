# Agent Roster — Master Registry
**Last Updated:** 2026-05-25
**Coordinator:** AgentJames (main orchestrator — routes tasks, manages GitHub, tracks milestones)

---

## 🗂️ PROJECT INDEX

| # | Project | Lead Agent | Helper Agents | Status |
|---|---------|-----------|---------------|--------|
| 1 | XFTC Website & Plugin | xftc-project-lead | 5 specialists | 🟡 Sprint 3 |
| 2 | YEPC — Hutto CR 132 | yepc-project-manager | 6 specialists | 🟡 Pre-Dev |
| 3 | The Elevation ATX | elevation-project-lead | 5 specialists | 🟡 LLC Pending |
| 4 | PBS Foundation | pbs-project-lead | 5 specialists | 🟡 Filing Pending |
| 5 | Nutrue Apparel | nutrue-project-lead | 5 specialists | 🟡 POD Setup |
| 6 | Smith Capital Properties | smithcap-project-lead | 4 specialists | 🟡 Active |
| 7 | S2T Designs Agency | s2t-project-lead | 5 specialists + 4 helpers | 🟢 Active |
| 8 | Personal Productivity | productivity-coordinator | 8 email agents | 🟢 Active |

---

## PROJECT 1 — XFTC WEBSITE & MEMBERSHIP PLUGIN

### Lead
**xftc-project-lead** — Sprint planning, milestone tracking, client comms with XFTC board, final QA approval

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| xftc-plugin-dev | Senior PHP Developer | Plugin architecture, custom DB tables, shortcodes, WP hooks, REST API endpoints, Sprint coding |
| xftc-frontend-dev | Frontend / Theme Developer | XFTC standalone theme, CSS/JS, portal UX, Gutenberg blocks, mobile responsiveness |
| xftc-payments-agent | Payments & Billing Specialist | Stripe PHP SDK integration, payment flows, receipts, refund logic, webhook handling |
| xftc-qa-agent | QA & Testing Engineer | Staging environment testing, regression testing, staging.s2tdesigns.com, bug reporting, test scripts |
| xftc-devops-agent | DevOps & Deployment Agent | File deployment via WP REST API, GitHub version control, plugin zip packaging, staging→production promotion |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| xftc-db-schema-helper | xftc-plugin-dev | Database schema design, migration scripts, dbDelta calls |
| xftc-shortcode-helper | xftc-plugin-dev | Shortcode library, registration, output rendering |
| xftc-email-template-helper | xftc-frontend-dev | HTML email templates, wp_mail wrappers, notification formatting |
| xftc-security-helper | xftc-qa-agent | Nonce validation, capability checks, sanitization/escaping audit |
| xftc-docs-helper | xftc-project-lead | Developer docs, changelog, inline PHPDoc generation |

### Files
- `.agents/projects/xftc-redevelopment/`
- `.agents/projects/xftc-plugin-product/`
- `.agents/projects/wordpress-membership-plugin/`

---

## PROJECT 2 — YEPC (Youth Elite Performance Complex)

### Lead
**yepc-project-manager** — Master milestone tracker, cross-agency coordination, investor reporting, timeline management

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| yepc-real-estate-agent | Real Estate & Site Research | Land search, parcel due diligence, zoning analysis, title research, comp analysis |
| yepc-capital-fundraising-agent | Capital & Investor Relations | Investor pitch decks, naming rights proposals, sponsor outreach, lending pre-qualification |
| yepc-government-relations-agent | Government & Political Affairs | Hutto EDC, Williamson County, TxDOT/CAMPO monitoring, council agenda tracking, OZ nomination |
| yepc-grant-writer-agent | Capital Grants Specialist | EDA, HUD CDBG, USATF, FHWA TAP — full application writing and submission tracking |
| yepc-financial-model-agent | Financial Modeling & Pro Forma | Phase 1–3 cost projections, ROI modeling, debt service analysis, 5-yr pro forma |
| yepc-legal-agent | Legal & Entity Structure | YEPC LLC formation, partnership agreements, ground lease review, title/deed research |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| yepc-site-survey-helper | yepc-real-estate-agent | Aerial/satellite analysis, utility map research, floodplain checks |
| yepc-grant-research-helper | yepc-grant-writer-agent | Grant database sweeps, eligibility pre-screening, deadline calendar |
| yepc-sponsor-outreach-helper | yepc-capital-fundraising-agent | Corporate sponsor contact research, cold outreach drafts |
| yepc-infrastructure-helper | yepc-government-relations-agent | TxDOT project tracking, CAMPO agenda monitoring, ROW footprint research |
| yepc-pitch-deck-helper | yepc-capital-fundraising-agent | Slide content drafting, financial summary formatting, one-pager generation |

### Files
- `.agents/projects/yepc/`

---

## PROJECT 3 — THE ELEVATION ATX (Private Experience Series)

### Lead
**elevation-project-lead** — Brand vision, event calendar, LLC milestone tracker, investor deck oversight

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| elevation-brand-agent | Brand & Creative Director | Brand identity, visual language, event theme concepts, social media creative strategy |
| elevation-events-agent | Event Programming & Operations | Event format design, vendor sourcing, venue walkthroughs, production logistics |
| elevation-marketing-agent | Growth & Marketing | Waitlist funnel, TikTok/Reels strategy, email marketing, BGLO network outreach |
| elevation-funding-agent | Capital & Funding | SBA 7(a) prep, PeopleFund/LiftFund CDFI applications, angel investor outreach, pitch deck |
| elevation-legal-agent | Legal & Compliance | Texas LLC filing, TABC licensing roadmap, lease negotiation support, contracts |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| elevation-apparel-helper | elevation-marketing-agent | Printful/Shopify POD drops, product listing, collection launches on hoodswag.shop |
| elevation-waitlist-helper | elevation-marketing-agent | Landing page copy, email capture flows, theElevationATX.com content |
| elevation-financial-helper | elevation-funding-agent | Year 1 monthly P&L, event-level margin analysis, seed capital tracking |
| elevation-venue-helper | elevation-events-agent | 15119 N IH-35 site research, RCI Hospitality approach, alternative venue scouting |
| elevation-social-helper | elevation-brand-agent | Caption writing, viral script drafting, hashtag strategy, content calendar |

### Files
- `.agents/projects/rowdy-crown/` (The Elevation — formerly Rowdy Crown)

---

## PROJECT 4 — PHI BETA SIGMA COLLEGIATE PATHWAYS FOUNDATION

### Lead
**pbs-project-lead** — 501(c)(3) milestone tracker, board governance, chapter outreach coordination

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| pbs-legal-agent | Legal & Compliance | TX SOS Articles of Incorporation filing, IRS Form 1023-EZ, EIN application, bylaws finalization |
| pbs-fundraising-agent | Fundraising & Development | Grant research for travel/education, donor outreach, annual giving strategy, chapter dues model |
| pbs-communications-agent | Communications & PR | Foundation website, newsletter, social media, chapter-to-chapter outreach strategy |
| pbs-programs-agent | Program Design | Travel assistance program framework, eligibility criteria, application process, disbursement policy |
| pbs-board-agent | Board & Governance | Board recruitment, officer structure, meeting cadence, Robert's Rules compliance |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| pbs-irs-helper | pbs-legal-agent | IRS Form 1023-EZ prep, tax-exempt eligibility checklist, EIN lookup |
| pbs-grant-research-helper | pbs-fundraising-agent | Foundation and government grants for fraternity/collegiate travel programs |
| pbs-website-helper | pbs-communications-agent | Foundation website structure, content drafting, domain registration guidance |
| pbs-donor-outreach-helper | pbs-fundraising-agent | Alumni outreach templates, chapter solicitation scripts, online giving page setup |
| pbs-program-docs-helper | pbs-programs-agent | Application forms, award letter templates, disbursement tracking sheets |

### Files
- `.agents/projects/pbs-foundation/`

---

## PROJECT 5 — NUTRUE APPAREL

### Lead
**nutrue-project-lead** — Brand strategy, product roadmap, LLC formation, revenue milestone tracking

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| nutrue-ecommerce-agent | E-Commerce & Store Ops | Shopify store management, product listings, Printful integration, order fulfillment |
| nutrue-brand-agent | Brand & Creative | Visual identity, collection concepts, photography direction, lookbook creation |
| nutrue-marketing-agent | Digital Marketing | TikTok/Instagram content strategy, influencer outreach, email list building, SEO |
| nutrue-legal-agent | Legal & Business Formation | LLC registration, trademark research, supplier contracts, terms of service |
| nutrue-finance-agent | Finance & Revenue Tracking | Monthly P&L, COGS/margin analysis, tax prep coordination, reinvestment planning |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| nutrue-product-helper | nutrue-ecommerce-agent | Product description writing, mockup generation, variant setup |
| nutrue-social-helper | nutrue-marketing-agent | Caption writing, post scheduling, hashtag research, engagement tracking |
| nutrue-supplier-helper | nutrue-ecommerce-agent | Printful catalog research, blank garment sourcing, quality comparison |
| nutrue-ads-helper | nutrue-marketing-agent | Meta/TikTok ad copy, audience targeting strategy, budget allocation |
| nutrue-grant-helper | nutrue-finance-agent | Minority-owned business grants, MBDA programs, Texas Enterprise Fund eligibility |

### Files
- `.agents/projects/nutrue/`

---

## PROJECT 6 — SMITH CAPITAL PROPERTIES

### Lead
**smithcap-project-lead** — Portfolio oversight, deal pipeline management, investor relations, entity management

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| smithcap-acquisitions-agent | Acquisitions & Due Diligence | Property search, underwriting, LOI drafting, comps, LoopNet/CoStar monitoring |
| smithcap-finance-agent | Finance & Capital Markets | SBA 504/7(a), CDFI pre-qualification, pro forma, debt service modeling |
| smithcap-legal-agent | Legal & Entity Structure | LLC formation queue, operating agreements, title review, contract redlines |
| smithcap-communications-agent | Investor Relations & Comms | Deal memos, investor updates, pitch summaries, LinkedIn content, partner emails |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| smithcap-market-research-helper | smithcap-acquisitions-agent | Market data, cap rate comps, Williamson County demographic analysis |
| smithcap-zoning-helper | smithcap-acquisitions-agent | Zoning lookups, rezoning feasibility, entitlement process mapping |
| smithcap-loan-prep-helper | smithcap-finance-agent | SBA document checklist, PFS template, business plan narrative, lender identification |
| smithcap-deal-memo-helper | smithcap-communications-agent | Deal summary one-pagers, LOI drafts, investor Q&A prep |

### Files
- `.agents/projects/smithcap/`

---

## PROJECT 7 — S2T DESIGNS (Web & Graphic Design Agency)

### Lead
**s2t-project-lead** — Client intake, platform assessment, proposal writing, milestone tracking, cross-agent coordination

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| s2t-webdev-agent | Platform-Agnostic Web Developer | WordPress, Wix, Squarespace, Webflow, Weebly, Shopify — builds sites on the best platform for each client; bridges to wordpresspluginsagent for complex WP plugin builds |
| s2t-brand-designer-agent | Brand & Graphic Designer | Logos, brand kits, social media graphics, print materials, apparel graphics, event design |
| s2t-seo-agent | SEO & Performance | On-page SEO, Core Web Vitals, Google Analytics/Search Console, speed optimization, local SEO |
| s2t-maintenance-agent | Website Maintenance | Monthly WP plugin updates, security scans, backups, uptime monitoring, content edits |
| s2t-comms-agent | Client Communications | Proposals, onboarding emails, milestone updates, handoff docs, agency marketing copy |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| s2t-devops-helper | s2t-webdev-agent | DNS setup, SSL, staging→production deployment, hosting config |
| s2t-platform-assessment-helper | s2t-project-lead | Platform scoring matrix, recommendation memos, client fit analysis |
| s2t-content-helper | s2t-webdev-agent | Website copy, page content, meta descriptions, alt text, blog posts |
| s2t-client-intake-helper | s2t-project-lead | Intake questionnaire, client brief organization, discovery call prep |

### Bridge
- **wordpresspluginsagent** — Shared with XFTC project; invoked by s2t-webdev-agent for any client requiring custom PHP plugin architecture

### Staging Environment
- URL: https://staging.s2tdesigns.com (also used for XFTC development)
- Admin: https://staging.s2tdesigns.com/wp-admin
- Credentials: agent_design / yK#jR7ScYjbk#@M#8A#356dp

### Files
- `.agents/projects/s2tdesigns/`

---

## PROJECT 8 — PERSONAL PRODUCTIVITY

### Lead
**productivity-coordinator** — Daily email digest, inbox triage, calendar management, cross-account task routing

### Email Agents

| Agent | Email / Identity | Status |
|-------|-----------------|--------|
| smithdaii-agent | smithda.ii@gmail.com — Personal | ✅ Connected |
| communications-gcr-agent | communicationsdirgcr@gmail.com — Dir GCR | ✅ Connected |
| sigma-signal-agent | thesigmasignal.1stvp1914@gmail.com — The Sigma Signal | ✅ Connected |
| smithcap-email-agent | david.smith@smithcapitalproperties.com | ✅ Connected |
| xftc-email-agent | dsmith@xtremeforcetrackclub.org | ✅ Connected |
| allensmith-agent | Outlook — Personal (Allen Smith) | ⬜ Pending |
| nutrue-email-agent | Nutrue Apparel custom domain | ⬜ Pending |
| pbs-email-agent | Psi Beta Sigma 1914 custom domain | ⬜ Pending |

### Helper Agents (sub-tasks)
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| digest-formatter-helper | productivity-coordinator | Daily digest formatting, priority scoring, subject-line summarization |
| calendar-sync-helper | productivity-coordinator | Google Calendar event creation, scheduling, conflict detection |
| draft-reply-helper | All email agents | Reply drafting, tone matching, follow-up scheduling |

---

## 🤖 SHARED / CROSS-PROJECT AGENTS

| Agent | Specialty | Projects Served |
|-------|-----------|-----------------|
| grants-research-agent | Weekly funding sweep, all orgs | XFTC, YEPC, PBS, Nutrue |
| grant-writer-agent | Program-level grant applications | XFTC, PBS, Nutrue |
| github-sync-agent | AgentHarness version control, nightly push | All projects |
| wordpresspluginsagent | Custom WordPress plugin dev (XFTC-built, agency-shared) | XFTC, S2T Designs clients |
| web-dev-researcher | WordPress audits, site strategy | XFTC, Nutrue, PBS, S2T clients |

---

## ⚙️ ACTIVE AUTOMATIONS

| Automation | Schedule | Status |
|------------|----------|--------|
| Daily Email Digest | Every day 8:00 AM CT | ✅ Active |
| XFTC Signup & Payment Logger | Every 4 hours | ✅ Active |
| Weekly Monday Grant Digest | Every Monday 8:00 AM CT | ✅ Active |
| GitHub AgentHarness Nightly Sync | Nightly midnight | ✅ Active |
| Sprint 2 Completion Check | Every 4 hours | ⬜ Archive — Sprint 2 complete |

---

## 🚨 OPEN ITEMS — Needs David's Action

| Priority | Item | Project | Deadline |
|----------|------|---------|----------|
| 🔴 | Stripe API keys → WP Admin → XFTC → Payments | XFTC | ASAP |
| 🔴 | OZ 2.0 nomination decision (Hutto/Williamson County) | YEPC | June 26, 2026 |
| 🔴 | The Elevation LLC — TX SOS Certificate of Formation ($300) | Elevation | ASAP |
| 🟡 | PBS Foundation Board of Directors — finalize 3+ members | PBS | Before 1023-EZ |
| 🟡 | TX SOS + IRS EIN filing — PBS Foundation | PBS | June 2026 |
| 🟡 | Nutrue Apparel LLC registration | Nutrue | June 2026 |
| 🟡 | RCI Hospitality approach — commercial RE broker for 15119 N IH-35 | Elevation | June 2026 |
| 🟡 | S2T Designs — build agency portfolio site on staging | S2T Designs | July 2026 |
| 🟡 | S2T Designs — finalize brand kit (logo, colors, typography) | S2T Designs | July 2026 |
| 🟢 | Nutrue Apparel email SMTP/IMAP credentials | Productivity | When available |
| 🟢 | Outlook connection for allensmithagent | Productivity | When available |
| 🟢 | Psi Beta Sigma 1914 email credentials | Productivity | When available |
| 🟢 | Gravity Forms cleanup — XFTC WP Admin (deactivate 17 legacy forms) | XFTC | When available |

---

## PROJECT 9 — SMITHCAP FINANCIAL MANAGEMENT OFFICE (FMO)

### Lead
**finance-cfo** — Portfolio-wide CFO, consolidated financial oversight, capital strategy, agent coordination

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| finance-cpa | CPA | Tax compliance, entity structure, financial statements, 990 filing |
| finance-advisor | Personal Financial Advisor | Personal wealth planning, income optimization, risk management, retirement |
| finance-investment-manager | Investment Manager | Portfolio allocation, brokerage management, real estate ROI, business equity |
| finance-bookkeeper | Bookkeeper | Daily transaction recording, bank reconciliation, AR/AP, 1099s |
| finance-tax-strategist | Tax Strategist | Deduction optimization, entity tax structure, year-end moves, OZ/1031 |
| finance-analyst | Financial Analyst | Pro formas, investor decks, deal analysis, scenario modeling |
| finance-compliance | Compliance & Grant Reporting | Nonprofit 990 filing, grant spend tracking, restricted fund compliance |

### Portfolio Served
- Smith Capital Properties (RE Holding)
- YEPC — CR 132 (Development)
- The Elevation ATX (Hospitality)
- XFTC (501c3)
- PBS Foundation (501c3)
- Nutrue Apparel (POD)
- S2T Designs (Agency)

### Files
- `.agents/projects/smithcap-finance/`
- `.agents/agents/projects/smithcap-finance/`

---

## PROJECT 10 — SOLAR REPAIR COMPANY (TBD NAME)

### Lead
**solar-project-lead** — Launch planning, milestone tracking, Hert Renewables coordination, business plan execution

### Current Name
Smith and Taylor Construction → **Rebranding** (top pick: Apex Solar Services)

### Business Model
- Primary: Residential solar repair (panel, inverter, wiring, roof penetration)
- Secondary: Commercial repair via subcontract with Hert Renewables

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| solar-legal-agent | Legal & Compliance | LLC formation, TDLR licensing, Hert contract review, TX SB 1036 |
| solar-finance-agent | Finance & Insurance | GL/E&O/WC quotes, bookkeeping, Hert billing, payroll |
| solar-marketing-agent | Brand & Marketing | Name/domain, website, Google Business, local SEO, lead gen |
| solar-sales-agent | Sales & Pricing | Residential quotes, service menu, maintenance contracts |
| solar-operations-agent | Field Operations | Scheduling, crew dispatch, Hert coordination, safety, parts |

### Key Insurance Note
- Must carry multi-trade GL (electrical + roofing + structural) — NOT a standard single-trade policy
- TX SB 1036 requires GL for all solar contractors by September 1, 2026
- Primary insurance contact: The Agent's Office, Frisco TX (972-696-9995)

### Files
- `.agents/projects/solar-repair/`
- `.agents/agents/projects/solar-repair/`

---

## PROJECT 11 — S2T DESIGNS SOCIAL MEDIA DIVISION

### Lead
**social-project-lead** — Client campaign oversight, content calendar management, monthly reporting, new client onboarding

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| social-content-strategist | Content Strategist | Platform strategy, content pillars, monthly calendars, trend research, creative briefs |
| social-copywriter | Copywriter | Captions, video scripts, ad copy, hashtags, CTAs — all clients and platforms |
| social-designer | Graphic Designer | Static posts, carousels, Reels covers, Story frames, ad creatives, brand templates |
| social-analyst | Performance Analyst | KPI tracking, monthly client reports, optimization recommendations, benchmarking |
| social-ads-manager | Paid Ads Manager | Meta, TikTok, YouTube paid campaigns — targeting, budgets, A/B testing, ROAS tracking |
| social-community-manager | Community Manager | Daily comment/DM engagement, Google Business reviews, escalation handling, sentiment tracking |
| social-video-designer | Graphic Designer & Video Producer | Short-form video (Reels/TikTok/YT Shorts), motion graphics, branded video templates, event recaps, thumbnails — cross-client |

### Active Clients
| Client | Status |
|--------|--------|
| S2T Designs (internal brand) | 🟡 Setup |
| Little Ebenezer Baptist Church | 🟡 Pending discovery |
| Xtreme Force Track Club | 🟡 Pending scope |
| Clarity Solar Services | 🟡 Pending brand launch |

### Files
- `.agents/agents/projects/social-media/`
- `.agents/projects/social-media/PROJECT.md`

---

## PROJECT 12 — MINISTRY & PREACHING TEAM

### Lead
**ministry-project-lead** — Content calendar, sermon series tracking, team coordination, SoulSpeak alignment review

### Specialist Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| ministry-sermon-writer | Sermon Manuscript Developer | Full sermon manuscripts in Expository SoulSpeak format — 3-stage arc, delivery markup, cadence and pause indicators |
| ministry-bible-study | Bible Study Developer | Weekly Bible study lessons, discussion guides, devotionals — all levels |
| ministry-sunday-school | Sunday School Curriculum | Age-grouped lessons: Little Lights (4–8), Junior (9–12), Youth (13–18), Young Adult (19–25), Adult (26+) |
| ministry-delivery-coach | Preaching Delivery Coach | 30-Day SoulSpeak Training Program — drills, feedback, pre-sermon checklists, self-grading rubrics |
| ministry-research-agent | Biblical Research | Scripture context, original language study, commentary synthesis, sermon illustrations |

### Preaching Style
**Expository SoulSpeak** — Rooted in biblical exposition, shaped by personal testimony, structured for musical cadence, built for emotional movement.

**The 6 P's:** Presence · Pace · Power · Pause · Passion · Precision

**The 3-Stage Arc:** Explain (text) → Feel (testimony) → Release (declaration)

**The SoulSpeak Formula:** Teach it clearly. Feel it honestly. Deliver it musically. End it powerfully.

### Personal Testimony Bank
- Running from the call in 1997 — returning in 2001 through Sister Valerie
- "But God brought me through." — core testimony phrase
- "There is fire in me." — "I'm On Fire" active sermon series

### Files
- `.agents/projects/ministry/`
- `.agents/agents/projects/ministry/`
