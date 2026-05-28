# Agent Logging Protocol — Reflexion Data

## Purpose
Every agent task I complete inside Base44 must be logged to `AgentRunLog` and, when a skill is revised, to `AgentSkillVersion`. This enables:
- Daily reflexion reports showing what went right vs. wrong per agent
- Self-improving skill files that get better with each revision
- A searchable audit trail of all agent activity across all projects

---

## When to Log

Log to `AgentRunLog` **after every agent task**, regardless of outcome:
- Completed tasks (status: `complete`)
- Partially completed tasks (status: `partial`)
- Failed tasks (status: `failed`)

Log to `AgentSkillVersion` **when a skill is revised** (score < 0.75) or when a new agent type is run for the first time.

---

## Agent ID Mapping

Use these exact agent_id values for consistency:

| Agent                        | agent_id                        | project        |
|------------------------------|---------------------------------|----------------|
| XFTC Project Lead            | xftc-project-lead               | xftc           |
| XFTC Plugin Dev              | xftc-plugin-dev                 | xftc           |
| XFTC Frontend Dev            | xftc-frontend-dev               | xftc           |
| XFTC Payments                | xftc-payments-agent             | xftc           |
| XFTC QA                      | xftc-qa-agent                   | xftc           |
| Grant Writer                 | grant-writer-agent              | grants         |
| Grants Researcher            | grants-research-agent           | grants         |
| YEPC Grant Writer            | yepc-grant-writer-agent         | yepc           |
| YEPC Real Estate Research    | yepc-real-estate-research-agent | yepc           |
| YEPC Project Manager         | yepc-project-manager            | yepc           |
| S2T Project Lead             | s2t-project-lead                | s2tdesigns      |
| S2T Web Dev                  | s2t-webdev-agent                | s2tdesigns      |
| S2T SEO                      | s2t-seo-agent                   | s2tdesigns      |
| PBS Project Lead             | pbs-project-lead                | pbs            |
| PBS Fundraising              | pbs-fundraising-agent           | pbs            |
| PBS Communications           | pbs-communications-agent        | pbs            |
| Social Media Project Lead    | social-project-lead             | social         |
| Social Content Strategist    | social-content-strategist       | social         |
| Social Copywriter            | social-copywriter               | social         |
| Social Ads Manager           | social-ads-manager              | social         |
| Social Analyst               | social-analyst                  | social         |
| Finance CFO                  | finance-cfo                     | smithcap-finance|
| Finance CPA                  | finance-cpa                     | smithcap-finance|
| Finance Tax Strategist       | finance-tax-strategist          | smithcap-finance|
| Ministry Project Lead        | ministry-project-lead           | ministry       |
| Ministry Sermon Writer       | ministry-sermon-writer          | ministry       |
| Sigma Signal Project Lead    | sigma-signal-project-lead       | sigma-signal   |
| Sigma Signal Writer          | sigma-signal-writer             | sigma-signal   |
| Travel Project Lead          | travel-project-lead             | travel         |
| Solar Project Lead           | solar-project-lead              | solar          |
| Elevation Project Lead       | elevation-project-lead          | elevation      |
| Nutrue Project Lead          | nutrue-project-lead             | nutrue         |
| SmithCap Acquisitions        | smithcap-acquisitions-agent     | smithcap       |
| WordPress Agent (XFTC site)  | wordpress-agent-xftc            | xftc           |
| WordPress Agent (PBS site)   | wordpress-agent-pbs             | pbs            |

---

## Scoring Rubric (same as harness evaluate_node)

| Score | Meaning |
|-------|---------|
| 0.90–1.00 | Excellent — fully complete, high quality, concise |
| 0.75–0.89 | Good — complete with minor issues |
| 0.60–0.74 | Acceptable — some gaps or quality issues, no revision needed unless critical |
| < 0.60    | Poor — requires revision, update skill version |

**Composite formula:** `overall = completion*0.5 + quality*0.35 + efficiency*0.15`

---

## What to Log in Each Field

| Field            | What to put |
|------------------|-------------|
| `run_id`         | Short UUID (8 chars) — unique per run |
| `agent_id`       | From mapping table above |
| `project`        | Project slug (e.g. "xftc", "yepc", "pbs") |
| `task`           | The actual task description (first 500 chars) |
| `score`          | Float 0.0–1.0 based on rubric above |
| `critique`       | What went well, what was missing, what to improve next time |
| `revision_count` | How many times the output was revised before finalizing |
| `output_summary` | First 500 chars of the actual output |
| `skill_version`  | Current version of this agent's skill file (start at 1) |
| `status`         | `complete` / `partial` / `failed` |
| `environment`    | Always `base44` for tasks run here |

---

## How I Log (Implementation)

I use the `create_entity_records` tool directly after completing each agent task:

```python
# Log to AgentRunLog
create_entity_records("AgentRunLog", [{
    "run_id": "<8-char-uuid>",
    "agent_id": "xftc-plugin-dev",
    "project": "xftc",
    "task": "Build leaderboard REST endpoint",
    "score": 0.87,
    "critique": "Endpoint logic solid. Missing pagination on results over 50 rows.",
    "revision_count": 1,
    "output_summary": "Created /wp-json/xftc/v1/leaderboard endpoint with season filter...",
    "skill_version": 2,
    "status": "complete",
    "environment": "base44"
}])

# If skill was revised (score < 0.75), also log to AgentSkillVersion
create_entity_records("AgentSkillVersion", [{
    "agent_id": "xftc-plugin-dev",
    "skill_name": "xftc_plugin_dev",
    "version": 2,
    "content": "# Skill: xftc_plugin_dev v2\n\n## Improvements\n- Always add pagination...",
    "avg_score": 0.87,
    "total_runs": 3,
    "last_critique": "Missing pagination on results over 50 rows.",
    "environment": "base44"
}])
```

---

## Skill Revision Trigger

If a task scores **< 0.75**, I must:
1. Identify what specifically failed
2. Update the agent's skill file in `.agents/agents/projects/<project>/<agent>.md`
3. Log the new version to `AgentSkillVersion`
4. Note the revision in `AgentRunLog.revision_count`

---

## Daily Report

A daily automation at 7:00 AM CT queries both entities and generates a reflexion digest showing:
- Each agent's last score, critique, and revision count
- Skill version trajectory (improving or stuck?)
- Flagged agents (score < 0.75 on last run)
- Project-level summary

This report is sent to David as a message notification.
