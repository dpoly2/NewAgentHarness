# Web Dev Research Agent

## Role
Research and surface actionable fixes, improvements, and solutions for each web development site. Runs analysis per agent/site and produces a prioritized recommendation report.

---

## Sites to Research

### 1. xtremeforcetrackclub.org
- **Status:** Connected via REST API
- **Known:** 33 active plugins, 10 published pages
- **Research Tasks:**
  - Check for outdated plugins and flag security risks
  - Audit page structure — are all key pages present? (Registration, Schedule, Meet Results, About, Contact)
  - Suggest seasonal content updates (registration, meet schedules)
  - Performance recommendations (image optimization, caching, CDN)
  - SEO audit — title tags, meta descriptions, schema markup for sports clubs

### 2. psibetasigma1914.org
- **Status:** Blocked — Authorization header not passing through WAF/hosting
- **Known:** Namecheap/Bosnacweb hosting, .htaccess fix applied but not working
- **Research Tasks:**
  - Alternative authentication methods (cookie-based, JWT plugins)
  - Best approach: fix main site vs. rebuild on newest.psibetasigma1914.org subdomain
  - Subdomain is returning 503 — diagnose and suggest resolution
  - Migration path: custom domain email → Gmail
  - Theme and design recommendations for a chapter/fraternity site

### 3. nutrueapparel.com
- **Status:** Blocked — same Authorization header issue (Namecheap/Bosnacweb)
- **Known:** Username nutrue_admin, e-commerce site
- **Research Tasks:**
  - WooCommerce health check — are products, shipping, and payments configured?
  - Plugin audit — e-commerce sites often accumulate bloat
  - Performance for e-commerce — page speed, checkout optimization
  - SEO for apparel e-commerce
  - Email integration — connect store emails to nutrueapparel identity agent
  - Social commerce opportunities (Instagram Shopping, TikTok Shop)

### 4. Smith Capital Properties (WordPress)
- **Status:** Credentials not yet provided
- **Research Tasks:**
  - Real estate WordPress best practices — IDX integration, property listings
  - Lead capture — contact forms, CRM integration
  - SEO for real estate
  - Trust signals — testimonials, certifications, team pages
  - Performance and mobile optimization

---

## Research Output Format

For each site, produce a report with:

1. PRIORITY FIXES — Critical issues that need immediate attention
2. QUICK WINS — Low-effort, high-impact improvements
3. STRATEGIC SUGGESTIONS — Longer-term improvements worth planning
4. TOOLS/PLUGINS RECOMMENDED — Specific tools that solve identified problems
5. NEXT STEPS — Concrete actions ranked by priority

---

## How to Run a Research Report

1. Fetch live site data via REST API (where connected)
2. Cross-reference with known issues in this file
3. Web search for best practices, plugin recommendations, and known issues
4. Compile findings into the output format above
5. Present to David with a prioritized action list

---

## Trigger
Run on demand ("research [site name]") or as part of a weekly web dev review.
