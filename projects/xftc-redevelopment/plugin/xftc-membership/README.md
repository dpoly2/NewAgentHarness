# XFTC Membership Plugin

**Version:** 2.0.0
**Last Updated:** May 20, 2026
**Status:** Sprint 2 Complete ✅ — Staging verified, production deploy pending

---

## Overview

The `ts-membership` WordPress plugin is the data and business logic engine for the Xtreme Force Track Club web ecosystem. It is fully decoupled from the display layer — the companion `ts-theme` handles all front-end rendering via shortcodes provided by this plugin.

---

## Architecture

```
ts-membership/
├── ts-membership.php          # Bootstrap — registers hooks, loads classes
├── includes/
│   ├── class-ts-activator.php     # DB table creation on plugin activation
│   ├── class-ts-deactivator.php   # Cleanup on deactivation
│   ├── class-ts-roles.php         # Custom WP user roles
│   ├── class-ts-members.php       # Athlete/member CRUD
│   ├── class-ts-registration.php  # Parent + athlete registration logic
│   ├── class-ts-seasons.php       # Season management
│   ├── class-ts-meets.php         # Meet scheduling
│   ├── class-ts-results.php       # Athlete results tracking
│   ├── class-ts-travel.php        # Travel manifest management
│   ├── class-ts-payroll.php       # Coach/staff payroll
│   ├── class-ts-payments.php      # Payment tracking
│   └── class-ts-emails.php        # Transactional email system
├── admin/
│   ├── class-ts-admin.php         # WP Admin panel registration
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
│   ├── class-ts-public.php        # Shortcode registration + AJAX handlers
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
    └── class-ts-rest-api.php      # WP REST API endpoints
```

---

## Database Tables

All tables use the `wp_ts_` prefix:

| Table | Purpose |
|-------|---------|
| `wp_ts_athletes` | Athlete records linked to parent WP users |
| `wp_ts_seasons` | Season definitions, dates, and pricing tiers |
| `wp_ts_meets` | Track meet events |
| `wp_ts_meet_registrations` | Athlete-to-meet enrollment |
| `wp_ts_results` | Athlete performance results |
| `wp_ts_payments` | Registration and payment records |
| `wp_ts_travel` | Travel manifests |
| `wp_ts_payroll` | Coach/staff payroll entries |

---

## User Roles

| Role | Capabilities |
|------|-------------|
| `TRACKSUITE_parent` | Register athletes, view portal, manage own athletes |
| `TRACKSUITE_athlete` | View own results and schedule |
| `TRACKSUITE_coach` | Manage meets, enter results |
| `TRACKSUITE_staff` | Manage travel, payroll |
| `TRACKSUITE_admin` | Full access to all XFTC admin panels |

---

## Shortcodes

| Shortcode | Description |
|-----------|-------------|
| `[TRACKSUITE_register_form]` | Multi-step parent + athlete registration (4 steps) |
| `[TRACKSUITE_portal]` | Tabbed parent dashboard |
| `[TRACKSUITE_my_athletes]` | Logged-in parent's athlete list |
| `[TRACKSUITE_my_results]` | Athlete results for logged-in parent |
| `[TRACKSUITE_my_payments]` | Payment history for logged-in parent |
| `[TRACKSUITE_my_travel]` | Travel manifest for logged-in parent |
| `[TRACKSUITE_meets]` | Public meet schedule |
| `[TRACKSUITE_results]` | Public results board |
| `[TRACKSUITE_roster]` | Public team roster |
| `[TRACKSUITE_checkout]` | Stripe checkout (requires Stripe keys) |
| `[TRACKSUITE_receipts]` | Payment receipts |
| `[TRACKSUITE_login_form]` | Parent login form |

---

## AJAX Endpoints

| Action | Handler | Description |
|--------|---------|-------------|
| `TRACKSUITE_register_athlete` | `ajax_register_athlete()` | Full registration — creates WP user + athlete record |
| `TRACKSUITE_login` | `ajax_login()` | Parent portal login |
| `TRACKSUITE_register_for_meet` | `ajax_register_for_meet()` | Enroll athlete in a meet |
| `TRACKSUITE_get_chart_data` | `ajax_get_chart_data()` | Portal performance chart data |

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

To install: upload the plugin folder to `/wp-content/plugins/ts-membership/` and activate via WP Admin > Plugins.

After activation:
1. Go to **Settings > XFTC Settings** and enter Stripe API keys
2. Flush permalinks: Settings > Permalinks > Save Changes
3. Assign the `[TRACKSUITE_register_form]` shortcode to the `/register/` page
4. Assign the `[TRACKSUITE_portal]` shortcode to the `/portal/` page

