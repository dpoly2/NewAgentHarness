# S2T Designs — Client: Phi Beta Sigma (PBS)
## WordPress Theme Research — Matching pbsgulfcoastregion.org
**Date:** 2026-05-22
**Prepared by:** AgentJames / s2t-webdev-agent

---

## Reference Site Analysis — pbsgulfcoastregion.org (Wix)

From a live audit of the site, the key design elements to replicate are:

| Element | Description |
|---------|-------------|
| **Top announcement bar** | Thin blue bar at top — "When We Believe, We Achieve - Stronger Together" |
| **Header** | Logo left, horizontal nav right, "Members Area / Log In" top-right corner |
| **Hero** | Full-width, full-bleed photo with large bold overlaid text ("COMMITTED to L.E.A.D.") |
| **Color palette** | Royal blue (#003087 PBS blue) + white + gold accents |
| **Typography** | Bold, heavy-weight sans-serif headlines — large and impactful |
| **Content sections** | Welcome message with image/text columns, Quick Start cards (3-up grid), sponsor logos bar |
| **Members Portal** | Gated members-only section with login |
| **Events section** | Events listing with open + members-only filter |
| **Newsletter signup** | Email subscribe widget in footer |
| **Footer** | Multi-column with nav links, social icons, copyright |
| **Navigation depth** | About Us, Programs, Events, Join Sigma, Groups, News — dropdown menus |

---

## Top Free WordPress Theme Recommendations

### 🥇 #1 — KADENCE (Primary Recommendation)
**wordpress.org/themes/kadence/**
**Active installs:** 500,000+ | **Rating:** 4.9/5 | **Updated:** May 2026

**Why it matches PBS Gulf Coast:**
- Drag-and-drop **header builder** — replicates the exact 2-row header (announcement bar top + logo/nav/login row below) without a page builder
- Full-width hero section with bold text overlay — native support
- **Global color controls** — set royal blue + white + gold once, applies site-wide
- **Announcement bar** built into the header builder (matches the blue ticker at top)
- Footer builder for multi-column footer layout
- Works seamlessly with Kadence Blocks (free) for the 3-column card sections, icon boxes, and sponsor logo rows
- Accessibility ready, extremely fast, mobile-first
- Starter templates include nonprofit/community organization designs

**Free version covers:** Full header builder, footer builder, announcement bar, global colors, global fonts, full-width sections, sidebar options, WooCommerce ready

**What's behind the pro paywall:** Advanced header scroll effects, some starter templates, conditional headers — but **none of these are needed** for the PBS site

**PBS-specific build notes:**
- Use Kadence Blocks (free plugin) for the "Quick Start" 3-card section
- Use Kadence's header builder to put "Members Area / Log In" in the top-right
- Members portal gating → use **MemberPress** or **ProfilePress** (free tier) plugin layered on top

---

### 🥈 #2 — ASTRA
**wordpress.org/themes/astra/**
**Active installs:** 1,000,000+ | **Rating:** 4.9/5 | **Updated:** May 2026

**Why it matches PBS Gulf Coast:**
- Most popular free theme on WordPress.org — 1M+ active installs, 6,000+ 5-star reviews
- Transparent/sticky header options — matches the floating header look
- Full-width hero support via Spectra (free Astra page builder plugin) or Elementor
- Custom header layouts for the two-row announcement bar + nav structure
- Lightning fast — scores 95+ on PageSpeed out of the box
- Massive library of starter templates including nonprofit orgs

**Limitation vs Kadence:** The header builder is slightly less flexible in the free version — need Spectra (free Astra plugin) or Elementor to get the two-row announcement bar layout exactly right

**PBS-specific build notes:**
- Pair with **Spectra** (free) or **Elementor Free** for the hero section
- Use Astra's built-in custom header for the Members Area login link placement
- Strong choice if the S2T team is already comfortable with Elementor

---

### 🥉 #3 — NEVE
**wordpress.org/themes/neve/**
**Active installs:** 300,000+ | **Rating:** 4.8/5

**Why it matches PBS Gulf Coast:**
- Very lightweight and fast
- Header builder included in free version (announcement bar, logo placement, nav, account icon)
- Starter templates for nonprofits and community organizations
- Clean grid layouts for the Quick Start cards section
- Members login icon/button natively in header

**Limitation:** Fewer starter templates in free tier vs Kadence; some layout controls locked behind Neve Pro

---

### Honorable Mention — BLOCKSY
**wordpress.org/themes/blocksy/**
**Active installs:** 100,000+ | **Rating:** 4.9/5

- Excellent free header builder with announcement bar support
- Very modern design output — closest to Wix's design quality
- Content blocks free plugin (Blocksy Companion) adds features
- Slightly steeper learning curve than Kadence/Astra
- Good alternative if client wants a more modern/polished look than traditional nonprofit themes

---

## Final Recommendation for PBS Client

**Go with Kadence + Kadence Blocks (both free).**

| Reason | Detail |
|--------|--------|
| Announcement bar | Built into header builder — no extra plugin |
| 2-row header | Header builder handles logo + nav + Members login in minutes |
| Hero section | Full-bleed, full-width, text overlay — native |
| Card sections | Kadence Blocks free covers the 3-up Quick Start grid |
| Color matching | Global controls — set PBS blue (#003087) once |
| Members portal | Layer ProfilePress (free) or MemberPress on top for gated content |
| Events | Layer The Events Calendar (free) for the events section |
| Speed | Kadence scores 90+ mobile PageSpeed out of the box |
| S2T familiarity | Kadence is already in S2T's recommended stack |

---

## Required Free Plugin Stack (to replicate full PBS Gulf Coast feature set)

| Plugin | Purpose | Cost |
|--------|---------|------|
| **Kadence Blocks** | Card grids, icon sections, sponsor logo rows, hero layouts | Free |
| **The Events Calendar** | Events listing with categories (open/members-only) | Free |
| **ProfilePress** | Member registration, login, members-only gating | Free tier |
| **WPForms Lite** | Contact form in footer | Free |
| **MailPoet** | Newsletter email subscribe widget | Free up to 1,000 subscribers |
| **Yoast SEO** | SEO meta, sitemap | Free |
| **Smush** | Image compression (hero photos) | Free |

**Total cost for full feature parity: $0** (free theme + free plugins)

---

## What Wix Does That Needs a Workaround in WordPress

| Wix Feature | WordPress Equivalent | Notes |
|-------------|---------------------|-------|
| Members Area (built-in) | ProfilePress or MemberPress | Free tier of ProfilePress covers basic gated content |
| Wix Groups | BuddyPress Groups (free) | More setup but fully functional |
| Wix Chat widget | Tidio or Crisp (free) | Drop-in replacement |
| Wix Blog | WordPress native blog | WordPress is better at this than Wix |
| Wix Events | The Events Calendar (free) | Near-identical feature set |

---

## Staging Plan
- Provision new subdomain: `pbs.s2tdesigns.com`
- Install WordPress + Kadence theme
- Install free plugin stack above
- Build to match pbsgulfcoastregion.org layout
- Client review on staging before migrating to their own domain

## Key Files
- `.agents/projects/s2tdesigns/PLATFORM-GUIDE.md`
- `.agents/projects/s2tdesigns/WORKFLOW.md`
