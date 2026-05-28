# AgentMajesty — New Client Onboarding Protocol
**Version:** 1.0  
**Last Updated:** 2026-05-26  
**Owner:** David Smith

---

## Trigger Phrase
When the operator says **"add new client [NAME]"** (or any variation like "onboard new client", "new client intake", "set up client"), AgentMajesty activates this protocol immediately.

---

## The Fast Path — 5 Questions

Ask all 5 in a single message, numbered. Do not proceed until all 5 are answered.

```
Got it — let me get [NAME] set up. Quick intake:

1. **Business type / industry?** (e.g., restaurant, nonprofit, real estate, e-commerce, church, law firm)
2. **Primary service we're providing?** (e.g., website design, social media, branding, full management, SEO)
3. **Primary contact name + email?**
4. **Engagement type?** (one-time project / monthly retainer / hourly)
5. **Start date or urgency?** (e.g., ASAP, next week, specific date)
```

---

## Profile Selection

Based on answers, assign the best-fit team from the existing roster:

| Client Type | Assign Lead | Assign Specialists |
|-------------|-------------|-------------------|
| Web design / branding | s2t-project-lead | s2t-webdev-agent, s2t-brand-designer-agent, s2t-seo-agent |
| Social media management | social-project-lead | social-content-strategist, social-copywriter, social-analyst |
| Nonprofit / foundation | pbs-project-lead | pbs-communications-agent, pbs-fundraising-agent |
| Real estate | smithcap-project-lead | smithcap-acquisitions-agent, smithcap-finance-agent |
| E-commerce | s2t-project-lead | s2t-webdev-agent, s2t-maintenance-agent |
| Multi-service / enterprise | s2t-project-lead | Full S2T team + social team |

---

## Deliverables — What Gets Created

After intake answers are received, AgentMajesty creates ALL of the following:

### 1. Project Folder
```
.agents/projects/s2tdesigns/clients/[slug]/
  PROJECT.md          ← filled from intake
  SCOPE.md            ← services + deliverables
  CONTACTS.md         ← client contact info
  TIMELINE.md         ← milestones + deadlines
```

### 2. PROJECT.md Template
```markdown
# [CLIENT NAME] — Project File
**Created:** [DATE]
**Client:** [CONTACT NAME] — [EMAIL]
**Business:** [BUSINESS TYPE]
**Service:** [PRIMARY SERVICE]
**Engagement:** [TYPE] — started [START DATE]
**Lead Agent:** [ASSIGNED LEAD]
**Status:** 🟡 Onboarding

---

## Scope of Work
[Derived from intake answers]

## Milestones
- [ ] Kickoff call / discovery
- [ ] Proposal / contract sent
- [ ] Contract signed
- [ ] Design/strategy phase
- [ ] Client review
- [ ] Launch / delivery
- [ ] Post-launch support

## Notes
[Any special requirements from intake]
```

### 3. Roster Updates
- Add client to `s2tdesigns/CLIENT-ROSTER.md`
- Add project entry to `.agents/agents/roster.md` PROJECT INDEX table
- Increment project count

### 4. Todos Created (auto-generated)
```
[TODO:{"title":"Send [NAME] proposal/contract","priority":"high","projectSlug":"s2tdesigns","tags":["client","onboarding"]}]
[TODO:{"title":"Schedule [NAME] kickoff call","priority":"high","projectSlug":"s2tdesigns","tags":["client","onboarding"]}]
[TODO:{"title":"Set up [NAME] project folder in Drive/GitHub","priority":"medium","projectSlug":"s2tdesigns","tags":["setup"]}]
```

### 5. GitHub Push
Commit message: `feat: onboard new client — [CLIENT NAME]`
Push to main branch.

---

## Response Format

After creating everything, AgentMajesty responds with:

```
✅ [CLIENT NAME] is in the system.

📁 Created: .agents/projects/s2tdesigns/clients/[slug]/
👤 Lead: [AGENT]
🤝 Engagement: [TYPE] starting [DATE]

What I've queued up:
• Proposal/contract todo — high priority
• Kickoff call todo — high priority  
• Project folder setup todo

Next step: want me to draft the proposal for [NAME] now?
```

---

## Slug Format
Convert client name to lowercase kebab-case:
- "First Baptist Church" → `first-baptist-church`
- "Joe's BBQ" → `joes-bbq`
- "ABC Consulting LLC" → `abc-consulting`

---

## Rules
1. **Never skip the 5 questions** — don't assume anything not provided
2. **Always create the PROJECT.md** — even if incomplete, skeleton is better than nothing
3. **Always create at least 2 todos** — proposal + kickoff call are mandatory
4. **Always update CLIENT-ROSTER.md** — it's the source of truth for S2T billing
5. **Always push to GitHub** — client data must be versioned
6. **Confirm completion** — tell operator exactly what was created
7. **Offer the next step** — "Want me to draft the proposal now?" or "Should I brief the s2t-project-lead?"
