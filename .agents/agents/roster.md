# Agent Roster — Master Registry
**Last Updated:** 2026-05-28
**Coordinator:** AgentJames (main orchestrator — routes tasks, manages GitHub, tracks milestones)

---

## 🗂️ PROJECT INDEX

| # | Project | Lead Agent | Specialists | Status |
|---|---------|-----------|-------------|--------|
| 1 | XFTC Website & Plugin | xftc-project-lead | 5 specialists + 5 helpers | 🟡 Sprint 3 |
| 2 | YEPC — Hutto CR 132 | yepc-project-manager | 6 specialists + 5 helpers | 🟡 Pre-Dev |
| 3 | The Elevation ATX | elevation-project-lead | 5 specialists + 5 helpers | 🟡 LLC Pending |
| 4 | PBS Foundation | pbs-project-lead | 5 specialists + 5 helpers | 🟡 Filing Pending |
| 5 | Nutrue Apparel | nutrue-project-lead | 5 specialists + 5 helpers | 🟡 POD Setup |
| 6 | Smith Capital Properties | smithcap-project-lead | 4 specialists | 🟡 Reactivation Needed |
| 7 | S2T Designs Agency | s2t-project-lead | 5 specialists + 4 helpers | 🟢 Active |
| 8 | Personal Productivity | productivity-coordinator | 5 email identities | 🟢 Active |
| 9 | SmithCap FMO | finance-project-lead | 7 specialists | 🟢 Active |
| 10 | Clarity Solar Services | solar-project-lead | 5 specialists | 🟡 Pre-Launch |
| 11 | S2T Social Media Division | social-project-lead | 7 specialists | 🟢 Active |
| 12 | Ministry & Preaching Team | ministry-project-lead | 4 specialists | 🟢 Active |
| 13 | The Sigma Signal | sigma-signal-project-lead | 6 specialists | 🟢 Active |
| 14 | Travel Division | travel-project-lead | 4 specialists + 1 helper | 🟢 Active |
| 15 | Business Structure & Holdings | holdings-project-lead | 5 specialists | 🔴 Formation Pending |

---

## 🌐 CLIENT & SITE REGISTRY

> All active client websites and digital properties — linked to their managing team and lead agent.

| Client / Property | URL | Platform | Managing Team | Lead Agent | Status |
|-------------------|-----|----------|---------------|------------|--------|
| Xtreme Force Track Club | xtremeforcetrackclub.org | WordPress | Project 1 — XFTC | xftc-project-lead | 🟡 Sprint 3 |
| XFTC Staging | staging.s2tdesigns.com | WordPress | Project 1 — XFTC | xftc-devops-agent | 🟡 Active Dev |
| Psi Beta Sigma 1914 | newsite.psibetasigma1914.org | WordPress (Kadence) | Project 7 — S2T Designs | s2t-project-lead | 🟡 Pre-Launch |
| Little Ebenezer Baptist Church | littleebenezerbaptistchurch.com | WordPress (Kadence — rebuild) | Project 7 — S2T Designs | s2t-project-lead | 🟡 Discovery |
| LEBC Social Media | FB / YouTube / Instagram | Multi-platform | Project 11 — Social Media | social-project-lead | 🟡 Active |
| Nutrue Apparel | nutrueapparel.com | WordPress / Printful | Project 5 — Nutrue | nutrue-project-lead | 🟡 POD Setup |
| Smith Capital Properties | smithcapitalproperties.com | WordPress | Project 6 — SmithCap | smithcap-project-lead | ⬜ Pending |
| S2T Designs Agency | s2tdesigns.com | WordPress | Project 7 — S2T Designs | s2t-project-lead | ⬜ To Build |
| The Sigma Signal | (email / Constant Contact) | Email newsletter | Project 13 — Sigma Signal | sigma-signal-project-lead | 🟢 Active |
| The Elevation ATX | theElevationATX.com | Landing page (TBD) | Project 3 — Elevation | elevation-project-lead | ⬜ To Build |

### WordPress Credentials Quick Reference
| Site | URL | WP Username | Auth Method |
|------|-----|-------------|-------------|
| XFTC Live | xtremeforcetrackclub.org | dsmith | App Password (stored in .env) |
| XFTC Staging | staging.s2tdesigns.com | agent_design | App Password (stored in .env) |
| Nutrue Apparel | nutrueapparel.com | nutrue_admin | Password (stored in .env) |
| PBS / S2T Staging | newsite.psibetasigma1914.org | s2tdesignadmin | App Password (needed — pending) |

---

## 🤝 CLIENT ACCOUNT ASSIGNMENTS

### Psi Beta Sigma 1914 — newsite.psibetasigma1914.org
- **Managing Lead:** s2t-project-lead
- **Web Dev:** s2t-webdev-agent
- **Design:** s2t-brand-designer-agent
- **Communications:** pbs-communications-agent (cross-project)
- **Newsletter:** sigma-signal-project-lead (The Sigma Signal)
- **Social:** social-project-lead (Project 11)
- **Key Contact:** David Smith (owner/webmaster)
- **Pending:** WordPress App Password for s2tdesignadmin to deploy CSS changes + verify payment gateway
- **Files:** `.agents/projects/s2tdesigns/clients/pbs/`

### Little Ebenezer Baptist Church — littleebenezerbaptistchurch.com
- **Managing Lead:** s2t-project-lead
- **Web Dev:** s2t-webdev-agent
- **Design:** s2t-brand-designer-agent
- **Social Media:** social-project-lead (Project 11)
- **Social Strategy:** social-content-strategist + social-ads-manager
- **Video:** social-video-designer
- **Key Contact:** Rev. Arthur L. Spence (Pastor) + LaShell M. Spence (First Lady)
- **Current Site Status:** D+ — 2 of 3 nav pages broken (AccessDenied), outdated content, no CTA
- **Platform:** Migrate from current static host → WordPress (Kadence)
- **Pending:** Discovery meeting with Pastor Spence, photography, online giving decision
- **Files:** `.agents/projects/s2tdesigns/clients/lebc/`

### Xtreme Force Track Club — xtremeforcetrackclub.org
- **Managing Lead:** xftc-project-lead
- **Plugin Dev:** xftc-plugin-dev
- **Frontend Dev:** xftc-frontend-dev
- **Payments:** xftc-payments-agent
- **QA:** xftc-qa-agent
- **DevOps:** xftc-devops-agent
- **Key Contact:** David Smith (owner/operator)
- **Current Status:** Sprint 3 — Dashboard widgets, Coach portal, Stripe live key integration
- **Blocker:** Stripe API keys, SFTP credentials for staging deployment
- **Files:** `.agents/projects/xftc-redevelopment/`

---

## PROJECT 1 — XFTC WEBSITE & MEMBERSHIP PLUGIN

### Lead
**xftc-project-lead** — Sprint planning, milestone tracking, client comms with XFTC board, final QA approval

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| xftc-plugin-dev | Senior PHP Developer | Plugin architecture, custom DB tables, shortcodes, WP hooks, REST API endpoints |
| xftc-frontend-dev | Frontend / Theme Developer | XFTC standalone theme, CSS/JS, portal UX, Gutenberg blocks, mobile responsiveness |
| xftc-payments-agent | Payments & Billing Specialist | Stripe PHP SDK integration, payment flows, receipts, refund logic, webhook handling |
| xftc-qa-agent | QA & Testing Engineer | Staging environment testing, regression testing, staging.s2tdesigns.com, bug reporting |
| xftc-devops-agent | DevOps & Deployment Agent | File deployment, GitHub version control, plugin zip packaging, staging→production |

### Helper Agents
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| xftc-db-schema-helper | xftc-plugin-dev | Database schema design, migration scripts, dbDelta calls |
| xftc-shortcode-helper | xftc-plugin-dev | Shortcode library, registration, output rendering |
| xftc-email-template-helper | xftc-frontend-dev | HTML email templates, wp_mail wrappers, notification formatting |
| xftc-security-helper | xftc-qa-agent | Nonce validation, capability checks, sanitization/escaping audit |
| xftc-docs-helper | xftc-project-lead | Developer docs, changelog, inline PHPDoc generation |

### Sites
| Site | URL | User | Notes |
|------|-----|------|-------|
| Live | xtremeforcetrackclub.org | dsmith | Production — credentials in .env |
| Staging | staging.s2tdesigns.com | agent_design | Active dev — credentials in .env |

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
| yepc-government-relations-agent | Government & Political Affairs | Hutto EDC, Williamson County, TxDOT/CAMPO monitoring, council agenda tracking |
| yepc-grant-writer-agent | Capital Grants Specialist | EDA, HUD CDBG, USATF, FHWA TAP — full application writing and submission tracking |
| yepc-financial-model-agent | Financial Modeling & Pro Forma | Phase 1–3 cost projections, ROI modeling, debt service analysis, 5-yr pro forma |
| yepc-legal-agent | Legal & Entity Structure | YEPC LLC formation, partnership agreements, ground lease review, title/deed research |

### Helper Agents
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

## PROJECT 3 — THE ELEVATION ATX

### Lead
**elevation-project-lead** — Brand vision, event calendar, LLC milestone tracker, investor deck oversight

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| elevation-brand-agent | Brand & Creative Director | Brand identity, visual language, event theme concepts, social media creative strategy |
| elevation-events-agent | Event Programming & Operations | Event format design, vendor sourcing, venue walkthroughs, production logistics |
| elevation-marketing-agent | Growth & Marketing | Waitlist funnel, TikTok/Reels strategy, email marketing, BGLO network outreach |
| elevation-funding-agent | Capital & Funding | SBA 7(a) prep, PeopleFund/LiftFund CDFI applications, angel investor outreach |
| elevation-legal-agent | Legal & Compliance | Texas LLC filing, TABC licensing roadmap, lease negotiation support, contracts |

### Helper Agents
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
| pbs-legal-agent | Legal & Compliance | TX SOS Articles of Incorporation filing, IRS Form 1023-EZ, EIN application, bylaws |
| pbs-fundraising-agent | Fundraising & Development | Grant research for travel/education, donor outreach, annual giving strategy |
| pbs-communications-agent | Communications & PR | Foundation website, newsletter, social media, chapter-to-chapter outreach |
| pbs-programs-agent | Program Design | Travel assistance program framework, eligibility criteria, disbursement policy |
| pbs-board-agent | Board & Governance | Board recruitment, officer structure, meeting cadence, Robert's Rules compliance |

### Helper Agents
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
| nutrue-ecommerce-agent | E-Commerce & Store Ops | WordPress/Shopify store management, product listings, Printful integration |
| nutrue-brand-agent | Brand & Creative | Visual identity, collection concepts, photography direction, lookbook creation |
| nutrue-marketing-agent | Digital Marketing | TikTok/Instagram content strategy, influencer outreach, email list building, SEO |
| nutrue-legal-agent | Legal & Business Formation | LLC registration, trademark research, supplier contracts, terms of service |
| nutrue-finance-agent | Finance & Revenue Tracking | Monthly P&L, COGS/margin analysis, tax prep coordination, reinvestment planning |

### Helper Agents
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| nutrue-product-helper | nutrue-ecommerce-agent | Product description writing, mockup generation, variant setup |
| nutrue-social-helper | nutrue-marketing-agent | Caption writing, post scheduling, hashtag research, engagement tracking |
| nutrue-supplier-helper | nutrue-ecommerce-agent | Printful catalog research, blank garment sourcing, quality comparison |
| nutrue-ads-helper | nutrue-marketing-agent | Meta/TikTok ad copy, audience targeting strategy, budget allocation |
| nutrue-grant-helper | nutrue-finance-agent | Minority-owned business grants, MBDA programs, Texas Enterprise Fund eligibility |

### Sites
| Site | URL | User | Notes |
|------|-----|------|-------|
| Live | nutrueapparel.com | nutrue_admin | Namecheap/Bosnacweb hosting — .htaccess fix required |

### Files
- `.agents/projects/nutrue/`

---

## PROJECT 6 — SMITH CAPITAL PROPERTIES

### Lead
**smithcap-project-lead** — Portfolio oversight, deal pipeline management, entity compliance, investor relations

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| smithcap-acquisitions-agent | Acquisitions & Deal Flow | Property sourcing, LOI drafting, due diligence coordination, deal pipeline tracking |
| smithcap-communications-agent | Communications & Investor Relations | Investor updates, partner communications, brand presence |
| smithcap-finance-agent | Finance & Capital | Capital stack analysis, debt/equity modeling, lender relationships |
| smithcap-legal-agent | Legal & Compliance | Entity maintenance, contract review, TX SOS/Comptroller filings |

### 🚨 Current Blocker
**Smith Capital Properties LLC is INACTIVE** — missed TX franchise tax / PIR filings.
- Step 1: File past-due reports at comptroller.texas.gov/taxes/franchise
- Step 2: Pay penalties (minimum $50, 5%/month on any tax owed)
- Step 3: File Certificate of Reinstatement (Form 811, $75) with TX SOS
- Step 4: Obtain new Certificate of Good Standing

### Files
- `.agents/projects/smithcap/`
- `.agents/projects/smithcap-finance/`

---

## PROJECT 7 — S2T DESIGNS AGENCY

### Lead
**s2t-project-lead** — Client intake, project scoping, deliverable oversight, billing, agency brand

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| s2t-webdev-agent | Web Developer | WordPress builds, theme customization, plugin installation, DNS/hosting setup |
| s2t-brand-designer-agent | Brand Designer | Logo, color palette, typography, brand guides, mockups |
| s2t-seo-agent | SEO Specialist | On-page SEO, Google Business Profile, local search optimization |
| s2t-maintenance-agent | Site Maintenance | Plugin updates, backups, uptime monitoring, security patches |
| s2t-comms-agent | Client Communications | Onboarding emails, status updates, invoicing, discovery questionnaires |

### Helper Agents
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| s2t-client-intake-helper | s2t-project-lead | New client intake forms, discovery questionnaire delivery |
| s2t-content-helper | s2t-webdev-agent | Page copywriting, bio drafting, placeholder content |
| s2t-devops-helper | s2t-webdev-agent | Staging → production deployments, DNS changes, SSL setup |
| s2t-platform-assessment-helper | s2t-project-lead | Existing site audits, platform migration recommendations |

### Active Clients
| Client | Site | Lead Agent | Status | Key Contact |
|--------|------|------------|--------|-------------|
| Psi Beta Sigma 1914 | newsite.psibetasigma1914.org | s2t-project-lead | 🟡 Pre-Launch | David Smith (webmaster) |
| Little Ebenezer Baptist Church | littleebenezerbaptistchurch.com | s2t-project-lead | 🟡 Discovery | Rev. Arthur L. Spence |
| Xtreme Force Track Club | xtremeforcetrackclub.org | xftc-project-lead | 🟡 Sprint 3 | David Smith (owner) |

### Files
- `.agents/projects/s2tdesigns/`
- `.agents/projects/s2tdesigns/clients/lebc/`
- `.agents/projects/s2tdesigns/clients/pbs/`

---

## PROJECT 8 — PERSONAL PRODUCTIVITY

### Lead
**productivity-coordinator** — Daily email digest, inbox triage, task routing, calendar monitoring

### Email Identity Accounts
| Account | Identity | Primary Use |
|---------|----------|-------------|
| smithda.ii@gmail.com | Personal | Daily triage, primary connector account |
| communicationsdirgcr@gmail.com | Communications Director GCR | Org communications, announcements |
| thesigmasignal.1stvp1914@gmail.com | The Sigma Signal | Newsletter coordination, submissions |
| david.smith@smithcapitalproperties.com | Smith Capital Properties | Property inquiries, deal flow |
| dsmith@xtremeforcetrackclub.org | Xtreme Force Track Club | Member comms, registration, payments |
| davidallensmith77@outlook.com | Personal Outlook | Sigma Signal historical data |

### Active Automations
| Automation | Schedule | Status |
|------------|----------|--------|
| Daily Email Digest | 8:00 AM CT daily | 🟢 Active |
| XFTC Athlete Signup & Payment Logger | Real-time (Gmail connector) | 🔴 Token Invalid — needs re-auth |
| Weekly Monday Grant Digest | 8:00 AM CT Monday | 🟢 Active |
| Sigma Signal Daily Submission Check | 2:00 PM CT daily | 🟢 Active |
| Weekly Travel Fare Alert | 8:30 AM CT Monday | 🟢 Active |

### Files
- `.agents/agents/agent_profiles.md`

---

## PROJECT 9 — SMITHCAP FINANCIAL MANAGEMENT OFFICE (FMO)

### Lead
**finance-project-lead** (CFO) — Cross-entity financial oversight, tax strategy, capital allocation

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| finance-cpa | CPA / Tax | Tax filings, quarterly estimates, entity returns, W-2 reconciliation |
| finance-advisor | Financial Advisor | Investment planning, retirement strategy, wealth building |
| finance-investment-manager | Investment Manager | RSU tracking, 401(k) optimization, brokerage strategy |
| finance-bookkeeper | Bookkeeper | Transaction categorization, monthly reconciliation, expense tracking |
| finance-tax-strategist | Tax Strategist | Cross-entity tax planning, deduction strategy, SE tax management |
| finance-analyst | Financial Analyst | KPI dashboards, pro forma modeling, variance analysis |
| finance-compliance | Compliance Officer | Entity filings, franchise tax, registered agent, annual reports |

### Key Numbers (2026)
| Item | Value |
|------|-------|
| HP Base Salary | $150,743.10 |
| 2025 Gross Income | $166,403.31 |
| 401(k) Max (2026) | $23,500 |
| TX State Income Tax | $0 (Texas) |
| Smith Capital LLC | ⚠️ INACTIVE — reactivate immediately |

### Files
- `.agents/projects/smithcap-finance/`

---

## PROJECT 10 — CLARITY SOLAR SERVICES

### Lead
**solar-project-lead** — Business formation, licensing, client acquisition, Hert subcontract

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| solar-legal-agent | Legal & Licensing | TX SB 1036 compliance, contractor license, LLC formation, insurance |
| solar-finance-agent | Finance | Startup cost modeling, SBA loan prep, Hert subcontract revenue projection |
| solar-marketing-agent | Marketing | Brand launch, Google LSA ads, Nextdoor/HOA outreach, referral program |
| solar-sales-agent | Sales | Lead intake, quote process, CRM setup, closing scripts |
| solar-operations-agent | Operations | Job scheduling, vendor sourcing, equipment procurement, crew management |

### Key Info
- **Domain:** claritysolarservices.com (register ASAP)
- **Tagline:** "Clear Skies. Clear Results."
- **Critical Deadline:** TX SB 1036 multi-trade GL insurance required by Sep 1, 2026
- **Insurance Contact:** The Agent's Office, Frisco TX — 972-696-9995

### Files
- `.agents/projects/solar-repair/`

---

## PROJECT 11 — S2T SOCIAL MEDIA DIVISION

### Lead
**social-project-lead** — Content calendar oversight, platform strategy, client reporting

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| social-content-strategist | Content Strategist | Platform strategy, content pillars, audience targeting, editorial calendar |
| social-copywriter | Copywriter | Captions, scripts, CTAs, bio copy, ad copy across all platforms |
| social-designer | Graphic Designer | Static posts, carousels, story templates, branded visuals |
| social-analyst | Analytics | Engagement tracking, growth metrics, ad performance reporting |
| social-ads-manager | Paid Ads Manager | Meta/Facebook Ads, Google Ads setup, budget allocation, A/B testing |
| social-community-manager | Community Manager | Comment replies, DM management, community engagement, reputation |
| social-video-designer | Video Designer | Reels, TikTok, YouTube Shorts — cinematic and cross-entity video production |

### Active Client Accounts
| Client | Platforms | Lead | Priority |
|--------|-----------|------|----------|
| Little Ebenezer Baptist Church | Facebook, YouTube, Instagram | social-project-lead | 🔴 Google Business Profile + Facebook Ads |
| Psi Beta Sigma 1914 | Facebook, Instagram | social-project-lead | 🟡 Growth |
| Xtreme Force Track Club | Facebook, Instagram | social-project-lead | 🟡 Seasonal |
| The Sigma Signal | Email / Social teaser | sigma-signal-project-lead | 🟢 Active |

### Files
- `.agents/projects/social-media/`

---

## PROJECT 12 — MINISTRY & PREACHING TEAM

### Lead
**ministry-project-lead** — Sermon calendar, content coordination, delivery coaching oversight

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| ministry-sermon-writer | Sermon Writer | Full expository manuscripts, Greek/Hebrew word studies, 3-point structure |
| ministry-bible-study | Bible Study Leader | Midweek study guides, discussion questions, commentary research |
| ministry-sunday-school | Sunday School | Age-differentiated lesson plans for youth tracks |
| ministry-delivery-coach | Delivery Coach | Cadence ladder coaching, pulpit technique, vocal pacing, manuscript prep |

### Methodology
- **Style:** Expository SoulSpeak — scholarly depth with pastoral warmth
- **Structure:** 3-point expository, Greek/Hebrew word studies, Cadence Ladder
- **Prompt library:** `.agents/projects/ministry/PROMPT-TEMPLATES.md`

### Files
- `.agents/projects/ministry/`
- `.agents/projects/ministry/sermons/`
- `.agents/projects/ministry/STYLE-GUIDE.md`

---

## PROJECT 13 — THE SIGMA SIGNAL

### Lead
**sigma-signal-project-lead** — Editorial calendar, issue production, team coordination, submission intake

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| sigma-signal-writer | Lead Writer | Feature articles, chapter spotlights, member profiles, news recap |
| sigma-signal-designer | Layout Designer | Issue layout, header graphics, section formatting |
| sigma-signal-researcher | Researcher | History KB, fraternity news, national Sigma updates |
| sigma-signal-historian | Historian | Crescent Archive content, Sigma heritage features, historical trivia |
| sigma-signal-poet | Poet / Creative | Ode to Sigma section, creative writing, inspirational content |
| sigma-signal-submissions | Submissions Manager | Google Form intake, member submission triage, follow-up |

### Key Info
| Item | Detail |
|------|--------|
| Cadence | 2nd & 4th Thursday monthly |
| Platform | Constant Contact |
| Submission Email | thesigmasignal.1stvp1914@gmail.com |
| Google Form | Active — member content submissions |
| Primary Source | davidallensmith77@outlook.com (historical archive) |

### Files
- `.agents/projects/sigma-signal/`

---

## PROJECT 14 — TRAVEL DIVISION

### Lead
**travel-project-lead** — Trip orchestration, itinerary planning, budget tracking, booking coordination

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| travel-flights-agent | Flights Specialist | Fare comparison across Google Flights, Kayak, Skyscanner, Southwest direct |
| travel-hotel-agent | Lodging Specialist | Hotel/Airbnb search, loyalty program optimization, free cancellation preference |
| travel-ground-agent | Ground Transport | Car rental vs. rideshare analysis, AUS parking, local transit |
| travel-experience-agent | Experience & Itinerary | Activities, dining, day-by-day itinerary, local intel |

### Helper Agents
| Agent | Assigned By | Task Type |
|-------|-------------|-----------|
| travel-budget-helper | travel-project-lead | Trip cost rollup, budget tracking, low/mid/high scenarios |

### Standing Preferences
- Home airport: AUS · Prefers nonstop (if delta < $150) · Carry-on only · Aisle seat

### Active Trips
| Trip | Dates | Status |
|------|-------|--------|
| AUS → ATL | Jun 2–7, 2026 | 🟡 Flight researched — hotel pending |

### Files
- `.agents/projects/travel/`
- `.agents/projects/travel/trips/`

---

---

## PROJECT 15 — BUSINESS STRUCTURE & HOLDINGS

### Lead
**holdings-project-lead** — Entity architecture design, formation queue, legal/tax/finance/compliance coordination

### Specialist Agents
| Agent | Role | Responsibilities |
|-------|------|-----------------|
| holdings-legal-agent | Legal & Entity Formation | TX LLC formations, operating agreements, TX SOS filings, nonprofit firewall |
| holdings-tax-agent | Tax Strategy & Entity Elections | S-Corp elections, SE tax optimization, inter-entity distributions, QBI planning |
| holdings-finance-agent | Finance & Capital Flows | Banking structure, management fee schedule, inter-entity loans, investor readiness |
| holdings-compliance-agent | Compliance & Annual Filings | PIR/franchise tax calendar, license renewals, Smith Capital LLC reactivation |
| holdings-investor-agent | Investor Relations & Capital Readiness | Cap table, CDFI pipeline, investor decks, SBA pre-qualification |

### Entity Scope
| Entity | Type | Priority |
|--------|------|---------|
| Smith Capital Holdings LLC | TX LLC (new) | 🔴 Form first |
| S2T Designs LLC | TX LLC (new) | 🔴 Immediate |
| The Elevation ATX LLC | TX LLC (new) | 🔴 ASAP |
| Nutrue Apparel LLC | TX LLC (new) | 🔴 ASAP |
| Smith Capital Properties LLC | TX LLC (reactivate) | 🟡 Week 3 |
| Clarity Solar Services LLC | TX LLC (new) | 🟡 Q3 2026 |
| YEPC Development LLC | TX LLC (new) | 🟡 Pre-acquisition |
| XFTC 501(c)(3) | Nonprofit — independent | ✅ Active |
| PBS Foundation 501(c)(3) | Nonprofit — independent | 🟡 Filing pending |

### Files
- `.agents/projects/holdings/MASTER-STRUCTURE.md`
- `.agents/agents/projects/holdings/`


## 🤖 SHARED / CROSS-PROJECT AGENTS

| Agent | Specialty | Projects Served |
|-------|-----------|----------------|
| grants-research-agent | Grant database sweeps, eligibility screening | XFTC, PBS Foundation, YEPC, Nutrue |
| grant-writer-agent | Formal grant applications, narrative writing | XFTC, PBS Foundation, Nutrue |
| yepc-grant-writer-agent | Large-scale capital infrastructure grants | YEPC |
| web-dev-researcher | Platform research, plugin evaluation, tech stack advisory | S2T, XFTC, Nutrue |
| wordpresspluginsagent | WordPress plugin management, updates, compatibility | All WP sites |

---

## ⚙️ ACTIVE AUTOMATIONS

| Automation | Schedule | Status |
|------------|----------|--------|
| Daily Email Digest | 8:00 AM CT daily | 🟢 Active |
| XFTC Athlete Signup & Payment Logger | Real-time Gmail connector | 🔴 Needs re-auth |
| Weekly Monday Grant Digest | 8:00 AM CT Monday | 🟢 Active |
| Sigma Signal Daily Submission Check | 2:00 PM CT daily | 🟢 Active |
| Sigma Signal Newsletter Production Reminder | 9:00 AM UTC Thursdays | 🟢 Active |
| YEPC Hutto EDC Monitor | Weekly | 🟢 Active |
| Weekly Travel Fare Alert | 8:30 AM CT Monday | 🟢 Active |

---

## 🚨 OPEN ITEMS / BLOCKERS

| Priority | Item | Project | Deadline |
|----------|------|---------|----------|
| 🔴 | Form Smith Capital Holdings LLC — anchors entire business structure | Project 15 | ASAP |
| 🔴 | Form S2T Designs LLC + The Elevation LLC + Nutrue LLC ($900 total TX SOS) | Project 15 | Week 1 |
| 🔴 | Smith Capital Properties LLC INACTIVE — file TX Comptroller + Form 811 | Project 6 | ASAP |
| 🔴 | XFTC Gmail connector token invalid — re-authorize OAuth | Project 8 | ASAP |
| 🔴 | PBS 1914 Golf Tournament payment gateway needed | Project 13 / S2T | June 1, 2026 |
| 🔴 | PBS site DNS migration still pending | S2T / Project 7 | ASAP |
| 🔴 | s2tdesignadmin WordPress App Password needed for PBS site CSS deploy | S2T | ASAP |
| 🟡 | AUS → ATL Jun 2 flight — book Southwest $649 before price rises | Travel | ASAP |
| 🟡 | XFTC staging deployment blocked — SFTP credentials needed | Project 1 | Sprint 3 |
| 🟡 | Stripe live keys needed for XFTC Sprint 3 | Project 1 | Sprint 3 |
| 🟡 | Clarity Solar Services domain registration (claritysolarservices.com) | Project 10 | ASAP |
| 🟡 | The Elevation LLC filing with TX SOS ($300) | Project 3 | ASAP |
| 🟡 | LEBC discovery meeting with Pastor Spence needed | S2T / Project 7 | TBD |
| 🟡 | 401(k) contribution increase to $23,500 max via HP Workday | Personal Finance | ASAP |
| 🟢 | Update AgentHarness generic build prompt on GitHub | Project 14 | Done ✅ |
