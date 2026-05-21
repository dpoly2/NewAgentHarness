# Local Development Setup — AgentHarness Offline Mode
**Date:** 2026-05-20
**Goal:** Run all active projects locally using GitHub Copilot CLI + VS Code so development continues independently of Base44 credits.

---

## What You Have (Already in GitHub)
All project files are at: https://github.com/dpoly2/AgentHarness

- `/projects/xftc-redevelopment/` — XFTC plugin + theme (Sprint 2 verified)
- `/projects/xftc-plugin-product/` — TrackSuite productization roadmap
- `/projects/pbs-foundation/` — Phi Beta Sigma Collegiate Pathways Foundation
- `/projects/yepc/` — Youth Elite Performance Complex
- `/agents/` — All agent profiles and roles

---

## Step 1 — Clone the Repo

```bash
git clone https://github.com/dpoly2/AgentHarness.git
cd AgentHarness
```

---

## Step 2 — Install GitHub Copilot CLI

```bash
# Install GitHub CLI first (if not already installed)
# Mac:
brew install gh

# Windows:
winget install GitHub.cli

# Then authenticate:
gh auth login

# Install Copilot CLI extension:
gh extension install github/gh-copilot

# Verify:
gh copilot --version
```

---

## Step 3 — VS Code Setup (Recommended IDE)

Install these extensions:
- **GitHub Copilot** — AI code completion
- **GitHub Copilot Chat** — inline chat (your primary "agent" interface)
- **PHP Intelephense** — PHP intelligence for WordPress plugin work
- **WordPress Snippets** — WP-specific helpers
- **GitLens** — enhanced Git history

Open the repo:
```bash
code AgentHarness
```

---

## Step 4 — Local WordPress Environment (for plugin testing)

Use **LocalWP** (free, easiest) or **Laragon** (Windows) to run WordPress locally.

### LocalWP (Mac/Windows/Linux):
1. Download from https://localwp.com
2. Create a new site: "tracksuite-dev"
3. PHP 8.1+, MySQL, Apache or Nginx
4. Once created, find the `wp-content/plugins/` path
5. Symlink or copy your plugin there:

```bash
# Mac/Linux — symlink so edits are live:
ln -s /path/to/AgentHarness/projects/xftc-redevelopment/plugin/xftc-membership \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/plugins/xftc-membership

# Windows (run as Admin):
mklink /D "C:\Users\YOU\Local Sites\tracksuite-dev\app\public\wp-content\plugins\xftc-membership" \
  "C:\path\to\AgentHarness\projects\xftc-redevelopment\plugin\xftc-membership"
```

6. Do the same for the theme:
```bash
ln -s /path/to/AgentHarness/projects/xftc-redevelopment/theme/xftc-theme \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/themes/xftc-theme
```

---

## Step 5 — Copilot CLI Workflow (Your New "Agent" Loop)

### Ask Copilot to explain or write code:
```bash
gh copilot suggest "write a WordPress settings API registration function for club name and email"
gh copilot explain "what does this PHP class do"
```

### Use Copilot Chat in VS Code:
- `Ctrl+Shift+I` (or `Cmd+Shift+I`) opens Copilot Chat
- Reference files directly: `@workspace explain the xftc-membership plugin structure`
- Ask it to continue work: `@workspace continue Phase 1 de-brandification — replace all xftc_ prefixes with tracksuite_`

### Copilot inline (while editing a file):
- Start typing a function — Copilot autocompletes
- Add a comment like `// TODO: replace hardcoded club name with get_option()` and Copilot will suggest the fix

---

## Step 6 — Git Workflow (Keep AgentHarness in sync)

```bash
# Always pull latest before starting:
git pull origin main

# Work on a feature branch:
git checkout -b phase1/de-brandification

# Commit as you go:
git add .
git commit -m "Phase 1: replace xftc_ prefix with tracksuite_ in class-xftc-admin.php"

# Push to GitHub:
git push origin phase1/de-brandification

# Merge when done:
git checkout main
git merge phase1/de-brandification
git push origin main
```

---

## Step 7 — Project Priorities (Pick Up Where We Left Off)

Work these in order:

### XFTC + TrackSuite (most active)
1. **Phase 1 — De-brandification** (`projects/xftc-plugin-product/PHASE-1.md`)
   - Grep codebase for all `xftc_` strings
   - Replace with `tracksuite_` + Settings API
   - Add WP Customizer color picker
2. **Stripe integration** — add live keys to staging, run `composer require stripe/stripe-php` on staging server
3. **Admin dashboard widgets** — wire up existing stubs in `admin/views/dashboard.php`
4. **Coach/Staff front-end portal** — so non-admins never touch WP Admin

### Phi Beta Sigma Foundation
- File 501(c)(3) with IRS (Form 1023-EZ if under $50K projected revenue)
- Recruit board of directors
- Files: `projects/pbs-foundation/`

### YEPC / Smith Capital
- Monitor Hutto EDC response (outreach sent — follow up May 25)
- Track OZ 2.0 nomination deadline: **June 26, 2026**
- Files: `projects/yepc/`

---

## Copilot Prompt Templates (Save These)

Use these in Copilot Chat to continue work exactly where we left off:

```
@workspace I'm building a WordPress plugin called TrackSuite (formerly xftc-membership). 
Read the PROJECT.md in projects/xftc-plugin-product/ and continue Phase 1 de-brandification. 
Start by grepping all xftc_ prefixes in the plugin directory and replacing them with tracksuite_.
```

```
@workspace Review SPRINT-2.md in projects/xftc-redevelopment/ and begin Sprint 3. 
Priority: wire the admin dashboard widgets in admin/views/dashboard.php.
```

```
@workspace Read projects/pbs-foundation/CHARTER.md and BYLAWS.md. 
Help me prepare the IRS Form 1023-EZ application for the Phi Beta Sigma Collegiate Pathways Foundation.
```

---

## Staging Site Access (Still Available)
- **URL:** https://staging.s2tdesigns.com
- **WP Admin:** https://staging.s2tdesigns.com/wp-admin
- **User:** agent_design
- **Pass:** yK#jR7ScYjbk#@M#8A#356dp

## Live XFTC Site Access
- **URL:** https://xtremeforcetrackclub.org/wp-admin
- **User:** dsmith
- **App Password:** PvCp LL4V X1BJ xxcj ei2z i6pB

---

## When Credits Refresh
Come back here and I'll pick up exactly where Copilot left off. All state is in GitHub — nothing is lost.

---

## Summary of Everything Built So Far
| Project | Status | Next Step |
|---------|--------|-----------|
| XFTC Membership Plugin v2.0.0 | ✅ Sprint 2 verified | Stripe keys + Sprint 3 |
| XFTC Standalone Theme v1.0.0 | ✅ Complete | Production deploy |
| TrackSuite Product Roadmap | ✅ Planned | Phase 1 execution |
| Phi Beta Sigma Foundation | ✅ Charter + Bylaws done | 501(c)(3) filing |
| YEPC / CR 132 Site | ✅ Research + outreach done | Hutto EDC follow-up May 25 |
| AgentHarness GitHub Repo | ✅ Synced | Daily auto-sync active |
