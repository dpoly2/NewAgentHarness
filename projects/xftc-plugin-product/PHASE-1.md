# Phase 1 — De-brandification

**Status:** Not Started
**Goal:** Remove all ts-specific hardcoding and make the plugin fully config-driven
**Prerequisite for:** Every other phase — nothing ships until this is done

---

## Task List

### 1. Audit all hardcoded XFTC strings
- [ ] Grep entire codebase for "xftc", "Xtreme Force", "xtreme-force", hardcoded emails, colors, URLs
- [ ] Document every instance with file + line number
- [ ] Categorize: plugin function prefix | display string | DB table | CSS class | email content

### 2. Create Settings API foundation
- [ ] Register `tracksuite_settings` option group
- [ ] Fields: club_name, club_abbreviation, club_email, club_location, club_domain
- [ ] Add settings page under WP Admin → TrackSuite → Settings
- [ ] Add defaults on plugin activation (pulls from wp_blogname as fallback)

### 3. Replace display strings
- [ ] All PHP template strings using `get_option('tracksuite_club_name')`
- [ ] All email templates using `{club_name}` merge tag
- [ ] All JS strings passed via `wp_localize_script()`

### 4. Rename plugin function prefixes
- [ ] `TRACKSUITE_` → `tracksuite_` for all public functions and hooks
- [ ] `TRACKSUITE_` → `TRACKSUITE_` for all constants
- [ ] `wp_ts_` → `wp_ts_` for all DB table names
- [ ] Add DB migration script for existing XFTC installs

### 5. Theme Customizer panel
- [ ] Register "TrackSuite" Customizer section
- [ ] Primary color picker (default: club's chosen color)
- [ ] Accent color picker
- [ ] Logo upload control
- [ ] Club name + tagline text fields
- [ ] Output as CSS custom properties: `--ts-primary`, `--ts-accent`
- [ ] Replace hardcoded `#1a1a2e` / `#f5a623` in style.css with `var(--ts-primary)` / `var(--ts-accent)`

### 6. CSS class rename
- [ ] `.ts-*` → `.ts-*` throughout plugin and theme CSS/JS
- [ ] Update all PHP view files referencing old class names
- [ ] Update public.js AJAX selectors

### 7. Email template system
- [ ] Create `class-ts-emails.php` with merge tag support
- [ ] Tags: `{club_name}`, `{athlete_name}`, `{parent_name}`, `{season}`, `{meet_name}`
- [ ] Admin-editable email templates (subject + body) stored in DB
- [ ] Fallback to hardcoded defaults if not configured

### 8. DB migration script
- [ ] `class-ts-migrator.php` — detects old `wp_ts_*` tables and renames them
- [ ] One-time migration notice in WP Admin for existing installs
- [ ] Safe rollback if migration fails

---

## Files to Modify

| File | Changes |
|------|---------|
| `ts-membership.php` | Rename to `tracksuite.php`, update headers, prefix all hooks |
| `includes/class-ts-*.php` | Rename files + classes to `class-ts-*.php` |
| `admin/class-ts-admin.php` | Rename + refactor settings page |
| `admin/assets/admin.css` | Replace `.ts-*` with `.ts-*` |
| `public/class-ts-public.php` | Rename + update shortcode tags |
| `public/assets/public.css` | Replace hardcoded colors + class names |
| `public/assets/public.js` | Replace selectors + localized strings |
| `admin/views/*.php` | Replace all display strings |
| `public/views/*.php` | Replace all display strings |
| `api/class-ts-rest-api.php` | Update namespace from `xftc/v1` to `tracksuite/v1` |
| `theme/style.css` | Replace hardcoded colors with CSS vars |
| `theme/functions.php` | Update enqueue handles, add Customizer |

---

## Definition of Done
- [ ] Zero instances of "xftc" or "Xtreme Force" in plugin codebase (except migration script)
- [ ] Fresh install shows generic "Track Club" branding until configured
- [ ] Onboarding prompt appears on first activation
- [ ] Existing XFTC staging install migrates cleanly via migration script
- [ ] All CSS colors driven by Customizer CSS vars
- [ ] All emails use merge tags

---

## Estimated Effort
3–4 days (wordpresspluginsagent)

