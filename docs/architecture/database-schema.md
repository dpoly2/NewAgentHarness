# Database Schema

Expanded compact reference for the local `runs_v3.db` schema.

## Schema structure

- Core runtime tables come from `hub_db.py`.
- Feature scripts extend the database for memory, email, feedback, file upload, agent messaging, prompt templates, and briefing history.
- Many relationships are application-level rather than strongly enforced foreign keys.

## Table groups

### Core runtime
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| runs | 13 | id:INTEGER, run_id:TEXT, agent_id:TEXT, project:TEXT, graph:TEXT, task:TEXT, score:REAL, critique:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| skills | 8 | id:INTEGER, agent_id:TEXT, skill_name:TEXT, version:INTEGER, content:TEXT, avg_score:REAL, last_critique:TEXT, created_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| job_queue | 12 | id:TEXT, agent_id:TEXT, project:TEXT, graph:TEXT, task:TEXT, priority:TEXT, status:TEXT (`queued`/`running`/`cancelling`/`completed`/`failed`) … | — | .agents/agentharness/app/v3/hub_db.py |
| ws_events | 3 | id:INTEGER, payload_json:TEXT, created_at:TEXT | — | .agents/agentharness/app/v3/core/database.py |
| todos | 11 | id:TEXT, title:TEXT, description:TEXT, priority:TEXT, status:TEXT, project:TEXT, due_date:TEXT, tags:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| notifications | 12 | notification_id:TEXT, user_id:TEXT, type:TEXT, priority:TEXT, title:TEXT, details:TEXT, data_json:TEXT, created_at:TIMESTAMP … | — | .agents/agentharness/app/v3/proactive_monitor.py |
| hub_config | 3 | key:TEXT, value:TEXT, updated_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| users | 8 | id:INTEGER, username:TEXT, email:TEXT, hashed_password:TEXT, role:TEXT, is_active:INTEGER, created_at:TEXT, last_login:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| scheduled_jobs | 13 | id:TEXT, agent_id:TEXT, project:TEXT, graph:TEXT, task:TEXT, run_type:TEXT, cron_expr:TEXT, interval_sec:INTEGER … | — | .agents/agentharness/app/v3/hub_db.py |

### Portfolio / CRM
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| projects | 9 | id:TEXT, slug:TEXT, name:TEXT, description:TEXT, status:TEXT, lead_agent:TEXT, tags:TEXT, created_at:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| clients | 13 | id:TEXT, slug:TEXT, name:TEXT, business_type:TEXT, service:TEXT, contact_name:TEXT, contact_email:TEXT, engagement:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| travel_trips | 11 | id:TEXT, name:TEXT, destination:TEXT, depart_date:TEXT, return_date:TEXT, status:TEXT, budget:REAL, spent:REAL … | — | .agents/agentharness/app/v3/hub_db.py |
| agent_registry | 15 | id:TEXT, agent_id:TEXT, name:TEXT, type:TEXT, role:TEXT, description:TEXT, project_slug:TEXT, capabilities:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| agent_memory | 5 | id:INTEGER, agent_id:TEXT, key:TEXT, value:TEXT, updated_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| conversations | 5 | id:TEXT, slug:TEXT, title:TEXT, created_at:TEXT, updated_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| messages | 6 | id:TEXT, conversation_id:TEXT, role:TEXT, content:TEXT, agent_id:TEXT, created_at:TEXT | FOREIGN KEY (conversation_id | .agents/agentharness/app/v3/hub_db.py |
| daily_briefs | 3 | id:TEXT, content:TEXT, created_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |

### Automations / content
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| automations | 15 | id:TEXT, slug:TEXT, name:TEXT, description:TEXT, project_slug:TEXT, agent_id:TEXT, trigger_type:TEXT, trigger_config:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| automation_runs | 11 | id:TEXT, automation_id:TEXT, automation_slug:TEXT, triggered_by:TEXT, status:TEXT, output:TEXT, error:TEXT, duration_sec:REAL … | FOREIGN KEY (automation_id | .agents/agentharness/app/v3/hub_db.py |
| automation_documents | 12 | id:TEXT, automation_id:TEXT, run_id:TEXT, title:TEXT, doc_type:TEXT, content:TEXT, file_path:TEXT, status:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| knowledge_base | 12 | id:TEXT, title:TEXT, content:TEXT, source:TEXT, source_type:TEXT, category:TEXT, tags:TEXT, project_slug:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| documents | 15 | id:TEXT, title:TEXT, doc_type:TEXT, content:TEXT, format:TEXT, project_slug:TEXT, client_id:TEXT, entity_type:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| attachments | 10 | id:TEXT, entity_type:TEXT, entity_id:TEXT, filename:TEXT, original_name:TEXT, file_path:TEXT, mime_type:TEXT, file_size:INTEGER … | — | .agents/agentharness/app/v3/hub_db.py |
| integrations | 14 | id:TEXT, name:TEXT, provider:TEXT, entity_type:TEXT, entity_id:TEXT, auth_type:TEXT, credentials:TEXT, scope:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| reports | 12 | id:TEXT, title:TEXT, report_type:TEXT, content:TEXT, summary:TEXT, project_slug:TEXT, generated_by:TEXT, job_id:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| events_log | 9 | id:INTEGER, event_type:TEXT, entity_type:TEXT, entity_id:TEXT, actor:TEXT, summary:TEXT, detail:TEXT, level:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |

### Markets
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| market_positions | 17 | id:TEXT, ticker:TEXT, name:TEXT, position_type:TEXT, action:TEXT, shares:REAL, entry_price:REAL, current_price:REAL … | — | .agents/agentharness/app/v3/hub_db.py |
| market_watchlist | 7 | id:TEXT, ticker:TEXT, name:TEXT, category:TEXT, target_price:REAL, notes:TEXT, added_at:TEXT | — | .agents/agentharness/app/v3/hub_db.py |
| market_trade_theories | 14 | id:TEXT, name:TEXT, description:TEXT, hypothesis:TEXT, starting_balance:REAL, current_balance:REAL, status:TEXT, win_count:INTEGER … | — | .agents/agentharness/app/v3/hub_db.py |
| market_paper_trades | 24 | id:TEXT, theory_id:TEXT, ticker:TEXT, name:TEXT, position_type:TEXT, direction:TEXT, shares:REAL, entry_price:REAL … | — | .agents/agentharness/app/v3/hub_db.py |

### Memory / intelligence
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| global_memory | 11 | id:TEXT, category:TEXT, key:TEXT, value:TEXT, source:TEXT, confidence:REAL, importance:INTEGER, last_verified:TEXT … | — | .agents/agentharness/app/v3/add_global_memory.py |

### Email / feedback / files
| Table | Cols | Preview columns | Relationships | Source |
| --- | --- | --- | --- | --- |
| email_connectors | 19 | id:TEXT, label:TEXT, email_address:TEXT, provider:TEXT, auth_type:TEXT, imap_host:TEXT, imap_port:INTEGER, smtp_host:TEXT … | — | .agents/agentharness/app/v3/hub_db.py |
| email_accounts | 14 | id:TEXT, user_id:INTEGER, provider:TEXT, email_address:TEXT, display_name:TEXT, access_token:TEXT, refresh_token:TEXT, token_expires_at:TEXT … | — | .agents/agentharness/app/v3/add_email_accounts.py |
| email_cleanup_plans | 8 | id:TEXT, account_id:TEXT, status:TEXT, total_emails:INTEGER, suggested_cleanup_count:INTEGER, estimated_space_mb:INTEGER, created_at:TEXT, executed_at:TEXT | FOREIGN KEY (account_id | .agents/agentharness/app/v3/add_email_accounts.py |
| email_cleanup_items | 14 | id:TEXT, plan_id:TEXT, email_id:TEXT, category:TEXT, subject:TEXT, from_address:TEXT, email_date:TEXT, size_bytes:INTEGER … | FOREIGN KEY (plan_id | .agents/agentharness/app/v3/add_email_accounts.py |
| message_feedback | 8 | feedback_id:TEXT, message_id:TEXT, user_id:TEXT, conversation_id:TEXT, rating:INTEGER, feedback_text:TEXT,, category:TEXT,, created_at:TIMESTAMP | FOREIGN KEY (message_id | .agents/agentharness/app/v3/add_feedback_system.py |
| corrections | 10 | correction_id:TEXT, message_id:TEXT, user_id:TEXT, conversation_id:TEXT, original_intent:TEXT,, corrected_intent:TEXT, correction_text:TEXT, correction_type:TEXT … | FOREIGN KEY (message_id | .agents/agentharness/app/v3/add_feedback_system.py |
| user_style_preferences | 13 | user_id:TEXT, preferred_length:TEXT, preferred_formality:TEXT, use_emojis:BOOLEAN, citation_density:TEXT, code_style:TEXT, avg_positive_response_tokens:INTEGER, avg_negative_response_tokens:INTEGER … | — | .agents/agentharness/app/v3/add_feedback_system.py |
| uploaded_files | 15 | file_id:TEXT, user_id:TEXT, filename:TEXT, file_type:TEXT, mime_type:TEXT, file_size:INTEGER, storage_path:TEXT, parsed_content:TEXT, … | FOREIGN KEY (user_id | .agents/agentharness/app/v3/add_file_uploads.py |
| file_chunks | 9 | chunk_id:TEXT, file_id:TEXT, chunk_index:INTEGER, chunk_text:TEXT, chunk_tokens:INTEGER, page_number:INTEGER,, embedding_vector:TEXT,, embedding_model:TEXT … | FOREIGN KEY (file_id | .agents/agentharness/app/v3/add_file_uploads.py |
| prompt_templates | 10 | id:TEXT, title:TEXT, category:TEXT, prompt_text:TEXT, agent_id:TEXT, project_slug:TEXT, is_system:INTEGER, usage_count:INTEGER … | — | .agents/agentharness/app/v3/add_prompt_templates.py |
| agent_messages | 13 | message_id:TEXT, conversation_id:TEXT, sender_agent:TEXT, recipient_agent:TEXT, message_type:TEXT, payload_json:TEXT, status:TEXT, created_at:TIMESTAMP … | — | .agents/agentharness/app/v3/add_agent_messaging.py |
| agent_conversations | 10 | conversation_id:TEXT, user_id:TEXT, initiator_agent:TEXT, participant_agents:TEXT, goal:TEXT, status:TEXT, created_at:TIMESTAMP, completed_at:TIMESTAMP … | — | .agents/agentharness/app/v3/add_agent_messaging.py |
| agent_capabilities | 10 | agent_name:TEXT, display_name:TEXT, description:TEXT, capabilities_json:TEXT, dependencies:TEXT,, response_time_avg_ms:INTEGER, success_rate:REAL, total_requests:INTEGER … | — | .agents/agentharness/app/v3/add_agent_messaging.py |
| morning_briefs | 7 | brief_id:TEXT, user_id:TEXT, brief_text:TEXT, stats_json:TEXT, created_at:TIMESTAMP, viewed:BOOLEAN, viewed_at:TIMESTAMP | — | .agents/agentharness/app/v3/morning_brief.py |

## Table notes

- `runs` stores score, critique, output, revision count, and status for historical agent runs.
- `job_queue` is the operational queue backing `POST /api/runs`; `cancelling` is the cross-worker cancel propagation state in addition to the normal queued/running/completed/failed lifecycle.
- `ws_events` is the shared broadcast channel for multi-worker WebSocket delivery and is auto-cleaned after 5 minutes.
- `global_memory` is the shared long-term fact store consumed by Inez and specialist agents.
- `agent_skill_levels`, `reflexion_log`, and `interaction_patterns` are the three main Progressive Intelligence tables.
- `uploaded_files` and `file_chunks` support the document-RAG ingestion path.
- `email_cleanup_plans` and `email_cleanup_items` capture analysis → approval → execution workflows.
- `market_trade_theories` and `market_paper_trades` provide paper-trading storage without requiring brokerage connectivity.

## Relationship summary

- Explicit foreign keys: `messages.conversation_id -> conversations.id`, `automation_runs.automation_id -> automations.id`.
- Logical relationships: `automation_documents` links to automations/runs, `file_chunks` links to uploaded files, cleanup items link to cleanup plans, and reports/jobs commonly link via `job_id`.
- Shared identifiers such as `project_slug`, `client_id`, `agent_id`, and `conversation_id` are application-level join keys across many modules.

## Source files

- `.agents/agentharness/app/v3/add_agent_messaging.py`
- `.agents/agentharness/app/v3/add_email_accounts.py`
- `.agents/agentharness/app/v3/add_feedback_system.py`
- `.agents/agentharness/app/v3/add_file_uploads.py`
- `.agents/agentharness/app/v3/add_global_memory.py`
- `.agents/agentharness/app/v3/add_prompt_templates.py`
- `.agents/agentharness/app/v3/hub_db.py`
- `.agents/agentharness/app/v3/morning_brief.py`
- `.agents/agentharness/app/v3/proactive_monitor.py`

## Operational guidance

- Treat SQLite as the system of record for local ArchonHub state.
- Prefer adding new feature tables in isolated migration-style scripts like the existing `add_*` helpers.
- Keep JSON blobs in text columns only when a schema would be too rigid for the current iteration.
- When adding API surfaces, document which table is authoritative and which are derived/summary tables.

## Suggested review order

1. `runs`, `job_queue`, and `scheduled_jobs` for execution flow.
2. `agent_registry`, `agent_memory`, `global_memory`, and intelligence tables for agent behavior.
3. `documents`, `knowledge_base`, `uploaded_files`, and `file_chunks` for RAG.
4. `email_connectors`, cleanup tables, and feedback tables for user-facing workflow extensions.
5. Markets and reports tables for domain-specific expansion.

## Table-by-table reminders

- `users` and `user_preferences` shape auth and personalization.
- `notifications` may come from core hub flows or proactive monitor flows.
- `events_log` is the right place for durable audit-style summaries.
- `attachments` can bridge documents or other entities without schema duplication.
- `integrations` exists as a generic connector store beyond email-specific rows.
- `reports` are the durable human-readable output layer across multiple projects.
- `hub_config` is used for lightweight feature flags and runtime config values.
- `prompt_templates` provides reusable prompt text separate from agent skill files.

## Change management notes

- If you add a new table, update both the architecture docs and any matching iOS models or API docs.
- If you alter a JSON column shape, treat that as an API contract change for all downstream consumers.
- When possible, add indexes for any new high-cardinality query path that appears in list/search endpoints.
- Keep migration helpers idempotent so they can be safely re-run in local environments.

## Related docs

- [Architecture overview](overview.md)
- [API reference](../api/reference.md)
- [Global memory feature](../features/global-memory.md)
- [Document RAG feature](../features/document-rag.md)

## Additional schema notes

- `skills` stores the current persisted skill text per agent in the local engine.
- `job_queue` and `runs` are complementary: one is operational queue state, the other is historical execution history.
- `clients`, `projects`, and `documents` form the main business-data triangle for portfolio work.
- `knowledge_base` is lighter-weight than `documents` and better suited for reusable snippets or distilled notes.
- `attachments` lets the system associate files with many entity types without bespoke join tables.
- `daily_briefs` and `morning_briefs` coexist because the codebase has both older and newer briefing pathways.
- `integrations` is a generic store; `email_connectors` is the specialized email-focused connector schema.

