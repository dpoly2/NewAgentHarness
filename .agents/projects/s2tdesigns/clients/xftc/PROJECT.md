# S2T Designs — Client: Xtreme Force Track Club
**Client Slug:** xftc
**Last Updated:** 2026-05-26

---

## Client Info
- **Organization:** Xtreme Force Track Club (XFTC)
- **Site URL (Live):** https://xtremeforcetrackclub.org
- **Site URL (Staging):** https://staging.s2tdesigns.com
- **Platform:** WordPress — custom `xftc-theme` + `xftc-membership` plugin
- **WP User:** dsmith
- **Hosting:** (confirm with David)
- **Contact:** David Smith — dsmith@xtremeforcetrackclub.org

---

## Stack
- **Theme:** Custom `xftc-theme` (WordPress)
- **Plugin:** Custom `xftc-membership` (coach portal, athlete dashboard, Stripe payments)
- **Payments:** Stripe (live keys pending)
- **Staging:** staging.s2tdesigns.com (user: agent_design)

---

## Managing Team
- **Lead:** xftc-project-lead
- **Plugin Dev:** xftc-plugin-dev
- **Frontend Dev:** xftc-frontend-dev
- **DevOps:** xftc-devops-agent
- **Social Media:** social-project-lead (Project 11)

---

## Status
| Phase | Status | Notes |
|-------|--------|-------|
| Sprint 1 — Core theme | ✅ Done | Custom WordPress theme built |
| Sprint 2 — Membership plugin | ✅ Done | Coach portal + athlete dashboard |
| Sprint 3 — Dashboard widgets | 🟡 Active | Coach portal, Stripe live keys |
| Stripe live keys | ⬜ Blocked | Awaiting keys from David |
| SFTP credentials | ⬜ Blocked | Needed for plugin deployment |
| Go-live | ⬜ Pending | After Stripe + SFTP resolved |

## Current Blockers
- [ ] Stripe live API keys (test keys working on staging)
- [ ] SFTP/hosting credentials for plugin deployment to live
- [ ] Coach portal dashboard widgets (Sprint 3)

---

## Key Files
- Full project docs: `.agents/projects/xftc-redevelopment/`
- Plugin code: `projects/xftc-membership-plugin/`
- Theme code: `projects/xftc-theme/`
