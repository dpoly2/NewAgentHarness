# XFTC Theme

**Version:** 1.0.0
**Last Updated:** May 20, 2026
**Status:** Deployed to staging ✅

---

## Overview

`xftc-theme` is the standalone WordPress theme for Xtreme Force Track Club. It handles all front-end presentation and is fully decoupled from the data layer — all dynamic content is rendered via shortcodes provided by the `xftc-membership` plugin.

The theme degrades gracefully if the plugin is inactive, displaying fallback messages instead of breaking.

---

## File Structure

```
xftc-theme/
├── style.css              # Theme header + base styles
├── theme.json             # Block editor / FSE settings
├── functions.php          # Theme setup, script/style enqueuing
├── index.php              # Fallback template
├── front-page.php         # Homepage template
├── header.php             # Site header
├── footer.php             # Site footer
├── page.php               # Default page template
├── single.php             # Single post template
├── 404.php                # Custom 404 ("FALSE START.")
├── inc/
│   ├── nav-walker.php     # Custom Bootstrap-compatible nav walker
│   └── template-tags.php  # Reusable template helpers
├── assets/
│   └── js/
│       └── theme.js       # Theme JS (nav, misc interactions)
└── templates/
    ├── register.php        # Registration page → [xftc_register_form]
    ├── portal.php          # Parent portal → [xftc_portal]
    ├── schedule.php        # Meet schedule → [xftc_meets]
    ├── results.php         # Results board → [xftc_results]
    ├── roster.php          # Team roster → [xftc_roster]
    └── parts/
        ├── header.php      # Reusable header partial
        └── footer.php      # Reusable footer partial
```

---

## Page Templates

| Template | Shortcode Used | URL |
|----------|---------------|-----|
| `register.php` | `[xftc_register_form]` | `/register/` |
| `portal.php` | `[xftc_portal]` | `/portal/` |
| `schedule.php` | `[xftc_meets]` | `/schedule/` |
| `results.php` | `[xftc_results]` | `/results/` |
| `roster.php` | `[xftc_roster]` | `/roster/` |

---

## Design System

- **Primary color:** `#0D1B2A` (navy)
- **Accent color:** `#F5A623` (XFTC gold)
- **Font:** System sans-serif stack
- **Custom 404:** Athletic theme with "FALSE START." message

---

## Dependencies

- WordPress 6.0+
- `xftc-membership` plugin (for all dynamic content)
- PHP 8.0+

---

## Deployment

To install: upload the `xftc-theme/` folder to `/wp-content/themes/` and activate via WP Admin > Appearance > Themes.

After activation:
1. Flush permalinks: Settings > Permalinks > Save Changes
2. Assign template pages: Register, Portal, Schedule, Results, Roster
3. Configure menus in WP Admin > Appearance > Menus
