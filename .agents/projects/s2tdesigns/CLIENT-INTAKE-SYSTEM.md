# S2T Designs — Dynamic Client Intake & Team Assignment System
**Version:** 1.0
**Last Updated:** 2026-05-26
**Purpose:** Standardized process for onboarding any new client and dynamically assembling the right agent team based on their actual needs.

---

## HOW IT WORKS

1. Client fills out the **Intake Questionnaire** (Section 1)
2. Responses are scored against the **Need Detection Matrix** (Section 2)
3. The matrix outputs a **Team Assignment Profile** — the exact agents needed (Section 3)
4. A **Client Folder** is auto-created from the template (Section 4)
5. The **PROJECT.md** is pre-filled with all intake data and team assignments (Section 5)
6. Client is added to `CLIENT-ROSTER.md` and the master `roster.md`

---

## SECTION 1 — CLIENT INTAKE QUESTIONNAIRE

> Give this to every new client on first contact. Can be sent as a form, email, or collected verbally on a discovery call.

```
S2T DESIGNS — NEW CLIENT INTAKE FORM
=====================================

ABOUT YOUR BUSINESS
1. Business / Organization Name:
2. Industry / Type: (e.g. church, nonprofit, retail, restaurant, professional services)
3. Location / Service Area:
4. Primary Contact Name + Email + Phone:
5. Existing website URL (if any):
6. Social media accounts (list all active):

PROJECT GOALS
7. What is the PRIMARY goal of this project? (pick one)
   [ ] Build a brand new website from scratch
   [ ] Redesign / rebuild existing website
   [ ] Add e-commerce / online store
   [ ] Branding only (logo, colors, brand guide)
   [ ] Social media setup / management
   [ ] Ongoing maintenance / support plan
   [ ] Other: _______________

8. What SECONDARY goals apply? (check all that apply)
   [ ] Increase visibility / attract new customers/visitors
   [ ] Sell products online
   [ ] Accept donations or tithes
   [ ] Promote events
   [ ] Manage members or subscribers
   [ ] Post news / blog / sermons
   [ ] Book appointments online
   [ ] Run paid ads (Facebook, Google)
   [ ] Grow social media following
   [ ] Email newsletter / marketing
   [ ] SEO / Google search ranking
   [ ] Replace a broken or outdated site

TECHNICAL & BUDGET
9. How would you rate your team's tech comfort?
   [ ] None — we need you to handle everything
   [ ] Basic — we can update text/images but not code
   [ ] Intermediate — we've used a website builder
   [ ] Advanced — we have someone on staff who can handle updates

10. What is your budget range for this project?
    [ ] Under $500
    [ ] $500–$1,000
    [ ] $1,000–$2,500
    [ ] $2,500–$5,000
    [ ] $5,000+
    [ ] Not sure — tell me what makes sense

11. Do you have a hard deadline?
    [ ] Yes — Date: _______________
    [ ] No — flexible

CONTENT & ASSETS
12. Do you have a logo?
    [ ] Yes — ready to provide
    [ ] Yes — but it needs a refresh
    [ ] No — need one designed from scratch

13. Do you have professional photos?
    [ ] Yes — ready to provide
    [ ] No — we'll need stock photos or a photo shoot

14. Who will write the website copy (text)?
    [ ] We will write it ourselves
    [ ] We need S2T to write it or help edit
    [ ] We have existing copy to reuse

15. Who will manage the site after launch?
    [ ] We will update it ourselves
    [ ] We need S2T to maintain it monthly
    [ ] We'll decide after launch

REFERENCE & INSPIRATION
16. Share 2–3 websites you like the look or feel of:
    a.
    b.
    c.

17. Any competitors or peer organizations whose site you admire?

18. Anything else we should know about your project or organization?
```

---

## SECTION 2 — NEED DETECTION MATRIX

> Read the intake answers and check every box that applies. Each checked box maps to one or more agents.

### A. WEBSITE TYPE
| If client needs... | Assign |
|--------------------|--------|
| New website from scratch | s2t-webdev-agent + s2t-brand-designer-agent |
| Redesign existing site | s2t-webdev-agent + s2t-platform-assessment-helper |
| WordPress specifically | s2t-webdev-agent + wordpresspluginsagent |
| Non-WordPress (Wix, Squarespace, etc.) | s2t-webdev-agent |
| Site audit only | s2t-platform-assessment-helper |

### B. BRANDING & DESIGN
| If client needs... | Assign |
|--------------------|--------|
| New logo | s2t-brand-designer-agent |
| Color palette + brand guide | s2t-brand-designer-agent |
| Print materials (flyers, banners) | s2t-brand-designer-agent |
| Social media graphic templates | s2t-brand-designer-agent + social-designer |
| Photography direction / sourcing | s2t-brand-designer-agent |

### C. E-COMMERCE & PAYMENTS
| If client needs... | Assign |
|--------------------|--------|
| Online store (products) | s2t-webdev-agent + nutrue-ecommerce-agent (as consultant) |
| Online donations / tithes | s2t-webdev-agent (GiveWP or Tithe.ly integration) |
| Event ticket sales | s2t-webdev-agent (The Events Calendar + payment gateway) |
| Membership / subscription billing | xftc-payments-agent (as consultant for TrackSuite) |
| Booking / appointments | s2t-webdev-agent (Bookly or Calendly integration) |

### D. CONTENT & MEDIA
| If client needs... | Assign |
|--------------------|--------|
| Blog / news section | s2t-webdev-agent + s2t-content-helper |
| Sermon archive / media library | s2t-webdev-agent + ministry-project-lead (as consultant) |
| Event calendar | s2t-webdev-agent |
| Photo gallery | s2t-webdev-agent + s2t-brand-designer-agent |
| Video integration (YouTube/Vimeo) | s2t-webdev-agent + social-video-designer |
| Copywriting / page text | s2t-content-helper |

### E. SOCIAL MEDIA
| If client needs... | Assign |
|--------------------|--------|
| Social media setup (new accounts) | social-project-lead + social-content-strategist |
| Content calendar / strategy | social-content-strategist |
| Caption writing / post creation | social-copywriter |
| Graphic post design | social-designer |
| Video / Reels / TikTok | social-video-designer |
| Facebook / Google Ads | social-ads-manager |
| Community management / DM replies | social-community-manager |
| Analytics / performance reporting | social-analyst |

### F. SEO & VISIBILITY
| If client needs... | Assign |
|--------------------|--------|
| On-page SEO setup | s2t-seo-agent |
| Google Business Profile | s2t-seo-agent + social-project-lead |
| Local search optimization | s2t-seo-agent |
| Google Analytics setup | s2t-seo-agent |

### G. EMAIL MARKETING
| If client needs... | Assign |
|--------------------|--------|
| Email newsletter setup | s2t-webdev-agent (MailPoet / Mailchimp integration) |
| Newsletter content / writing | sigma-signal-writer (as consultant if newsletter-focused) |
| Email automation / drip campaigns | s2t-webdev-agent + social-content-strategist |

### H. ONGOING MAINTENANCE
| If client needs... | Assign |
|--------------------|--------|
| Monthly plugin updates + backups | s2t-maintenance-agent |
| Security monitoring | s2t-maintenance-agent |
| Content updates (text/images) | s2t-maintenance-agent + s2t-content-helper |
| Emergency support / uptime | s2t-devops-helper |

### I. NONPROFIT / CHURCH SPECIFIC
| If client needs... | Assign |
|--------------------|--------|
| Grant research support | grants-research-agent |
| Donation page + donor management | s2t-webdev-agent + pbs-fundraising-agent (as consultant) |
| 501(c)(3) compliance language | pbs-legal-agent (as consultant) |
| Member portal | xftc-plugin-dev (as consultant for TrackSuite) |
| Ministry / sermon content strategy | ministry-project-lead (as consultant) |

---

## SECTION 3 — TEAM ASSIGNMENT PROFILES

> Pre-built team configs for the most common client types. Pick the closest match, then add/remove based on the matrix above.

---

### PROFILE A — Church / Faith Organization
**Triggers:** nonprofit, church, ministry, donations, sermons, events, community

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Brand Designer | s2t-brand-designer-agent | ✅ Always |
| SEO | s2t-seo-agent | ✅ (Google Business Profile critical) |
| Social Lead | social-project-lead | ✅ (Facebook/YouTube primary) |
| Social Ads | social-ads-manager | ✅ (Facebook Ads for growth) |
| Video Designer | social-video-designer | ✅ (Sermon clips / Reels) |
| Content Helper | s2t-content-helper | ✅ (Ministry copy) |
| Maintenance | s2t-maintenance-agent | 🟡 Optional (monthly plan) |
| Ministry Consultant | ministry-project-lead | 🟡 If sermon content strategy needed |

**Standard deliverables:** Full WordPress site (Kadence) + Google Business Profile + Facebook setup + sermon archive + online giving integration

---

### PROFILE B — Nonprofit / Foundation
**Triggers:** 501(c)(3), grants, donations, programs, board, scholarship

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Brand Designer | s2t-brand-designer-agent | ✅ Always |
| SEO | s2t-seo-agent | ✅ |
| Content Helper | s2t-content-helper | ✅ (mission/program copy) |
| Grant Research | grants-research-agent | 🟡 If funding support needed |
| Legal Consultant | pbs-legal-agent | 🟡 If 501(c)(3) language needed |
| Social Lead | social-project-lead | 🟡 Optional |
| Maintenance | s2t-maintenance-agent | 🟡 Optional |

**Standard deliverables:** WordPress site + donation page + events calendar + email newsletter integration

---

### PROFILE C — Small Business / Retail
**Triggers:** products, services, local business, appointments, e-commerce

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Brand Designer | s2t-brand-designer-agent | ✅ Always |
| SEO | s2t-seo-agent | ✅ (local search critical) |
| Social Lead | social-project-lead | ✅ |
| Social Ads | social-ads-manager | ✅ (Google/Meta ads) |
| Content Helper | s2t-content-helper | ✅ |
| Maintenance | s2t-maintenance-agent | ✅ (recommended) |

**Standard deliverables:** WordPress site + Google Business Profile + WooCommerce (if products) + Bookly (if appointments)

---

### PROFILE D — Apparel / E-Commerce Brand
**Triggers:** clothing, apparel, Shopify, POD, Printful, products, collections

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Brand Designer | s2t-brand-designer-agent | ✅ Always |
| Social Lead | social-project-lead | ✅ |
| Social Ads | social-ads-manager | ✅ (Meta/TikTok ads) |
| Video Designer | social-video-designer | ✅ (product drops/Reels) |
| Copywriter | social-copywriter | ✅ (product descriptions) |
| E-Commerce Consultant | nutrue-ecommerce-agent | 🟡 Printful/Shopify expertise |

**Standard deliverables:** Shopify store (or WooCommerce) + Printful integration + social profiles + launch campaign

---

### PROFILE E — Youth / Sports Organization
**Triggers:** youth, sports, track, athletes, registration, schedule, coaches

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Plugin Dev Consultant | xftc-plugin-dev | 🟡 If TrackSuite licensing applies |
| Brand Designer | s2t-brand-designer-agent | ✅ |
| Payments Consultant | xftc-payments-agent | 🟡 If registration/payment portal needed |
| Social Lead | social-project-lead | ✅ |

**Standard deliverables:** WordPress site + registration/payment system + events/meet schedule + athlete roster

---

### PROFILE F — Professional Services / Consultant
**Triggers:** law, finance, consulting, real estate, healthcare, professional

| Role | Agent | Required? |
|------|-------|-----------|
| Project Lead | s2t-project-lead | ✅ Always |
| Web Developer | s2t-webdev-agent | ✅ Always |
| Brand Designer | s2t-brand-designer-agent | ✅ |
| SEO | s2t-seo-agent | ✅ (local + authority SEO) |
| Content Helper | s2t-content-helper | ✅ (professional bio + service pages) |
| Social Lead | social-project-lead | 🟡 (LinkedIn priority) |
| Maintenance | s2t-maintenance-agent | ✅ |

**Standard deliverables:** WordPress site + Google Business Profile + LinkedIn optimization + contact/booking form

---

## SECTION 4 — NEW CLIENT FOLDER STRUCTURE

> When a new client is onboarded, create this folder in the workspace:

```
.agents/projects/s2tdesigns/clients/[client-slug]/
├── PROJECT.md          ← Master project doc (use template below)
├── INTAKE.md           ← Raw intake questionnaire responses
├── SITE-REVIEW.md      ← Audit of existing site (if applicable)
├── BRAND-GUIDE.md      ← Brand colors, fonts, logo rules (once defined)
├── SOCIAL-AUDIT.md     ← Social media audit (if social is in scope)
├── MEDIA-CAMPAIGN.md   ← Social/ad campaign plan (if applicable)
└── assets/
    ├── logo/           ← Logo files (SVG, PNG, etc.)
    ├── images/         ← Photography and site images
    └── branding/       ← Brand documents, PDFs
```

**Client slug naming:** lowercase, hyphenated
- Little Ebenezer Baptist Church → `lebc`
- Psi Beta Sigma 1914 → `pbs`
- First Baptist Church Austin → `first-baptist-austin`
- Smith Auto Repair → `smith-auto`

---

## SECTION 5 — PROJECT.MD TEMPLATE

> Copy this for every new client. Fill in from intake data.

```markdown
# S2T Designs — Client: [CLIENT NAME]
**Client Slug:** [slug]
**Last Updated:** [DATE]
**Status:** 🟡 Discovery

---

## Client Info
- **Organization:** [Full legal name]
- **Type:** [Church / Nonprofit / Small Business / E-Commerce / Other]
- **Site URL (Current):** [URL or "None"]
- **Site URL (New Build):** [staging URL once created]
- **Platform:** [WordPress / Shopify / Wix / TBD]
- **Contact:** [Name — email — phone]
- **Address / Location:** [City, State]

---

## Project Scope
- **Primary Goal:** [from intake Q7]
- **Secondary Goals:** [from intake Q8 — list all checked items]
- **Budget:** [from intake Q10]
- **Deadline:** [from intake Q11]
- **Tech Comfort:** [from intake Q9]

---

## Assigned Team
| Role | Agent | Status |
|------|-------|--------|
| Project Lead | s2t-project-lead | ✅ Active |
| [Role] | [agent-slug] | ✅/🟡/⬜ |
| [Role] | [agent-slug] | ✅/🟡/⬜ |

*(Built from Need Detection Matrix — Section 2 of CLIENT-INTAKE-SYSTEM.md)*

---

## Branding
- **Primary Color:** [Hex]
- **Secondary Color:** [Hex]
- **Font (Headlines):** [Font name]
- **Font (Body):** [Font name]
- **Logo Status:** [Ready / Needs refresh / To design]
- **Photography:** [Ready / Need stock / Need shoot]

---

## Site Architecture
*(List pages here once confirmed)*
- Home
- About
- [Additional pages based on scope]

---

## Milestone Tracker
| Phase | Status | Notes |
|-------|--------|-------|
| Intake & Discovery | ⬜ | |
| Platform Assessment | ⬜ | |
| Proposal Sent | ⬜ | |
| Contract Signed | ⬜ | |
| Brand / Design | ⬜ | |
| Development | ⬜ | |
| Content Load | ⬜ | |
| QA & Review | ⬜ | |
| Launch | ⬜ | |
| Post-Launch / Maintenance | ⬜ | |

---

## Key Files
- `.agents/projects/s2tdesigns/clients/[slug]/INTAKE.md`
- `.agents/projects/s2tdesigns/clients/[slug]/BRAND-GUIDE.md`
- `.agents/projects/s2tdesigns/clients/[slug]/assets/`
```

---

## SECTION 6 — ONBOARDING CHECKLIST

> Run this every time a new client is added. Check off in order.

```
NEW CLIENT ONBOARDING CHECKLIST
================================
Client Name: _______________
Date Started: _______________

INTAKE
[ ] Intake questionnaire completed (INTAKE.md saved)
[ ] Existing site audited if applicable (SITE-REVIEW.md)
[ ] Social media audited if social is in scope (SOCIAL-AUDIT.md)
[ ] Discovery call scheduled / completed

SETUP
[ ] Client slug assigned (lowercase-hyphenated)
[ ] Client folder created: .agents/projects/s2tdesigns/clients/[slug]/
[ ] PROJECT.md created from template and filled in
[ ] CLIENT-ROSTER.md updated with new client row
[ ] roster.md Client & Site Registry updated

TEAM ASSIGNMENT
[ ] Need Detection Matrix completed (Section 2)
[ ] Team Profile selected (Section 3 — A/B/C/D/E/F)
[ ] All assigned agents listed in PROJECT.md
[ ] Any cross-project consultants notified (e.g. social-project-lead, ministry-project-lead)

DELIVERABLES
[ ] Proposal drafted and sent (s2t-comms-agent)
[ ] Contract / agreement signed
[ ] Staging environment created at staging.s2tdesigns.com/[client-slug]
[ ] GitHub folder pushed to dpoly2/AgentHarness

LAUNCH
[ ] Site QA completed
[ ] DNS migration plan confirmed
[ ] Client training session scheduled (if needed)
[ ] Maintenance plan offered
[ ] CLIENT-ROSTER.md status updated to 🟢 Live
```

---

## SECTION 7 — QUICK-ADD COMMAND

> When David says "add new client [NAME]", run through this in order:

**Step 1:** Ask these 5 fast questions (if not already known):
```
1. What type of org? (church / nonprofit / business / apparel / sports / professional)
2. What's the main goal? (new site / redesign / social / branding / maintenance)
3. Do they need e-commerce or payments? (yes / no)
4. Do they need social media management? (yes / no)
5. Budget range? (under $1k / $1k-$2.5k / $2.5k-$5k / $5k+)
```

**Step 2:** Match to Team Profile (A–F) + run Need Detection Matrix for any extras

**Step 3:** Create the client folder + PROJECT.md + update CLIENT-ROSTER.md + roster.md

**Step 4:** Push to GitHub

**Done.** Client is live in the system with the right team assigned.
