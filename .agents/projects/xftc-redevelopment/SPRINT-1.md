# Sprint 1 — Foundation & Core Plugin (Weeks 3–6)

## Sprint Goal
Deliver a working plugin scaffold with activated DB tables, custom user roles, parent-athlete registration, season creation, and basic admin dashboard.

## Tasks

### 1. Plugin Scaffold
- [ ] Create `xftc-membership.php` main plugin file with header, constants, autoloader
- [ ] Set up folder structure per ARCHITECTURE.md
- [ ] Register activation/deactivation hooks
- [ ] Create all DB tables on activation (wpdb->query with dbDelta)

### 2. Custom User Roles
- [ ] Register 5 custom roles: xftc_parent, xftc_athlete, xftc_coach, xftc_admin, xftc_staff
- [ ] Assign capability sets per role
- [ ] Add role management to WP Admin → Users

### 3. Parent Registration Flow
- [ ] Custom registration page (shortcode: [xftc_register])
- [ ] Parent creates account → WP user created (xftc_parent role)
- [ ] Parent can add multiple athlete sub-profiles
- [ ] Athlete profiles saved to wp_xftc_athletes table

### 4. Season Management (Admin)
- [ ] Admin screen: create/edit seasons
- [ ] Fields: name, type, dates, registration open/close, fees
- [ ] List view with active season toggle

### 5. Basic Admin Dashboard
- [ ] WP Admin → Xtreme Force top-level menu
- [ ] Sub-menus: Members, Seasons, Meets, Travel, Payroll, Reports
- [ ] Members list table (searchable, filterable by status/season)

### 6. Transactional Emails
- [ ] Welcome email on parent registration
- [ ] Athlete profile confirmation email

### 7. GitHub Push
- [ ] All Sprint 1 code pushed to dpoly2/AgentHarness under projects/xftc-redevelopment/plugin/

## Definition of Done
- Plugin installs and activates without errors on xtremeforcetrackclub.org
- All DB tables created on activation
- Parent can register and add athlete profiles via front-end
- Admin can view member list and manage seasons
- Emails send on registration

## Assignee
wordpresspluginsagent
