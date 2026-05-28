# TrackSuite — WordPress Plugin Product Roadmap

**Project:** Productization of the XFTC Membership Plugin + Theme
**Working Title:** TrackSuite (placeholder — to be finalized)
**Owner:** David Smith / Smith Capital Properties
**Started:** 2026-05-20
**Status:** Phase 0 — Planning

---

## Vision

A white-label WordPress membership suite purpose-built for track & field clubs. Bundles a data management plugin + branded theme into a single installable product sold to USATF-registered clubs nationwide.

**Target Market:** 3,000+ USATF registered clubs currently using Gravity Forms hacks, spreadsheets, or nothing at all.

---

## Business Model — Freemium + Annual License

| Tier | Price | Features |
|------|-------|---------|
| **Free** | $0 | Registration, roster management, meet schedule, basic parent portal |
| **Pro** | $149/year | Stripe payments, travel manifests, payroll, results analytics, priority support |
| **Club+** | $299/year | Multi-team support, custom branding wizard, API access, white-glove onboarding |

**Revenue targets:**
- 50 clubs → $7,500 ARR
- 200 clubs → $30,000 ARR
- 500 clubs → $75,000 ARR

**Distribution:** freemium core on WordPress.org + Pro license via dedicated sales site

---

## Phase Overview

| Phase | Name | Goal | Est. Timeline |
|-------|------|------|---------------|
| 0 | Planning | Roadmap, architecture audit, naming | Week 1 |
| 1 | De-brandification | Remove all XFTC hardcoding, make config-driven | Weeks 2–3 |
| 2 | Onboarding Wizard | Club setup flow, color picker, Stripe connect | Weeks 4–5 |
| 3 | License System | Gate Pro features behind license key | Weeks 6–7 |
| 4 | Multi-sport Extensibility | Abstract "track & field" into configurable event types | Weeks 8–9 |
| 5 | Demo & Docs | Demo site, full documentation, video walkthrough | Weeks 10–11 |
| 6 | Launch | WordPress.org submission, sales site live, first 10 clubs | Week 12 |

---

## Phase 1 — De-brandification (Priority: IMMEDIATE)

Everything hardcoded for XFTC must become dynamic. This is the foundational requirement before any other club can install it.

### 1.1 — Settings API refactor
Replace all hardcoded strings with `get_option()` calls:

| Hardcoded Value | Replacement Option Key |
|-----------------|----------------------|
| "Xtreme Force Track Club" | `tracksuite_club_name` |
| "XFTC" | `tracksuite_club_abbreviation` |
| Navy/gold color scheme | `tracksuite_primary_color`, `tracksuite_accent_color` |
| "xtremeforcetrackclub.org" | `tracksuite_club_domain` |
| Austin / Pflugerville, TX | `tracksuite_club_location` |
| `info@xtremeforcetrackclub.org` | `tracksuite_club_email` |
| Gravity Forms references | removed |

### 1.2 — Theme Customizer integration
- Add a "TrackSuite" panel in WP Customizer
- Color picker: primary, accent, background
- Logo upload (replaces hardcoded XFTC logo)
- Club name + tagline fields
- Live preview in Customizer

### 1.3 — Database table prefix abstraction
Current tables: `wp_ts_athletes`, `wp_ts_meets`, etc.
Change to: `wp_ts_athletes`, `wp_ts_meets` (or make prefix configurable)
Add migration script for existing XFTC installs

### 1.4 — Email template variables
All emails currently reference "Xtreme Force" — replace with `{club_name}` merge tag system

---

## Phase 2 — Onboarding Wizard

First-run experience when plugin is activated on a new site.

### Steps:
1. **Club Info** — name, abbreviation, location, contact email, logo upload
2. **Season Setup** — current season name, registration open/close dates, age divisions
3. **Membership Tiers** — configure tier names and pricing (Free/Standard/Premium or custom)
4. **Payment Setup** — Stripe publishable + secret key entry, test connection
5. **Team Roles** — confirm admin email, invite first coach/staff member
6. **Done** — summary screen, links to portal + admin dashboard

---

## Phase 3 — License Key System

Gate Pro features behind a license key validated against a remote license server.

### Options:
| Solution | Pros | Cons |
|----------|------|------|
| **EDD Software Licensing** | Battle-tested, WP-native, $99 | Requires EDD store setup |
| **WP License Manager** | Lightweight, open source | Less support |
| **Freemius** | Handles billing + licensing + analytics | Revenue share (25%) |
| **Custom** | Full control | Dev overhead |

**Recommendation:** Start with **Freemius** for speed to market — handles payments, license keys, auto-updates, and analytics out of the box. Move to EDD if revenue share becomes painful at scale.

### Pro-gated features:
- `class-ts-payments.php` (Stripe integration)
- `class-ts-payroll.php`
- `class-ts-travel.php`
- Results analytics + Chart.js graphs
- CSV export functions
- API endpoints

---

## Phase 4 — Multi-Sport Extensibility

Abstract "track & field" event types into a configurable system so the plugin can serve cross country, swimming, wrestling clubs with minimal customization.

### Key abstractions:
- "Event categories" (100m, 200m, long jump...) → configurable via admin, not hardcoded
- "Result type" (time/distance/height/points) → per-event setting
- "Personal best" logic → driven by result type (lower = better for time, higher = better for distance)
- Season structure → configurable (indoor/outdoor/cross country or Spring/Fall/Year-round)

---

## Phase 5 — Demo & Documentation

### Demo site:
- Spin up a fresh WP install with TrackSuite
- Populate with fictional club: "Riverside Runners Track Club"
- Pre-loaded: 20 athletes, 5 meets, results, travel bookings
- Public URL for sales demos

### Documentation:
- Installation guide
- Club setup walkthrough
- Admin manual (meets, results, travel, payroll)
- Parent portal guide
- Stripe setup guide
- Developer hooks reference (filters + actions for customization)

---

## Phase 6 — Launch

### WordPress.org submission:
- Plugin meets WP.org guidelines (no encoded PHP, GPL-compatible)
- Readme.txt with screenshots
- Stable tag: 1.0.0

### Sales site (tracksuite.io or similar):
- Landing page with demo video
- Pricing table (Free / Pro / Club+)
- Freemius checkout embedded
- Blog: "Why your track club needs a real management system"

### Go-to-market:
- Post in USATF Club Directors Facebook group
- Reach out to 10 USATF registered TX clubs directly
- Offer free onboarding for first 5 clubs (testimonials + case studies)

---

## Codebase Changes Required (Priority Order)

1. [ ] Rename all `TRACKSUITE_` prefixes → `tracksuite_` (plugin functions, hooks, options)
2. [ ] Replace hardcoded strings with Settings API calls
3. [ ] Abstract DB table prefix
4. [ ] Add WP Customizer panel for theme branding
5. [ ] Build onboarding wizard (Settings → TrackSuite Setup)
6. [ ] Integrate Freemius SDK for licensing
7. [ ] Gate Pro classes behind license check
8. [ ] Abstract event categories + result types
9. [ ] Write PHPUnit tests for core CRUD classes
10. [ ] Submit to WordPress.org

---

## Open Questions
- [ ] Final product name (TrackSuite? ClubTrack? RunnerBase? PackManager?)
- [ ] Domain acquisition for sales site
- [ ] Support model (email only? Discord community? paid support tiers?)
- [ ] XFTC stays on a custom/maintained fork — how to manage divergence from the product branch?

---

## Related Projects
- [XFTC Redevelopment](../ts-redevelopment/PROJECT.md) — source codebase
- [XFTC Sprint 2](../ts-redevelopment/SPRINT-2.md) — current verified state

---

## Assignees
- wordpresspluginsagent — technical execution
- AgentJames — project coordination, roadmap management

