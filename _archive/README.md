# _archive/
**Last updated:** 2026-05-27

This folder holds superseded build artifacts, one-off scripts, and old functions
that are no longer part of the active AgentHarness execution path.

**Do not delete** — kept for reference and rollback if needed.

---

## Contents

### root-scripts/
One-off Python scripts and docs that were loose in the app root.
Moved here to keep the root clean for active execution.

| File | Was Used For |
|------|-------------|
| `build_lebc_deck.py` | LEBC media campaign deck builder (one-time) |
| `lebc_discovery.py` | LEBC discovery/audit script (one-time) |
| `PBS_NEXT_STEPS.md` | Psi Beta Sigma site next steps doc (superseded by project files) |
| `PBS_WEBSITE_README.md` | PBS site README (superseded by project files) |
| `LEBC_Media_Campaign_Proposal.pptx` | LEBC deck (delivered, archived) |
| `pbs_site_launch.pptx` | PBS site launch deck (delivered, archived) |

### pbs-sprints/
Old PBS sprint deployment scripts from the s2tdesigns client folder.
Superseded by direct REST API deployment workflow.

| File | Was Used For |
|------|-------------|
| `run_sprints.py` | Sprint A–I runner for PBS site build |
| `deploy-skyline.py` | One-time CSS skyline header deploy |

### functions-old/
Deprecated backend functions.

| File | Was Used For |
|------|-------------|
| `githubPush.ts` | GitHub push backend function — superseded by `.agents/skills/github_push.js` |

---

## Active Execution Path (do not archive these)

- `.agents/agentharness/` — LangGraph + Reflexion engine (Phases 1–4)
- `.agents/agents/` — All agent profile definitions
- `.agents/projects/` — Project docs, requirements, architecture
- `.agents/skills/` — Reusable skill scripts
- `.agents/rules/` — Standing agent rules
- `entities/` — Base44 entity schemas
