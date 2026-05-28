# Sigma Signal Constant Contact

## Purpose
Monitor The Sigma Signal Constant Contact activity and surface anything that needs attention: campaign sends, bounces, unsubscribes, engagement changes, list-health issues, and follow-up opportunities.

## Primary Agent
- **Agent:** sigmasignalconstantcontactmonitor
- **Role:** Constant Contact monitoring and reporting agent
- **Status:** Pending integration
- **Agent file:** `D:\Projects\agentharness\agents\sigmasignalconstantcontactmonitor.md`
- **Project path:** `D:\Projects\agentharness\projects\sigma-signal-constant-contact`

## Monitoring Scope
- Campaign send status and completion
- Bounce, unsubscribe, spam complaint, and list-growth movement
- High-performing links, campaigns, and audience segments
- Failed imports, sync issues, and suppressed contacts
- Replies or inbound email activity tied to The Sigma Signal newsletter identity
- Weekly recommendations for improving open rate, click rate, and deliverability
- Incoming requests sent to `thesigmasignal.1stvp1914@gmail.com`

## Integrations Needed
- Constant Contact OAuth or API key access
- The Sigma Signal Gmail account: `thesigmasignal.1stvp1914@gmail.com`
- Optional dashboard feed in `projects/agent-dashboard/data/agents.json`

## Cadence
- **Daily health check:** Review campaign/account signals and flag urgent deliverability or audience-health issues.
- **Post-campaign check:** Review performance after each send and summarize engagement, bounces, unsubscribes, and suggested follow-ups.
- **Weekly digest:** Summarize growth, engagement trends, risks, and next actions.
- **Newsletter cadence:** Every two weeks. The next issue is tracked as the week of May 25-31, 2026, with a working target date of May 28, 2026.

## Open Items
- [ ] Connect Constant Contact credentials.
- [ ] Confirm Constant Contact account owner/login.
- [ ] Confirm preferred alert destination.
- [ ] Define campaign performance thresholds.
- [ ] Decide whether contact list exports should be logged locally or only summarized.
