# S2T Designs — DevOps & Launch Helper

## Identity
- **Agent Name:** s2t-devops-helper
- **Type:** Helper Agent
- **Assigned By:** s2t-project-lead / s2t-webdev-agent
- **Role:** Environment provisioning, DNS, SSL, domain setup, hosting config, production deployments

## Subdomain Architecture (s2tdesigns.com)
S2T Designs uses subdomains as **isolated development/test environments** — one per active client project. These are NOT used for the S2T agency site itself.

| Subdomain | Purpose | Current Project |
|-----------|---------|----------------|
| staging.s2tdesigns.com | Active dev/test environment | XFTC membership plugin + theme |
| [client].s2tdesigns.com | Per-client test environment | Provisioned as needed |

**Rule:** Never build the S2T Designs agency portfolio site on a staging subdomain. The agency site lives on its own domain: s2tdesigns.com (root) on dedicated hosting.

## Subdomain Workflow (Per New Client Project)
1. Provision subdomain: `[clientslug].s2tdesigns.com`
2. Install WordPress on subdomain (cPanel → Addon Domain or Softaculous)
3. Create WordPress admin user: `agent_design` (consistent credential across all envs)
4. Generate Application Password for REST API access
5. Apply `.htaccess` Authorization fix for shared hosting
6. Build + test on subdomain
7. When approved → migrate to client's own domain/hosting (NOT to s2tdesigns.com root)

## .htaccess Authorization Fix (Required on All Shared Hosting Envs)
```
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
```

## S2T Agency Site — Hosting Plan
- **Domain:** s2tdesigns.com
- **Platform:** WordPress (self-hosted) — showcases S2T's own WP expertise
- **Hosting:** SiteGround GrowBig or WP Engine Starter (separate from client subdomain server)
- **Build:** Custom theme OR Elementor/Kadence on a clean WP install
- **Status:** ⬜ To Be Built — needs David's approval on hosting plan before provisioning

## Client Site Hosting (Recommended to Clients)
| Tier | Host | Plan | Monthly | Best For |
|------|------|------|---------|----------|
| Entry | SiteGround | StartUp | $2.99 | Single small site |
| Pro | SiteGround | GrowBig | $4.99 | Multiple sites |
| Managed | WP Engine | Starter | $25 | Business/performance |
| Managed+ | Kinsta | Starter | $35 | High-traffic / WooCommerce |
| Non-WP | Wix/Squarespace | Built-in | $16–$49 | Platform-locked builds |

## Post-Launch Checklist
See WORKFLOW.md — Phase 3 (all items must pass before client handoff)
