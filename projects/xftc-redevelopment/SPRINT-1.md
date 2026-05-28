# Sprint 1 — Foundation & Core Plugin (Weeks 3–6)

## Sprint Goal
Deliver a working plugin scaffold with activated DB tables, custom user roles, parent-athlete registration, season creation, and basic admin dashboard.

## Tasks

### 1. Plugin Scaffold
- [ ] Create `ts-membership.php` main plugin file with header, constants, autoloader
- [ ] Set up folder structure per ARCHITECTURE.md
- [ ] Register activation/deactivation hooks
- [ ] Create all DB tables on activation (wpdb->query with dbDelta)

### 2. Custom User Roles
- [ ] Register 5 custom roles: TRACKSUITE_parent, TRACKSUITE_athlete, TRACKSUITE_coach, TRACKSUITE_admin, TRACKSUITE_staff
- [ ] Assign capability sets per role
- [ ] Add role management to WP Admin → Users

### 3. Parent Registration Flow
- [ ] Custom registration page (shortcode: [TRACKSUITE_register])
- [ ] Parent creates account → WP user created (TRACKSUITE_parent role)
- [ ] Parent can add multiple athlete sub-profiles
- [ ] Athlete profiles saved to wp_ts_athletes table

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
- [ ] All Sprint 1 code pushed to dpoly2/AgentHarness under projects/ts-redevelopment/plugin/

## Definition of Done
- Plugin installs and activates without errors on xtremeforcetrackclub.org
- All DB tables created on activation
- Parent can register and add athlete profiles via front-end
- Admin can view member list and manage seasons
- Emails send on registration

## Assignee
wordpresspluginsagent

