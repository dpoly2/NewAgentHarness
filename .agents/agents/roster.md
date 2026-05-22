# Agent Roster
**Last Updated:** 2026-05-21

## Coordinator
- **AgentJames (main agent):** Routes tasks, manages GitHub sync, tracks all project milestones

---

## Personal Productivity Agents

| Agent Name             | Email Provider     | Primary Domain / Identity       | Status     |
|------------------------|--------------------|---------------------------------|------------|
| allensmithagent        | Outlook            | Personal (Allen Smith)          | Pending    |
| smithdaiiagent         | Gmail              | Personal (Smith Daily)          | Connected  |
| communicationsdirgcr   | Gmail              | Communications / Dir GCR        | Connected  |
| thesigmasignal         | Gmail              | The Sigma Signal                | Connected  |
| nutrueapparel          | Custom Domain      | Nutrue Apparel                  | Pending    |
| smithcapitalproperties | Gmail              | Smith Capital Properties        | Connected  |
| psibetasigma1914       | Custom (→ Gmail?)  | Psi Beta Sigma 1914             | Pending    |
| xtremeforcetrackclub   | Gmail              | Xtreme Force Track Club         | Connected  |

---

## Web Development Agents

| Agent Name              | Specialty                              | Status  |
|-------------------------|----------------------------------------|---------|
| wordpressagent          | WordPress site management, XFTC live site | Active  |
| wordpresspluginsagent   | Custom plugin development (XFTC membership plugin) | Active  |
| researchagent           | Site audits & strategy reports         | Active  |

---

## Research & Funding Agents

| Agent Name          | Specialty                                      | Status  |
|---------------------|------------------------------------------------|---------|
| grantsresearchagent | Grant discovery, funding opps, revenue ideas   | Active  |
| grantwriteragent    | Program-level grant application writing        | Active  |

---

## YEPC — Youth Elite Performance Complex Agents

| Agent Name                    | Specialty                                              | Status  |
|-------------------------------|--------------------------------------------------------|---------|
| yepcrprojectmanageragent      | Master project tracker, milestone management           | Active  |
| yepcrealestateresearchagent   | Zoning, permitting, EDC incentives, TxDOT/CAMPO        | Active  |
| yepccapitalfundraisingagent   | Investor decks, naming rights, sponsorships, lending   | Active  |
| yepcgovernmentrelationsagent  | City/county meetings, TxDOT, CAMPO monitoring          | Active  |
| yepcgrantwriteragent          | Capital project grant applications (EDA, HUD, etc.)   | Active  |

---

## The Elevation ATX Agents

| Agent Name                      | Specialty                                                | Status  |
|---------------------------------|----------------------------------------------------------|---------|
| rowdycrownresearchagent         | Site due diligence, market analysis, competitive intel   | Active  |
| rowdycrownpromoterconcept       | Brand identity, event programming, marketing strategy    | Active  |
| rowdycrownbusinessplanagent     | Financial model, pro forma, pitch deck, business plan    | Active  |
| rowdycrownfundingagent          | Grants, SBA loans, CDFIs, angel investors, brand partners| Active  |
| rowdycrownlegalcomplianceagent  | LLC formation, TABC licensing, permits, lease review     | Active  |

---

## Active Automations

| Automation                        | Schedule                   | Status  |
|-----------------------------------|----------------------------|---------|
| Daily Email Digest                | Every day at 8:00 AM CT    | ✅ Active |
| XFTC Signup & Payment Logger      | Every 4 hours              | ✅ Active |
| Weekly Monday Grant Digest        | Every Monday at 8:00 AM CT | ✅ Active |
| GitHub AgentHarness Sync          | Nightly                    | ✅ Active |
| Sprint 2 Completion Check         | Every 4 hours (temp)       | ✅ Active — Sprint 2 COMPLETE, can archive |

---

## Project Status Summary — May 21, 2026

### XFTC Membership Plugin
| Sprint | Status |
|--------|--------|
| Sprint 1 — Core scaffold, DB, user roles | ✅ Complete |
| Sprint 2 — Meets, Results, Travel, Payroll, Stripe stub | ✅ Complete + Staging Verified |
| Sprint 3 — Dashboard widgets, Coach portal, Stripe live | 🔄 In Progress |

**Blockers:**
- Stripe API keys needed (publishable + secret) → enter in WP Admin → Xtreme Force → Payments
- Composer needed on staging to install Stripe PHP SDK

### The Elevation ATX
| Deliverable | Status |
|------------|--------|
| Project master file | ✅ Complete |
| Executive proposal | ✅ Complete |
| Brand concept bible | ✅ Complete |
| Research report (site + market + TABC + SBA) | ✅ Complete — May 21 |
| Financial model (Year 1 monthly + 5-yr) | ✅ Complete — May 21 |
| Legal & compliance tracker | ✅ Complete — May 21 |
| Funding tracker | ✅ Complete — May 21 |
| Agent team (5 agents) | ✅ Active |
| The Elevation LLC — entity formation | ⬜ Not started — file next |
| Site acquisition approach (RCI Hospitality) | ⬜ Not started |
| Pitch deck | ⬜ Not started |

### YEPC — Hutto CR 132
| Milestone | Status |
|-----------|--------|
| Site analysis complete | ✅ Complete |
| Agent team initialized | ✅ Active (5 agents) |
| Weekly grant digest includes YEPC | ✅ Active |
| Hutto EDC outreach drafted | ✅ Drafted — May 25 reminder set |
| OZ 2.0 nomination research | ✅ Researched — deadline June 26, 2026 |

### Phi Beta Sigma Collegiate Pathways Foundation
| Milestone | Status |
|-----------|--------|
| Charter drafted | ✅ Complete |
| Bylaws drafted | ✅ Complete |
| Form 1023-EZ research | ✅ Copilot prompt ready |
| Board of Directors | ⬜ Not started |
| Legal filing (TX SOS + IRS) | ⬜ Not started |

---

## Open Items / Pending

### Needs Action from David
- [ ] **Stripe API keys** — enter in WP Admin → Xtreme Force → Payments (unblocks Sprint 3 payments)
- [ ] **The Elevation LLC** — file Texas LLC Certificate of Formation ($300, sos.state.tx.us)
- [ ] **RCI Hospitality approach** — engage commercial RE broker to contact RCI about 15119 N IH-35
- [ ] **May 25** — Hutto EDC follow-up email (reminder is set)
- [ ] **OZ 2.0 nomination** — decision needed before June 26, 2026 deadline
- [ ] **PBS Foundation Board** — finalize board of directors (blocks 1023-EZ filing)
- [ ] **Gravity Forms** — deactivate 17 legacy forms + delete PayPal Standard add-on (XFTC WP Admin)
- [ ] **Nutrue Apparel LLC** — register as LLC to unlock grant eligibility
- [ ] **Psi Beta Sigma chapter city** — provide for local grant targeting

### Pending Connections
- [ ] nutrueapparel.com email (SMTP/IMAP credentials needed)
- [ ] Outlook account (allensmithagent)
- [ ] psibetasigma1914 email

---

## Notes
- XFTC 501(c)(3) is the anchor nonprofit for YEPC capital grant strategy
- The Elevation LLC should be formed BEFORE TABC application — TABC requires TX registered entity
- AgentHarness GitHub repo: https://github.com/dpoly2/AgentHarness
- Nightly GitHub sync automation keeps all project files current
