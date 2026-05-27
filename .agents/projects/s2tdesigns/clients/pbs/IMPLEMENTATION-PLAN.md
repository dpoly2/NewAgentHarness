# Psi Beta Sigma 1914 — Website Implementation Plan
**Site:** https://newsite.psibetasigma1914.org
**Platform:** WordPress — Kadence Theme
**Managing Lead:** s2t-project-lead
**Web Dev:** s2t-webdev-agent
**Last Updated:** 2026-05-26
**Status:** 🔴 Pre-Launch — Implementation Ready, Deployment Blocked (App Password needed)

---

## SOURCE DOCUMENTS
- `PBS-WP-Content-Guide.pdf` — Full 19-page content guide (ready-to-paste copy for all pages)
- `PBS-WP-Content-Guide.docx` — Editable version of the same guide
- `REQUIREMENTS.md` — Client-provided site structure requirements

---

## FINAL SITE STRUCTURE (Reconciled from both documents)

The client's Requirements.md defines the navigation. The Content Guide fills each page with copy.

```
HOME
ABOUT
  └── Sigma History
  └── Chapter History
LEADERSHIP
  └── President's Corner
  └── Executive Board
  └── State, Regional & National Leadership
PROGRAMS
  └── Overview + International Programs
EVENTS
  └── Calendar of Events
BACK TO SCHOOL DRIVE          ← NEW PAGE (from Content Guide)
BECOME A SIGMA
SIGMA SOURCE
  └── State, Regional, National & Blu Print links
MEMBERS PORTAL                ← PASSWORD PROTECTED
  └── Membership Roster
  └── Pay Chapter Dues
CHAPTER PROGRAMS
  └── Annual Golf Tournament  ← September 26, 2026
  └── Annual Scholarship Banquet ← NEW PAGE
  └── Annual Event (placeholder)
SPONSORSHIP
  └── Become a Sponsor
  └── Sponsor Thank You page
CONTACT
```

**Total pages: 22 (including sub-pages)**
**New pages not currently on site: Back to School Drive, Scholarship Banquet, Sponsorship section**

---

## IMPLEMENTATION PHASES

---

### PHASE 1 — UNBLOCK & DEPLOY (Do First)
**Blocker:** WordPress App Password for `s2tdesignadmin` not yet provided
**Impact:** Cannot push CSS, create pages, or install plugins via API

**Tasks:**
- [ ] David generates App Password: WP Admin → Users → s2tdesignadmin → Application Passwords → Add New → name it "AgentJames" → copy the password
- [ ] Provide password to AgentJames → stored in `.agents/.env` as `WP_PBS_APP_PASSWORD`
- [ ] Verify REST API connectivity to `newsite.psibetasigma1914.org/wp-json/wp/v2`
- [ ] Deploy Austin skyline header CSS (already written in `skyline-header-css.css`)

---

### PHASE 2 — NAVIGATION & PAGE STRUCTURE
**Goal:** Build out the full 22-page structure with correct parent/child hierarchy

**Page creation order (parent pages first):**

| Page Title | Slug | Parent | Status |
|------------|------|--------|--------|
| Home | / | — | ✅ Exists |
| About | about | — | ✅ Exists — needs sub-pages |
| Sigma History | sigma-history | about | ⬜ Create |
| Chapter History | chapter-history | about | ⬜ Create |
| Leadership | leadership | — | ✅ Exists — needs sub-pages |
| President's Corner | presidents-corner | leadership | ⬜ Create |
| Executive Board | executive-board | leadership | ⬜ Create |
| State, Regional & National | state-regional-national | leadership | ⬜ Create |
| Programs | programs | — | ✅ Exists — needs content update |
| Events | events | — | ✅ Exists |
| Back to School Drive | back-to-school-drive | — | ⬜ Create NEW |
| Become a Sigma | become-a-sigma | — | ✅ Exists — no change per client |
| Sigma Source | sigma-source | — | ⬜ Create |
| Members Portal | members-portal | — | ⬜ Create (password-protected) |
| Membership Roster | membership-roster | members-portal | ⬜ Create (password-protected) |
| Pay Chapter Dues | pay-chapter-dues | members-portal | ⬜ Create (password-protected) |
| Chapter Programs | chapter-programs | — | ⬜ Create |
| Golf Tournament | golf-tournament | chapter-programs | ⬜ Create |
| Scholarship Banquet | scholarship-banquet | chapter-programs | ⬜ Create NEW |
| Annual Event | annual-event | chapter-programs | ⬜ Placeholder |
| Sponsorship | sponsorship | — | ⬜ Create |
| Contact | contact | — | ✅ Exists |

**WP REST API method:** `POST /wp/v2/pages` with `title`, `slug`, `parent`, `status: publish`, `content`

---

### PHASE 3 — CONTENT POPULATION
**Goal:** Paste all copy from the Content Guide into the correct pages

**Content ready (copy-paste from Content Guide PDF):**

| Page | Content Status | Bracketed Fields to Replace |
|------|---------------|---------------------------|
| Home — Hero | ✅ Ready | None |
| Home — Who We Are (3 cols) | ✅ Ready | None |
| Home — CTA Buttons | ✅ Ready | Link URLs |
| About — Sigma History | ✅ Ready | None |
| About — Chapter History | ✅ Ready | None |
| Leadership — Pres Corner | ✅ Ready | [President Name], [President Message] |
| Leadership — Exec Board | ✅ Template ready | [Photo], [Name], [Title] per officer |
| Leadership — State/Regional | ✅ Ready | [Southwest Region Director name], [TX State Director name] |
| Programs — All 5 | ✅ Ready | None — links to national site |
| Events | ✅ Ready | Event dates (Back to School, Scholarship Banquet) |
| Back to School Drive | ✅ Ready | [Drop-off location], [Donation link URL] |
| Become a Sigma | ✅ Ready | None |
| Sigma Source | ✅ Ready | [SW Region contact], [TX State contact] |
| Members Portal | ✅ Ready | [Dues amount] |
| Golf Tournament | ✅ Ready | [Golf course name], [times], [entry fee] |
| Scholarship Banquet | ✅ Ready | [Date], [Venue], [ticket prices] |
| Contact | ✅ Ready | [Chapter email], [social links] |

**Fields that MUST be filled in by chapter before going live:**
```
[ ] President's name + personal welcome message
[ ] Executive Board officer names + photos
[ ] Southwest Region Director name + contact
[ ] Texas State Director name + contact
[ ] Back to School Drive drop-off location
[ ] Donation link (PayPal.me, Cash App, or GiveWP URL)
[ ] Golf Tournament — course name, times, entry fee
[ ] Scholarship Banquet — date, venue, ticket prices
[ ] Chapter email address
[ ] Chapter social media handles (Instagram, Facebook, X)
[ ] Chapter dues amount (for Pay Dues page)
```

---

### PHASE 4 — PLUGIN INSTALLATION & CONFIGURATION
**Goal:** Install and configure all required plugins

| Plugin | Purpose | Page(s) | Priority |
|--------|---------|---------|----------|
| The Events Calendar (free) | Calendar of Events page | Events | 🔴 High — already on site, needs events added |
| WPForms Lite (free) | Contact form, membership interest form, dues payment | Become a Sigma, Contact, Members Portal | 🔴 High |
| GiveWP (free) | Donation pages with goal progress bars | Back to School Drive, Scholarship Banquet | 🔴 High |
| Kadence Blocks Pro | Team member cards, accordion blocks, timeline | Leadership, Programs | 🟡 Check if already active |
| Stackable (free tier) | Team member cards if Kadence insufficient | Leadership | 🟡 Optional |
| MemberPress or ProfileGrid | Password-protected members portal + roster | Members Portal | 🟡 Medium |
| Contact Form 7 | Alternative to WPForms | Multiple | 🟢 Backup option |

**Already confirmed active on site:**
- Kadence Theme ✅
- The Events Calendar ✅
- MailPoet ✅

**Install via WP REST API (once App Password provided):**
```
POST /wp/v2/plugins
{"slug": "give", "status": "active"}
{"slug": "wpforms-lite", "status": "active"}
```

---

### PHASE 5 — PAYMENT & DONATION SETUP
**Goal:** Enable all financial transactions on the site

| Transaction Type | Recommended Tool | Page | Urgency |
|-----------------|-----------------|------|---------|
| Golf Tournament tickets | WPForms + Stripe OR Eventbrite embed | Golf Tournament | 🔴 CRITICAL — June 1 deadline |
| Chapter dues | WPForms + Stripe/PayPal | Pay Chapter Dues | 🔴 High |
| Back to School donations | GiveWP campaign | Back to School Drive | 🟡 Medium |
| Scholarship Banquet tickets | WPForms + Stripe OR Eventbrite | Scholarship Banquet | 🟡 Medium |
| General donations | GiveWP or PayPal button | Home + multiple pages | 🟡 Medium |

**Fastest path for Golf Tournament (June 1 deadline):**
1. Create a free Eventbrite event → embed the Eventbrite widget on the Golf Tournament page
2. OR create a PayPal.me/Cash App link and use a WPForms simple form to collect registration info + direct to payment link
3. OR install Stripe + WPForms Stripe addon (requires WPForms Pro — $49/yr)

**Recommendation:** Use Eventbrite for the golf tournament (free, fast, no plugin needed, handles registration cap of 72 players automatically).

---

### PHASE 6 — MEMBERS PORTAL SETUP
**Goal:** Password-protected area for active members only

**Two options:**
- **Simple (no plugin):** Set Members Portal + sub-pages to "Password Protected" in WordPress Page Settings. Share one password with all members. Quick but not individual logins.
- **Full (plugin):** Use ProfileGrid (free) or MemberPress to create individual member accounts with login. Members can update their own info.

**Recommended:** Start with simple password protection → upgrade to ProfileGrid once dues collection is active.

**Implementation:**
1. Set Members Portal parent page to Password Protected (WP Page Settings → Visibility → Password Protected)
2. Set Membership Roster + Pay Dues sub-pages to same password
3. Share password with active members via chapter email
4. Roster hosted as a private Google Sheet embed (no PDF needed)

---

### PHASE 7 — SPONSORSHIP SECTION
**Goal:** New Sponsorship page with "Become a Sponsor" CTA and Thank You page

**Page content:**
- Intro: Why sponsor Psi Beta Sigma
- Sponsorship tiers (Table block):
  - Title Sponsor — $10,000 (logo placement, speaking opp, VIP foursome)
  - Platinum Sponsor — $5,000
  - Gold Sponsor — $2,500
  - Hole Sponsor (Golf) — $500
  - Community Partner — $250
- Download Sponsorship Package PDF (upload when ready)
- "Become a Sponsor" form (WPForms — name, org, tier, email, phone)
- Thank You page: auto-redirect after form submit, lists current sponsors with logos

**Sponsor logos section:** Add a Kadence logo/image gallery row on the Thank You page — update as sponsors are confirmed.

---

### PHASE 8 — EVENTS POPULATION
**Goal:** Pre-populate The Events Calendar with all known 2026 events

**Events to create:**

| Event | Date | Category | Color |
|-------|------|----------|-------|
| Phi Beta Sigma Founder's Day | January 9, 2027 (annual) | Brotherhood | White/Blue |
| Monthly BBB Business Spotlight — Whip My Soul | June 2026 | BBB | White/Blue |
| Monthly BBB Business Spotlight — Black Pearl Books | July 2026 | BBB | White/Blue |
| Monthly BBB Business Spotlight — Teakeasy | August 2026 | BBB | White/Blue |
| Back to School Supply Drive | Late August 2026 (TBD) | Education | Blue |
| Annual Golf Tournament | September 26, 2026 | Fundraising | Navy |
| Annual Scholarship Banquet | TBD | Fundraising | Navy |

**Event categories + colors (as recommended in Content Guide):**
- Education → Blue `#003087`
- Fundraising → Navy `#001F5B`
- BBB → White with blue border

---

### PHASE 9 — CSS & DESIGN POLISH
**Goal:** Deploy branding CSS and ensure visual consistency

**CSS already written:**
- Austin skyline header silhouette (`skyline-header-css.css` — ready to deploy)
- Global color: Royal Blue `#003087`
- CTA buttons: Royal blue fill, white text, white border on hover

**Additional CSS tasks:**
- [ ] Kadence global colors → set `#003087` as Primary, `#C9A84C` (gold accent) as Secondary
- [ ] Header nav — ensure royal blue background with white links
- [ ] Hero blocks on each page — consistent Cover Block style (royal blue bg, white text)
- [ ] Team member cards (Exec Board) — royal blue card header, white background
- [ ] Footer — royal blue background, white text, social icons

---

## IMPLEMENTATION SPRINT PLAN

### Sprint A — Unblock & Foundation (Do immediately once App Password provided)
1. Verify API connectivity
2. Deploy skyline CSS
3. Create all parent pages with correct slugs + hierarchy
4. Set Members Portal pages to password-protected

### Sprint B — Content Load (1–2 days)
1. Populate all pages with copy from Content Guide
2. Leave bracketed fields as visible placeholders `[FILL IN: President Name]`
3. Add all anchor events to The Events Calendar

### Sprint C — Payments & Plugins (2–3 days, parallel with B)
1. Install GiveWP — create Back to School campaign
2. Set up Golf Tournament registration (Eventbrite OR WPForms)
3. Install WPForms — build membership interest form + contact form
4. Set up dues payment link

### Sprint D — New Pages (2–3 days)
1. Back to School Drive page (full content + donation CTA)
2. Scholarship Banquet page (full content + ticket/sponsor CTA)
3. Sponsorship page + Thank You page
4. Sigma Source page (resource links)

### Sprint E — QA & Launch Prep (1 day)
1. Test all forms
2. Test all payment flows
3. Test password-protected pages
4. Mobile responsiveness check
5. DNS migration to psibetasigma1914.org production domain

---

## OPEN ITEMS REQUIRING CHAPTER INPUT

> These CANNOT be completed without information from the chapter. Flag to David for follow-up.

| Item | Who Provides | Urgency |
|------|-------------|---------|
| President's name + personal letter | Chapter President | 🔴 High |
| Executive Board full roster (name, title, photo) | Chapter Secretary | 🔴 High |
| Golf Tournament — course, times, entry fee | Tournament Chair | 🔴 CRITICAL (June 1) |
| Chapter email address | Chapter President | 🔴 High |
| Donation/payment method preference (Stripe vs PayPal vs Cash App) | Treasurer | 🔴 High |
| Back to School Drive — drop-off location | Programs Chair | 🟡 Medium |
| Scholarship Banquet — date, venue | Events Chair | 🟡 Medium |
| SW Region Director + TX State Director names | Chapter records / phibetasigma1914.org | 🟡 Medium |
| Social media handles (Instagram, Facebook, X) | Communications Officer | 🟡 Medium |
| Chapter dues amount | Treasurer | 🟡 Medium |
| Sponsorship Package PDF | Chapter President | 🟡 Medium (pre-launch is fine) |
| Officer headshots/photos | Each officer | 🟡 Medium |

---

## BLOCKERS (Current)

| Blocker | Impact | Resolution |
|---------|--------|------------|
| No WP App Password for s2tdesignadmin | Cannot deploy anything via API | David generates in WP Admin |
| DNS not migrated to production domain | Site not live at psibetasigma1914.org | Namecheap DNS update after QA complete |
| Golf Tournament payment gateway not set up | June 1 registration deadline at risk | Eventbrite OR WPForms + Stripe — do this week |
| Chapter contact info / officer names not provided | Multiple pages have placeholder copy | Chapter needs to fill in REQUIREMENTS data |
