# Local Development Setup — Full Guide
**AgentHarness Offline Mode | Copilot CLI + LocalWP + VS Code**
**Last Updated:** 2026-05-20

---

## Overview

This guide sets up your complete local development environment so you can continue all active projects — XFTC plugin, TrackSuite productization, Rowdy Crown, YEPC, and Phi Beta Sigma Foundation — without needing Base44 credits.

**Stack:**
- **GitHub** — single source of truth for all project files
- **LocalWP** — local WordPress environment for plugin/theme development
- **VS Code** — primary IDE
- **GitHub Copilot Chat** — your AI agent inside VS Code
- **GitHub Copilot CLI** — AI assistant in your terminal

---

## Part 1 — GitHub Setup

### 1.1 — Install Git (if not already installed)

**Mac:**
```bash
# Check if installed
git --version

# If not installed:
brew install git

# Or install Xcode command line tools:
xcode-select --install
```

**Windows:**
- Download from https://git-scm.com/download/win
- Install with default options
- Choose "Git from the command line and also from 3rd-party software"
- Choose VS Code as your default editor when prompted

**Verify:**
```bash
git --version
# Should return: git version 2.x.x
```

### 1.2 — Configure Git Identity

```bash
git config --global user.name "David Smith"
git config --global user.email "smithda.ii@gmail.com"
git config --global core.editor "code --wait"
git config --global init.defaultBranch main
```

### 1.3 — Authenticate with GitHub

```bash
# Install GitHub CLI
# Mac:
brew install gh

# Windows:
winget install GitHub.cli

# Authenticate (opens browser):
gh auth login
# Choose: GitHub.com → HTTPS → Yes (authenticate with browser) → Login
```

### 1.4 — Clone AgentHarness

```bash
# Navigate to where you want the folder (e.g., your Documents or Desktop)
cd ~/Documents

# Clone the repo
git clone https://github.com/dpoly2/AgentHarness.git

# Move into it
cd AgentHarness

# Verify structure
ls projects/
# Should show: local-dev-setup  pbs-foundation  rowdy-crown  xftc-plugin-product  xftc-redevelopment  yepc
```

---

## Part 2 — VS Code Setup

### 2.1 — Install VS Code

Download from https://code.visualstudio.com
- Windows: run the installer, check "Add to PATH" during setup
- Mac: drag to Applications, then run:

```bash
# Add VS Code to terminal PATH (Mac only)
# Open VS Code → Cmd+Shift+P → type "shell command" → click "Install 'code' command in PATH"
```

### 2.2 — Open the Project

```bash
# From terminal, inside the cloned repo:
code .
```

VS Code opens with your entire AgentHarness folder in the sidebar.

### 2.3 — Install Essential Extensions

Open the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`) and install these:

| Extension | Publisher | Why |
|-----------|-----------|-----|
| **GitHub Copilot** | GitHub | AI code completion as you type |
| **GitHub Copilot Chat** | GitHub | Chat interface — your offline agent |
| **PHP Intelephense** | Ben Mewburn | PHP intelligence, autocomplete, error detection |
| **WordPress Snippets** | wpprofit | WP-specific function snippets |
| **GitLens** | GitKraken | Visual git history, blame, branch management |
| **Prettier** | Prettier | Code formatting |
| **Auto Rename Tag** | Jun Han | Renames HTML/PHP closing tags automatically |
| **Path Intellisense** | Christian Kohler | Autocompletes file paths in PHP includes |
| **Thunder Client** | Thunder Client | Built-in REST API tester (replaces Postman) |
| **Markdown All in One** | Yu Zhang | Preview and edit your .md project files |

**Install all at once via terminal:**
```bash
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
code --install-extension bmewburn.vscode-intelephense-client
code --install-extension wpprofit.wordpress-snippets
code --install-extension eamodio.gitlens
code --install-extension esbenp.prettier-vscode
code --install-extension formulahendry.auto-rename-tag
code --install-extension christian-kohler.path-intellisense
code --install-extension rangav.vscode-thunder-client
code --install-extension yzhang.markdown-all-in-one
```

### 2.4 — Sign Into Copilot

1. Click the Copilot icon in the bottom status bar (or the chat icon in the sidebar)
2. Click "Sign in to GitHub"
3. Browser opens → authorize → return to VS Code
4. Copilot icon should turn solid (not grayed out)

**Requires:** GitHub Copilot subscription ($10/month or included with GitHub Pro/Teams)

### 2.5 — VS Code Settings (Recommended)

Open settings (`Ctrl+,` / `Cmd+,`) and set these, or add to `settings.json` (`Ctrl+Shift+P` → "Open User Settings JSON"):

```json
{
  "editor.fontSize": 14,
  "editor.tabSize": 4,
  "editor.formatOnSave": true,
  "editor.wordWrap": "on",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "php.validate.executablePath": "/usr/bin/php",
  "intelephense.stubs": [
    "wordpress",
    "mysqli",
    "json",
    "curl"
  ],
  "github.copilot.enable": {
    "*": true,
    "php": true,
    "markdown": true
  },
  "git.autofetch": true,
  "git.confirmSync": false,
  "gitlens.hovers.currentLine.over": "line"
}
```

---

## Part 3 — LocalWP Setup (WordPress Local Environment)

### 3.1 — Install LocalWP

Download from https://localwp.com (free, no account required)
- Available for Mac, Windows, Linux
- Install and launch

### 3.2 — Create Your Dev Site

1. Click **"+ Create a new site"**
2. Site name: `tracksuite-dev` (or `xftc-dev`)
3. Click **"Custom"** environment:
   - PHP: **8.1** or **8.2**
   - Web server: **Nginx** (preferred) or Apache
   - Database: MySQL 8.0
4. Set WordPress username/password:
   - Username: `admin`
   - Password: `admin` (local only — doesn't matter)
   - Email: your email
5. Click **"Add Site"** — LocalWP installs WordPress automatically

### 3.3 — Find Your Site's File Path

In LocalWP, click your site → click **"Go to site folder"**

The path will be something like:
- **Mac:** `~/Local Sites/tracksuite-dev/app/public/`
- **Windows:** `C:\Users\David\Local Sites\tracksuite-dev\app\public\`

Your WordPress root is in `app/public/`. Plugins live in `app/public/wp-content/plugins/`.

### 3.4 — Symlink the Plugin (Live Editing — No Copy/Paste Needed)

A symlink means edits in VS Code instantly appear in LocalWP — no manual copying.

**Mac/Linux:**
```bash
# Replace the path with YOUR actual Local Sites path
ln -s ~/Documents/AgentHarness/projects/xftc-redevelopment/plugin/xftc-membership \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/plugins/xftc-membership

# Verify it worked:
ls ~/Local\ Sites/tracksuite-dev/app/public/wp-content/plugins/
# Should show: xftc-membership (with an arrow → indicating symlink)
```

**Windows (run PowerShell as Administrator):**
```powershell
New-Item -ItemType SymbolicLink `
  -Path "C:\Users\David\Local Sites\tracksuite-dev\app\public\wp-content\plugins\xftc-membership" `
  -Target "C:\Users\David\Documents\AgentHarness\projects\xftc-redevelopment\plugin\xftc-membership"
```

### 3.5 — Symlink the Theme

```bash
# Mac/Linux:
ln -s ~/Documents/AgentHarness/projects/xftc-redevelopment/theme/xftc-theme \
  ~/Local\ Sites/tracksuite-dev/app/public/wp-content/themes/xftc-theme

# Windows PowerShell (as Admin):
New-Item -ItemType SymbolicLink `
  -Path "C:\Users\David\Local Sites\tracksuite-dev\app\public\wp-content\themes\xftc-theme" `
  -Target "C:\Users\David\Documents\AgentHarness\projects\xftc-redevelopment\theme\xftc-theme"
```

### 3.6 — Activate Plugin + Theme in WordPress

1. In LocalWP, click **"WP Admin"** button (opens browser to local WP Admin)
2. Go to **Plugins → Installed Plugins** → activate **xftc-membership**
3. Go to **Appearance → Themes** → activate **xftc-theme**
4. Go to **Settings → Permalinks** → click **Save Changes** (flushes rewrite rules)

### 3.7 — Install Composer (for Stripe PHP SDK)

Composer is PHP's package manager — needed to install Stripe.

**Mac:**
```bash
brew install composer
# Verify:
composer --version
```

**Windows:**
- Download installer: https://getcomposer.org/Composer-Setup.exe
- Run installer — it finds PHP automatically if LocalWP is running
- Verify in a new terminal: `composer --version`

**Install Stripe SDK in the plugin:**
```bash
cd ~/Documents/AgentHarness/projects/xftc-redevelopment/plugin/xftc-membership
composer require stripe/stripe-php
```

---

## Part 4 — GitHub Copilot CLI

### 4.1 — Install

```bash
# Requires gh CLI (already installed in Part 1)
gh extension install github/gh-copilot

# Verify:
gh copilot --version
```

### 4.2 — Core Commands

```bash
# Ask Copilot to suggest a shell command
gh copilot suggest "find all PHP files in the plugin directory that contain the string xftc_"

# Ask Copilot to explain a command
gh copilot explain "grep -r 'xftc_' ./plugin --include='*.php' -l"

# Use aliases for speed (add to your ~/.bashrc or ~/.zshrc):
echo 'alias gcs="gh copilot suggest"' >> ~/.zshrc
echo 'alias gce="gh copilot explain"' >> ~/.zshrc
source ~/.zshrc

# Now use:
gcs "rename all PHP class files from class-xftc-*.php to class-ts-*.php"
```

### 4.3 — Useful CLI Prompts for This Project

```bash
# Find all hardcoded XFTC strings (Phase 1 de-brandification)
gcs "grep recursively for xftc_, XFTC, Xtreme Force in the plugin folder, output file names and line numbers"

# Rename files in bulk
gcs "rename all files matching class-xftc-*.php to class-ts-*.php in current directory"

# Check PHP syntax on all plugin files
gcs "run php -l on every .php file in the current directory and show only errors"

# Push all changes to GitHub
gcs "git add all changes, commit with a message, and push to origin main"
```

---

## Part 5 — Copilot Chat in VS Code (Your Offline Agent)

This is your primary "agent" interface when offline. Copilot Chat knows your entire codebase.

### 5.1 — Open Copilot Chat

- Click the **chat bubble icon** in the left sidebar
- Or: `Ctrl+Shift+I` (Windows) / `Cmd+Shift+I` (Mac)

### 5.2 — Copilot Chat Participants

These prefixes focus Copilot on specific scopes:

| Prefix | What It Does |
|--------|-------------|
| `@workspace` | Searches your entire open folder — use this most |
| `@vscode` | VS Code settings and commands |
| `#file:filename.php` | Reference a specific file in your question |
| `#selection` | Ask about highlighted code |

### 5.3 — Master Prompt Templates (Copy-Paste Ready)

**XFTC Plugin — Continue Sprint 3:**
```
@workspace I'm continuing development on the XFTC membership WordPress plugin.
Read projects/xftc-redevelopment/SPRINT-2.md — specifically the "Sprint 3 carry-forward" 
section at the bottom. The plugin files are in projects/xftc-redevelopment/plugin/xftc-membership/.
Sprint 3 priorities:
1. Wire admin dashboard widgets in admin/views/dashboard.php
2. Build Coach/Staff front-end portal so they don't need WP Admin
3. Integrate Stripe once I add the API keys to plugin settings

Start with task 1 — show me the dashboard widget code.
```

**TrackSuite — Phase 1 De-brandification:**
```
@workspace I'm starting Phase 1 of the TrackSuite productization project.
Read projects/xftc-plugin-product/PHASE-1.md for the full task list.
The plugin source is in projects/xftc-redevelopment/plugin/xftc-membership/.

Step 1: Search every PHP file in the plugin for occurrences of "xftc_", "XFTC_", 
"Xtreme Force", and hardcoded colors (#1a1a2e, #f5a623).
Give me a complete list: filename, line number, current value, what it should be replaced with.
```

**Rowdy Crown — Research Agent:**
```
@workspace I am the Rowdy Crown Research Agent. Read projects/rowdy-crown/PROJECT.md 
and projects/rowdy-crown/agents/research-agent.md.

The target site is 15119 N IH-35 Service Rd, Pflugerville, TX 78660 (former Bombshells).
Smith Capital Properties (owner: David Smith) is evaluating acquisition.

This week:
1. What do I need to research to determine if this site is viable for a nightclub?
2. What are the TABC Mixed Beverage Permit requirements for Texas?
3. What Austin/Pflugerville demographic data should I pull to validate the market?

Give me a structured research plan with specific data sources and URLs.
```

**Rowdy Crown — Business Plan Agent:**
```
@workspace I am the Rowdy Crown Business Plan Agent. Read 
projects/rowdy-crown/agents/business-plan-agent.md and projects/rowdy-crown/PROPOSAL.md.

Build a detailed Year 1 monthly revenue model for Rowdy Crown ATX using these assumptions:
- Open March 2027
- Thursday: 150 guests avg, $15 cover, $35 avg bar spend
- Friday: 350 guests avg, $30 cover, $50 avg bar spend  
- Saturday: 400 guests avg, $40 cover, $55 avg bar spend (+ bottle service)
- Sunday brunch: 100 guests, $15 cover, $30 avg spend
- Private events: 2/month avg, $8,000 avg

Show Month 1–12 revenue by stream in a markdown table.
```

**Funding Research:**
```
@workspace I am the Rowdy Crown Funding Agent. Read projects/rowdy-crown/FUNDING.md.

Search for currently open grant opportunities for:
- Minority-owned business / Black-owned business
- Entertainment venue / hospitality / restaurant-bar
- Texas-based or national programs

For each grant found: name, org, amount, eligibility, deadline, application URL.
Update FUNDING.md with any new entries not already listed.
```

**Phi Beta Sigma Foundation — 501(c)(3) Filing:**
```
@workspace I am working on the Phi Beta Sigma Collegiate Pathways Foundation.
Read projects/pbs-foundation/CHARTER.md and projects/pbs-foundation/BYLAWS.md.

Help me prepare for IRS Form 1023-EZ submission:
1. What are the eligibility requirements for Form 1023-EZ vs full 1023?
2. What documents do I need to have ready before submitting?
3. Walk me through the key sections of Form 1023-EZ I need to complete based on our charter.
```

**YEPC — Hutto EDC Follow-up:**
```
@workspace I am working on the YEPC (Youth Elite Performance Complex) project.
Read projects/yepc/outreach/hutto-edc-initial-outreach.md and 
projects/yepc/outreach/hutto-edc-followup-7day.md.

Today is [INSERT DATE]. Draft the next appropriate follow-up email to the Hutto EDC
based on where we are in the outreach sequence. 
The contact is at the Hutto Economic Development Corporation regarding the 
110-acre CR 132 site under Smith Capital Properties.
```

---

## Part 6 — Daily Git Workflow

### Every Time You Sit Down to Work

```bash
# 1. Navigate to the repo
cd ~/Documents/AgentHarness

# 2. Pull latest (in case anything was auto-committed by Base44)
git pull origin main

# 3. Open in VS Code
code .
```

### While Working

```bash
# Check what's changed
git status

# See what changed in a file
git diff projects/xftc-redevelopment/plugin/xftc-membership/xftc-membership.php
```

### When You Finish a Session

```bash
# Stage all changes
git add .

# Commit with a clear message
git commit -m "feat: Phase 1 — replace xftc_ prefix with tracksuite_ in admin class"

# Push to GitHub
git push origin main
```

### Working on a Feature Branch (Recommended for big changes)

```bash
# Create and switch to a new branch
git checkout -b phase1/de-brandification

# Work, commit as you go...
git add .
git commit -m "Phase 1: replace all xftc_ function prefixes"

# When done, merge back to main
git checkout main
git merge phase1/de-brandification
git push origin main

# Delete the branch
git branch -d phase1/de-brandification
```

---

## Part 7 — Staging Site Access (Still Live)

For testing against the real staging environment:

| | Value |
|-|-------|
| **URL** | https://staging.s2tdesigns.com |
| **WP Admin** | https://staging.s2tdesigns.com/wp-admin |
| **Username** | agent_design |
| **Password** | yK#jR7ScYjbk#@M#8A#356dp |

**Deploy to staging via WP Admin:**
1. Zip the plugin folder: `zip -r xftc-membership.zip xftc-membership/`
2. WP Admin → Plugins → Add New → Upload Plugin → upload zip

**Deploy via WP-CLI (if available on staging):**
```bash
# SSH into staging (if you have access) then:
wp plugin install /path/to/xftc-membership.zip --force --activate
```

---

## Part 8 — Live Site Access (xtremeforcetrackclub.org)

| | Value |
|-|-------|
| **WP Admin** | https://xtremeforcetrackclub.org/wp-admin |
| **Username** | dsmith |
| **App Password** | PvCp LL4V X1BJ xxcj ei2z i6pB |

**⚠️ Always test on staging first. Never push untested code to live.**

---

## Part 9 — Project Priority Order

When you open Copilot, work these in order:

| Priority | Project | Task | Copilot Template |
|----------|---------|------|-----------------|
| 1 | XFTC Plugin | Sprint 3 — admin dashboard widgets | Template above |
| 2 | TrackSuite | Phase 1 — de-brandification | Template above |
| 3 | Rowdy Crown | Research site + build pro forma | Template above |
| 4 | PBS Foundation | 501(c)(3) Form 1023-EZ prep | Template above |
| 5 | YEPC | May 25 Hutto EDC follow-up | Template above |

---

## Part 10 — Troubleshooting

### "Copilot Chat doesn't know my files"
- Make sure you opened VS Code from the AgentHarness folder: `code .`
- Use `@workspace` prefix — without it, Copilot only looks at the current file
- If workspace index is stale: `Ctrl+Shift+P` → "GitHub Copilot: Reset Workspace Index"

### "LocalWP plugin not showing up in WP Admin"
- Check symlink was created correctly: `ls -la ~/Local\ Sites/tracksuite-dev/app/public/wp-content/plugins/`
- Symlink should show an arrow: `xftc-membership -> /path/to/AgentHarness/...`
- If no arrow, the symlink failed — re-run the `ln -s` command

### "PHP errors in LocalWP"
- Open LocalWP → site → "Open Site Shell" → this opens a terminal with WP-CLI
- Run: `wp --info` to confirm WP is working
- Check logs: `tail -f ~/Local\ Sites/tracksuite-dev/logs/php/php.log`

### "Git push rejected"
```bash
# Pull first to get any remote changes
git pull origin main --rebase
# Then push again
git push origin main
```

### "Copilot suggestions are off-topic"
- Be more specific with file references: `#file:xftc-membership.php what does this bootstrap do?`
- Add context: "I'm building a WordPress plugin. The main file is..."

---

## Quick Reference Card

```
Daily startup:
  cd ~/Documents/AgentHarness && git pull && code .

Copilot Chat shortcut:
  Cmd+Shift+I (Mac) / Ctrl+Shift+I (Windows)

Always prefix with:
  @workspace [your question]

Commit + push:
  git add . && git commit -m "your message" && git push origin main

LocalWP WP Admin:
  Click site → WP Admin button

Check for errors:
  LocalWP → site → "Open Site Shell" → wp plugin list
```
