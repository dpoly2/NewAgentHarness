# AgentHarness

David Smith's personal AI agent system — built on Base44 Superagent.

## Architecture

```
AgentHarness/
├── agents/           # Individual agent profiles and configs
├── rules/            # Site-specific agent rules
├── automations/      # Automation task descriptions
└── README.md
```

## Lanes

### Personal Productivity
Each email identity has a dedicated agent profile:
- `smithdaiiagent` — Personal Gmail
- `communicationsdirgcr` — Communications Director GCR
- `thesigmasignal` — The Sigma Signal newsletter
- `smithcapitalproperties` — Smith Capital Properties
- `xtremeforcetrackclub` — Xtreme Force Track Club
- `allensmithagent` — Personal Outlook (pending)
- `nutrueapparel` — Nutrue Apparel custom domain (pending)
- `psibetasigma1914` — Psi Beta Sigma 1914 (pending)

### Web Development
- `wordpressagent` — WordPress maintenance, themes, plugins
- `web_dev_researcher` — Site audits and prioritized fix reports

## Active Sites
| Site | Status | Notes |
|------|--------|-------|
| xtremeforcetrackclub.org | ✅ Connected | REST API via dsmith |
| psibetasigma1914.org | ⚠️ Blocked | .htaccess fix needed |
| nutrueapparel.com | ⚠️ Blocked | Authorization header issue |
| smithcapitalproperties.com | 🔲 Pending | Credentials needed |

## Automations
- **Daily Email Digest** — 8:00 AM Chicago time, all connected inboxes
- **Xtreme Force Logger** — Every 4 hours, logs new athlete signups and payments
