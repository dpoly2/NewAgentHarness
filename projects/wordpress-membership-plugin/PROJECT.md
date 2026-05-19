# Project: Custom WordPress Membership Plugin

## Overview
Build a custom WordPress plugin to manage club/org memberships directly within WordPress — tailored for Xtreme Force Track Club and potentially reusable across other David Smith properties.

## Goals
- Replace or extend existing manual registration/payment workflow
- Member registration, profiles, and renewal management
- Payment integration (Stripe)
- Member portal (login-protected dashboard)
- Admin dashboard for managing members, statuses, and payments
- Email notifications (welcome, renewal reminders, payment receipts)

## Target Sites
- xtremeforcetrackclub.org (primary)
- Potentially: psibetasigma1914.org, smithcapitalproperties.com

## Tech Stack
- WordPress Plugin (PHP)
- Custom Post Types (Members)
- Gravity Forms integration (existing forms)
- Stripe for payments
- WP REST API for agent interaction
- Shortcodes + Gutenberg blocks for front-end display

## Status
🟡 Planning — Agent assigned, project initialized

## Agent
**wordpresspluginsagent** — see `agents/wordpresspluginsagent.md`

## Milestones
- [ ] Requirements finalization
- [ ] Plugin scaffold / boilerplate
- [ ] Member registration flow
- [ ] Payment integration (Stripe)
- [ ] Member portal (front-end)
- [ ] Admin dashboard
- [ ] Testing & QA
- [ ] Deployment to xtremeforcetrackclub.org

## Files
- `PROJECT.md` — This file
- `requirements.md` — Detailed feature requirements
- `plugin-scaffold/` — Plugin source code (PHP)
