# XFTC Membership Plugin

**Version:** 2.0.0
**Last Updated:** May 20, 2026
**Status:** Sprint 2 Complete ✅ — Staging verified, production deploy pending

---

## Overview

The `xftc-membership` WordPress plugin is the data and business logic engine for the Xtreme Force Track Club web ecosystem. It is fully decoupled from the display layer — the companion `xftc-theme` handles all front-end rendering via shortcodes provided by this plugin.

---

## Architecture

```
xftc-membership/
├── xftc-membership.php          # Bootstrap — registers hooks, loads classes
├── includes/
│   ├── class-xftc-activator.php     # DB table creation on plugin activation
│   ├── class-xftc-deactivator.php   # Cleanup on deactivation
│   ├── class-xftc-roles.php         # Custom WP user roles
│   ├── class-xftc-members.php       # Athlete/member CRUD
│   ├── class-xftc-registration.php  # Parent + athlete registration logic
│   ├── class-xftc-seasons.php       # Season management
│   ├── class-xftc-meets.php         # Meet scheduling
│   ├── class-xftc-results.php       # Athlete results tracking
│   ├── class-xftc-travel.php        # Travel manifest management
│   ├── class-xftc-payroll.php       # Coach/staff payroll
│   ├── class-xftc-payments.php      # Payment tracking
│   └── class-xftc-emails.php        # Transactional email system
├── admin/
│   ├── class-xftc-admin.php         # WP Admin panel registration
│   ├── assets/admin.css             # Admin styles
│   └── views/                       # WP Admin view templates
│       ├── dashboard.php
│       ├── members.php
│       ├── seasons.php
│       ├── meets.php
│       ├── results.php
│       ├── payments.php
│       ├── payroll.php
│       ├── travel.php
│       └── settings.php
├── public/
│   ├── class-xftc-public.php        # Shortcode registration + AJAX handlers
│   ├── assets/
│   │   ├── public.css               # Front-end styles
│   │   └── public.js                # AJAX, multi-step form, portal JS
│   └── views/                       # Shortcode output templates
│       ├── register.php             # Multi-step registration form
│       ├── portal.php               # Parent dashboard (tabbed)
│       ├── meets.php                # Meet schedule display
│       ├── results.php              # Athlete results display
│       ├── checkout.php             # Stripe checkout view
│       └── receipts.php             # Payment receipt view
└── api/
    └── class-xftc-rest-api.php      # WP REST API endpoints
```

---

## Database Tables

All tables use the `wp_xftc_` prefix:

| Table | Purpose |
|-------|---------|
| `wp_xftc_athletes` | Athlete records linked to parent WP users |
| `wp_xftc_seasons` | Season definitions, dates, and pricing tiers |
| `wp_xftc_meets` | Track meet events |
| `wp_xftc_meet_registrations` | Athlete-to-meet enrollment |
| `wp_xftc_results` | Athlete performance results |
| `wp_xftc_payments` | Registration and payment records |
| `wp_xftc_travel` | Travel manifests |
| `wp_xftc_payroll` | Coach/staff payroll entries |

---

## User Roles

| Role | Capabilities |
|------|-------------|
| `xftc_parent` | Register athletes, view portal, manage own athletes |
| `xftc_athlete` | View own results and schedule |
| `xftc_coach` | Manage meets, enter results |
| `xftc_staff` | Manage travel, payroll |
| `xftc_admin` | Full access to all XFTC admin panels |

---

## Shortcodes

| Shortcode | Description |
|-----------|-------------|
| `[xftc_register_form]` | Multi-step parent + athlete registration (4 steps) |
| `[xftc_portal]` | Tabbed parent dashboard |
| `[xftc_my_athletes]` | Logged-in parent's athlete list |
| `[xftc_my_results]` | Athlete results for logged-in parent |
| `[xftc_my_payments]` | Payment history for logged-in parent |
| `[xftc_my_travel]` | Travel manifest for logged-in parent |
| `[xftc_meets]` | Public meet schedule |
| `[xftc_results]` | Public results board |
| `[xftc_roster]` | Public team roster |
| `[xftc_checkout]` | Stripe checkout (requires Stripe keys) |
| `[xftc_receipts]` | Payment receipts |
| `[xftc_login_form]` | Parent login form |

---

## AJAX Endpoints

| Action | Handler | Description |
|--------|---------|-------------|
| `xftc_register_athlete` | `ajax_register_athlete()` | Full registration — creates WP user + athlete record |
| `xftc_login` | `ajax_login()` | Parent portal login |
| `xftc_register_for_meet` | `ajax_register_for_meet()` | Enroll athlete in a meet |
| `xftc_get_chart_data` | `ajax_get_chart_data()` | Portal performance chart data |

---

## Sprint History

### Sprint 1 — Core Foundation ✅
- Plugin bootstrap and activation
- Database schema (10 tables)
- Custom user roles (5 roles)
- Base CRUD: members, seasons

### Sprint 2 — Feature Modules ✅
- Meet management (scheduling, enrollment)
- Athlete results tracking
- Travel manifest system
- Coach/staff payroll
- Stripe payment placeholder
- Multi-step registration form (4 steps)
- Parent portal (tabbed dashboard)
- Plugin/theme decoupling via shortcodes
- Bug fix: `send_parent_welcome()` method corrected

### Sprint 3 — Production Ready 🔜
- Stripe live key integration
- Coach/staff front-end portal (no WP Admin needed)
- Production deployment to xtremeforcetrackclub.org
- End-to-end QA and load testing

---

## Deployment

**Staging:** https://staging.s2tdesigns.com
**Production:** https://xtremeforcetrackclub.org (pending Sprint 3)

To install: upload the plugin folder to `/wp-content/plugins/xftc-membership/` and activate via WP Admin > Plugins.

After activation:
1. Go to **Settings > XFTC Settings** and enter Stripe API keys
2. Flush permalinks: Settings > Permalinks > Save Changes
3. Assign the `[xftc_register_form]` shortcode to the `/register/` page
4. Assign the `[xftc_portal]` shortcode to the `/portal/` page
