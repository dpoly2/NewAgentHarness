# Local Development Setup — AgentHarness Offline Mode
**Date:** 2026-05-20
**Goal:** Run all active projects locally using GitHub Copilot CLI + VS Code so development continues independently of Base44 credits.

---

## What You Have (Already in GitHub)
All project files are at: https://github.com/dpoly2/AgentHarness

- `/projects/ts-redevelopment/` — XFTC plugin + theme (Sprint 2 verified)
- `/projects/ts-plugin-product/` — TrackSuite productization roadmap
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
ln -s /path/to/AgentHarness/projects/ts-redevelopment/plugin/ts-membership \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/plugins/ts-membership

# Windows (run as Admin):
mklink /D "C:\Users\YOU\Local Sites\tracksuite-dev\app\public\wp-content\plugins\ts-membership" \
  "C:\path\to\AgentHarness\projects\ts-redevelopment\plugin\ts-membership"
```

6. Do the same for the theme:
```bash
ln -s /path/to/AgentHarness/projects/ts-redevelopment/theme/ts-theme \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/themes/ts-theme
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
- Reference files directly: `@workspace explain the ts-membership plugin structure`
- Ask it to continue work: `@workspace continue Phase 1 de-brandification — replace all TRACKSUITE_ prefixes with tracksuite_`

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
git commit -m "Phase 1: replace TRACKSUITE_ prefix with tracksuite_ in class-ts-admin.php"

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
1. **Phase 1 — De-brandification** (`projects/ts-plugin-product/PHASE-1.md`)
   - Grep codebase for all `TRACKSUITE_` strings
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

Use these in Copilot Chat to continue work exactly where we left off. Replace any <placeholders> before running.

### Local Dev Setup (Copilot Chat Template)

```
@workspace
You are my Local Development Assistant. Goal: set up a reproducible, offline LocalWP development site for this repository and verify the site runs in VS Code + LocalWP + Git.
Context:
- Repo path: D:\Projects\agentharness
- Editor: VS Code (with GitHub Copilot Chat installed)
- Local WP app: Local by Flywheel (Local)

Tasks (perform or provide exact Windows commands):
1) Confirm repository files exist at the path above.
2) Create a Local site named "agentharness-local" that maps to the project's public webroot (if the repo has a WordPress public folder, use it; otherwise create a new WP site and explain where to copy plugin/theme files).
   - Provide precise Local UI steps and the equivalent powershell/winget/Local CLI commands (if available).
3) Symlink plugin and theme directories from the repo into the Local site's wp-content (Windows mklink /D example required).
4) Ensure runtime tools are present (PHP, Composer, Node). If missing, provide winget commands to install them.
5) Run dependency installs for the project (composer install / npm ci) with commands and expected outputs.
6) Start the Local site, open WP Admin, activate the theme and plugin, and flush permalinks. Provide exact steps and commands.
7) Run basic verification: request the home page, check WP admin reachable, list active plugins and theme, and report any PHP errors (how to find logs).
8) If any manual steps are required (GUI sign-in, database import), output a concise checklist and the exact files/paths to use.

End by listing the commands run, files changed (or created), and a suggested git commit message to record the setup (e.g., "chore: add local dev site and symlinks").
```

---

### Project-specific Quick Prompts

```
@workspace I'm building a WordPress plugin called TrackSuite (formerly ts-membership).
Read the PROJECT.md in projects/ts-plugin-product/ and continue Phase 1 de-brandification.
Start by grepping all TRACKSUITE_ prefixes in the plugin directory and replacing them with tracksuite_.
```

```
@workspace Review SPRINT-2.md in projects/ts-redevelopment/ and begin Sprint 3.
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

