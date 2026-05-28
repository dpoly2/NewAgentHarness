# XFTC Redevelopment Project

**Last Updated:** May 20, 2026
**Status:** Sprint 2 Complete ✅ | Sprint 3 In Planning 🔜

---

## Project Summary

Full redevelopment of the Xtreme Force Track Club web presence using a custom WordPress plugin + standalone theme architecture. The system replaces the legacy Gravity Forms-based workflow with a purpose-built membership management platform.

**Live Site:** https://xtremeforcetrackclub.org
**Staging:** https://staging.s2tdesigns.com

---

## Components

| Component | Version | Status |
|-----------|---------|--------|
| `ts-membership` plugin | v2.0.0 | ✅ Sprint 2 Complete |
| `ts-theme` | v1.0.0 | ✅ Deployed to staging |

→ See individual READMEs:
- [Plugin README](plugin/ts-membership/README.md)
- [Theme README](theme/ts-theme/README.md)

---

## Sprint Overview

### Sprint 1 ✅ — Core Foundation
**Delivered:** Plugin scaffold, 10-table DB schema, 5 user roles, member + season CRUD

### Sprint 2 ✅ — Feature Modules
**Delivered:**
- Meet management + athlete enrollment
- Results tracking
- Travel manifests
- Payroll system
- Stripe payment placeholder
- Multi-step registration form (4 steps)
- Tabbed parent portal dashboard
- Plugin/theme decoupled via 13 shortcodes
- 4 AJAX endpoints
- Bug fix: `send_parent_welcome()` activation error resolved

**Verified on staging:**
- ✅ Plugin activates without fatal errors
- ✅ Portal page renders for logged-in users
- ✅ Register page renders for logged-out users
- ✅ Step 1 → Step 2 navigation working (JS multi-step form)
- ✅ Logged-in users redirected from `/register/` to `/portal/`

### Sprint 3 🔜 — Production Ready
**Planned:**
- [ ] Stripe live keys entered in WP Admin settings
- [ ] Coach/staff front-end portal (eliminate WP Admin dependency)
- [ ] Full end-to-end registration test (Steps 1–4 + AJAX submit)
- [ ] Permalink flush on production
- [ ] Plugin + theme install on xtremeforcetrackclub.org
- [ ] Load testing and QA

---

## Documents

| Document | Description |
|----------|-------------|
| [PROPOSAL.md](PROPOSAL.md) | 12-week project proposal |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture overview |
| [SPRINT-1.md](SPRINT-1.md) | Sprint 1 task log |
| [SPRINT-2.md](SPRINT-2.md) | Sprint 2 task log |
| [PROJECT.md](PROJECT.md) | Ongoing project notes |

