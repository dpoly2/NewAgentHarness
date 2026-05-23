# S2T Designs — Platform Assessment Guide
**Last Updated:** 2026-05-22

This guide is used by the s2t-webdev-agent to assess the best platform for each new client project.

---

## Platform Comparison Matrix

| Platform | Best For | Avoid When | Monthly Cost | Ownership |
|----------|----------|------------|--------------|-----------|
| **WordPress (self-hosted)** | Complex sites, custom functionality, full control, nonprofits, membership sites | Client can't manage tech; tiny budgets | $5–$50/mo hosting | Full — client owns everything |
| **Wix** | Small businesses, fast turnaround, drag-and-drop convenience, appointment booking | Need full code control or custom backend | $16–$45/mo | Platform-locked — can't export |
| **Weebly** | Very simple sites, square/ecommerce small stores | Scalability, modern design needs | $10–$26/mo | Platform-locked |
| **Squarespace** | Portfolio sites, photographers, restaurants, clean aesthetics | E-commerce at scale, custom code needs | $16–$49/mo | Platform-locked |
| **Webflow** | Design-heavy sites, animations, CMS, dev handoffs, agencies | Non-technical clients managing content | $14–$212/mo | Exportable HTML/CSS |
| **Shopify** | E-commerce first, product-heavy stores, Printful/POD | Services-only businesses, blogs | $29–$299/mo | Platform-locked but robust API |
| **GoDaddy Website Builder** | Absolute beginners, hyper-local small biz | Any business that plans to grow | $10–$20/mo | Platform-locked |

---

## Platform Decision Framework (Per Client)

### Step 1 — Assess the Client
Ask these 5 questions:
1. **What is the primary goal?** (Sell products / generate leads / share content / membership / portfolio)
2. **What is the technical ability of the person managing the site?**
3. **What is the monthly/annual budget for hosting + maintenance?**
4. **Does the site need custom functionality?** (booking, membership, payments, custom database)
5. **How important is long-term ownership and portability?**

### Step 2 — Score Against the Matrix
Score each platform 1–5 on:
- Goal fit
- Client manageability
- Budget fit
- Feature fit
- Ownership/portability

### Step 3 — Recommend + Justify
Provide 1 primary recommendation + 1 alternative, with a plain-English justification the client can understand.

---

## Platform Deep Dives

### WordPress (Self-Hosted)
**Strengths:** Open source, infinite extensibility, plugin ecosystem (60,000+), strong SEO, full ownership, WooCommerce for e-commerce, membership plugins (MemberPress, Paid Memberships Pro), multisite for agencies
**Weaknesses:** Requires hosting management, plugin conflicts, security maintenance, steeper learning curve
**S2T Recommended Stack:**
- Hosting: SiteGround or WP Engine (managed)
- Page Builder: Elementor or Kadence Blocks (Gutenberg-native)
- E-Commerce: WooCommerce
- Security: Wordfence or Solid Security
- Backups: UpdraftPlus
- Caching: WP Rocket or LiteSpeed Cache

### Wix
**Strengths:** No hosting management, drag-and-drop, built-in booking (Wix Bookings), Wix Stores, fast setup
**Weaknesses:** Hard to migrate off, limited SEO control, customization ceiling, template lock
**Best Clients:** Hair salons, tutors, local service businesses, new entrepreneurs with small budgets
**S2T Notes:** Use Wix Editor X (Wix Studio) for responsive design control

### Squarespace
**Strengths:** Beautiful templates, excellent for portfolios and restaurants, built-in blogging, good mobile
**Weaknesses:** Limited plugins, weaker e-commerce than Shopify/WooCommerce, code injection is limited
**Best Clients:** Photographers, artists, consultants, personal brands, restaurants

### Webflow
**Strengths:** Designer-grade control, CMS collections, animations, responsive by default, clean code export
**Weaknesses:** Expensive for hosting, steep learning curve for client self-management
**Best Clients:** Startups, agencies, tech companies, any client who wants a unique visual identity
**S2T Notes:** Use for premium brand projects where design differentiation matters

### Shopify
**Strengths:** Best-in-class e-commerce, inventory management, Printful/POD integration, payments built-in, App Store
**Weaknesses:** Monthly fees scale with volume, not ideal for content-first sites
**Best Clients:** Product-based businesses, POD brands, boutiques, anyone selling 10+ SKUs
**S2T Notes:** David uses Shopify at hoodswag.shop (hsfo.myshopify.com) — use as reference deployment

---

## Red Flags That Change Platform Recommendation
- Client wants **membership site** → WordPress + MemberPress or custom plugin
- Client wants **event registration** → WordPress + Gravity Forms or The Events Calendar
- Client wants **multi-location business** → WordPress multisite or Squarespace Business
- Client needs **custom API integration** → WordPress (most flexible) or Webflow + Zapier
- Client has < $500 total budget → Wix or Squarespace (fastest delivery, no hosting overhead)
- Client wants to **own and take the site anywhere** → WordPress or Webflow (exportable)
- Client is a **nonprofit** → WordPress (cheapest long-term, grant-reportable ownership)
