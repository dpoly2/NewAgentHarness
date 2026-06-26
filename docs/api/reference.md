# Endpoint Reference

Compact index of all current routes. Route logic lives in `routers/`; shared internals in `core/`.

## Route counts by group

| Group | Count |
| --- | --- |
| / | 1 |
| /ws | 1 |
| agents | 10 |
| alpaca | 15 |
| auth | 3 |
| automations | 9 |
| briefing | 4 |
| briefs | 3 |
| clients | 5 |
| config | 2 |
| connectors | 12 |
| context | 1 |
| conversations | 4 |
| corrections | 1 |
| documents | 5 |
| email | 6 |
| events | 1 |
| feedback | 5 |
| files | 7 |
| health | 1 |
| import | 1 |
| inez | 5 |
| integrations | 4 |
| intelligence | 4 |
| knowledge | 5 |
| memory | 8 |
| messages | 1 |
| models | 4 |
| monitoring | 3 |
| notifications | 3 |
| projects | 5 |
| prompt-templates | 5 |
| providers | 2 |
| queue | 3 |
| reports | 5 |
| runs | 3 |
| sandbox | 2 |
| scheduler | 4 |
| search | 3 |
| skills | 3 |
| stats | 1 |
| todos | 5 |
| trips | 5 |
| users | 5 |

## Full route table

| Method | Path | Handler | Auth | Source File |
| --- | --- | --- | --- | --- |
| GET | / | root | Public | .agents/agentharness/app/v3/hub_server.py |
| POST | /api/auth/login | login | Public | .agents/agentharness/app/v3/routers/auth_routes.py |
| POST | /api/auth/register | register | Public | .agents/agentharness/app/v3/routers/auth_routes.py |
| GET | /api/auth/me | me | Bearer JWT | .agents/agentharness/app/v3/routers/auth_routes.py |
| GET | /api/health | health | Bearer JWT | .agents/agentharness/app/v3/routers/config_api.py |
| POST | /api/runs | create_run | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/runs | list_runs | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/runs/{run_id}/cancel | cancel_run | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/queue | get_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/queue/pause | pause_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| POST | /api/queue/resume | resume_queue | Bearer JWT | .agents/agentharness/app/v3/routers/runs.py |
| GET | /api/todos | get_todos | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| POST | /api/todos | create_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| GET | /api/todos/{id} | get_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| PUT | /api/todos/{id} | update_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| DELETE | /api/todos/{id} | delete_todo | Bearer JWT | .agents/agentharness/app/v3/routers/todos.py |
| GET | /api/notifications | list_notifications | Bearer JWT | .agents/agentharness/app/v3/routers/notifications.py |
| POST | /api/notifications/read | mark_notifications_read | Bearer JWT | .agents/agentharness/app/v3/routers/notifications.py |
| DELETE | /api/notifications | clear_notifications | Bearer JWT | .agents/agentharness/app/v3/routers/notifications.py |
| GET | /api/trips | list_trips | Bearer JWT | .agents/agentharness/app/v3/routers/trips.py |
| POST | /api/trips | create_trip | Bearer JWT | .agents/agentharness/app/v3/routers/trips.py |
| GET | /api/trips/{id} | get_trip | Bearer JWT | .agents/agentharness/app/v3/routers/trips.py |
| PUT | /api/trips/{id} | update_trip | Bearer JWT | .agents/agentharness/app/v3/routers/trips.py |
| DELETE | /api/trips/{id} | delete_trip | Bearer JWT | .agents/agentharness/app/v3/routers/trips.py |
| GET | /api/connectors | list_connectors | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| POST | /api/connectors | create_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/{id} | get_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| PUT | /api/connectors/{id} | update_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| DELETE | /api/connectors/{id} | delete_connector | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| POST | /api/connectors/{id}/test | test_connector_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/google/init | google_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/google/callback | google_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/gmail/init | gmail_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/gmail/callback | gmail_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/microsoft/init | microsoft_oauth_init | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/connectors/oauth/microsoft/callback | microsoft_oauth_callback | Public | .agents/agentharness/app/v3/routers/connectors.py |
| GET | /api/projects | list_projects | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| POST | /api/projects | create_project | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| GET | /api/projects/{id} | get_project | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| PUT | /api/projects/{id} | update_project | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| DELETE | /api/projects/{id} | delete_project | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| GET | /api/clients | list_clients | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| POST | /api/clients | create_client | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| GET | /api/clients/{id} | get_client | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| PUT | /api/clients/{id} | update_client | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| DELETE | /api/clients/{id} | delete_client | Bearer JWT | .agents/agentharness/app/v3/routers/projects.py |
| GET | /api/conversations | list_conversations | Bearer JWT | .agents/agentharness/app/v3/routers/conversations.py |
| POST | /api/conversations | create_conversation | Bearer JWT | .agents/agentharness/app/v3/routers/conversations.py |
| GET | /api/conversations/{id}/messages | list_messages | Bearer JWT | .agents/agentharness/app/v3/routers/conversations.py |
| POST | /api/conversations/{id}/messages | create_message | Bearer JWT | .agents/agentharness/app/v3/routers/conversations.py |
| GET | /api/search | search_conversations | Bearer JWT | .agents/agentharness/app/v3/routers/search.py |
| GET | /api/search/web | web_search_get | Bearer JWT | .agents/agentharness/app/v3/routers/web_search_api.py |
| POST | /api/search/web | web_search_post | Bearer JWT | .agents/agentharness/app/v3/routers/web_search_api.py |
| GET | /api/search/web/status | web_search_status | Bearer JWT | .agents/agentharness/app/v3/routers/web_search_api.py |
| GET | /api/memory/agents/{agent_id} | get_memory | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| PUT | /api/memory/agents/{agent_id} | update_memory | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| GET | /api/prompt-templates | list_prompt_templates | Bearer JWT | .agents/agentharness/app/v3/routers/prompt_templates.py |
| POST | /api/prompt-templates | create_prompt_template | Bearer JWT | .agents/agentharness/app/v3/routers/prompt_templates.py |
| PUT | /api/prompt-templates/{template_id} | update_prompt_template | Bearer JWT | .agents/agentharness/app/v3/routers/prompt_templates.py |
| DELETE | /api/prompt-templates/{template_id} | delete_prompt_template | Bearer JWT | .agents/agentharness/app/v3/routers/prompt_templates.py |
| POST | /api/prompt-templates/{template_id}/use | use_prompt_template | Bearer JWT | .agents/agentharness/app/v3/routers/prompt_templates.py |
| POST | /api/inez/chat | inez_chat | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/brief | inez_morning_brief | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/status | inez_status | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/inez/memory | inez_memory | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| DELETE | /api/inez/memory/facts/{key} | delete_inez_fact | Bearer JWT | .agents/agentharness/app/v3/routers/inez.py |
| GET | /api/briefs | list_briefs | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| POST | /api/briefs | create_brief | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| DELETE | /api/briefs/{id} | delete_brief | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| GET | /api/skills | list_skills | Bearer JWT | .agents/agentharness/app/v3/routers/skills.py |
| GET | /api/skills/{agent_id} | get_skill | Bearer JWT | .agents/agentharness/app/v3/routers/skills.py |
| PUT | /api/skills/{agent_id} | update_skill | Bearer JWT | .agents/agentharness/app/v3/routers/skills.py |
| GET | /api/scheduler | list_scheduler | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| POST | /api/scheduler | create_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| DELETE | /api/scheduler/{id} | delete_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| POST | /api/scheduler/{id}/trigger | trigger_scheduler_job | Bearer JWT | .agents/agentharness/app/v3/routers/scheduler.py |
| GET | /api/config | get_config | Admin JWT | .agents/agentharness/app/v3/routers/config_api.py |
| PUT | /api/config | update_config | Admin JWT | .agents/agentharness/app/v3/routers/config_api.py |
| GET | /api/stats | get_stats | Bearer JWT | .agents/agentharness/app/v3/routers/config_api.py |
| GET | /api/briefing | get_briefing | Bearer JWT | .agents/agentharness/app/v3/routers/config_api.py |
| GET | /api/users | list_users | Admin JWT | .agents/agentharness/app/v3/routers/users.py |
| POST | /api/users | create_user_endpoint | Admin JWT | .agents/agentharness/app/v3/routers/users.py |
| GET | /api/users/{id} | get_user | Admin JWT | .agents/agentharness/app/v3/routers/users.py |
| PUT | /api/users/{id} | update_user | Admin JWT | .agents/agentharness/app/v3/routers/users.py |
| DELETE | /api/users/{id} | delete_user | Admin JWT | .agents/agentharness/app/v3/routers/users.py |
| GET | /api/agents | list_agents_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| POST | /api/agents | upsert_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/{agent_id} | get_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| PUT | /api/agents/{agent_id} | update_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| DELETE | /api/agents/{agent_id} | delete_agent_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/automations | list_automations | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| POST | /api/automations | create_automation | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| GET | /api/automations/{id} | get_automation | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| PUT | /api/automations/{id} | update_automation | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| DELETE | /api/automations/{id} | delete_automation | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| POST | /api/automations/{id}/trigger | trigger_automation | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| GET | /api/automations/{id}/runs | list_automation_runs | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| GET | /api/automations/{id}/documents | list_automation_docs | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| POST | /api/automations/{id}/documents | create_automation_doc | Bearer JWT | .agents/agentharness/app/v3/routers/automations.py |
| GET | /api/knowledge | list_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/knowledge | create_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/knowledge/{id} | get_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| PUT | /api/knowledge/{id} | update_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/knowledge/{id} | delete_knowledge | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/documents | list_documents | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/documents | create_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/documents/{id} | get_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| PUT | /api/documents/{id} | update_document | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/documents/{id} | delete_document_ep | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/integrations | list_integrations | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| POST | /api/integrations | upsert_integration | Bearer JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/integrations/{id} | get_integration | Admin JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| DELETE | /api/integrations/{id} | delete_integration | Admin JWT | .agents/agentharness/app/v3/routers/knowledge.py |
| GET | /api/events | list_events | Bearer JWT | .agents/agentharness/app/v3/routers/search.py |
| GET | /api/context | get_full_context | Bearer JWT | .agents/agentharness/app/v3/routers/search.py |
| GET | /api/reports | list_reports_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/reports.py |
| GET | /api/reports/types/summary | report_types_summary | Bearer JWT | .agents/agentharness/app/v3/routers/reports.py |
| GET | /api/reports/{report_id} | get_report_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/reports.py |
| DELETE | /api/reports/{report_id} | delete_report_endpoint | Admin JWT | .agents/agentharness/app/v3/routers/reports.py |
| POST | /api/reports/run | run_report_endpoint | Admin JWT | .agents/agentharness/app/v3/routers/reports.py |
| GET | /api/models | list_models | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| PUT | /api/models/toggle | toggle_model | Admin JWT | .agents/agentharness/app/v3/routers/models_api.py |
| POST | /api/models/route | route_model | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| GET | /api/models/providers | list_providers | Bearer JWT | .agents/agentharness/app/v3/routers/models_api.py |
| POST | /api/import | run_data_import | Admin JWT | .agents/agentharness/app/v3/routers/providers.py |
| WEBSOCKET | /ws | websocket_endpoint | WS auth message | .agents/agentharness/app/v3/hub_server.py |
| POST | /api/files/upload | upload_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| POST | /api/files/upload/form | upload_file_form | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files/{file_id} | get_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| DELETE | /api/files/{file_id} | delete_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files | list_files | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| POST | /api/files/{file_id}/embed | embed_file | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| GET | /api/files/_search | search_documents | Bearer JWT | .agents/agentharness/app/v3/routers/files.py |
| POST | /api/messages/{message_id}/feedback | submit_feedback | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| POST | /api/corrections | submit_correction | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/stats | get_feedback_stats | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/analyze | analyze_feedback | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/preferences | get_user_preferences | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/analyze | analyze_feedback | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/feedback/preferences | get_user_preferences | Bearer JWT | .agents/agentharness/app/v3/routers/feedback.py |
| GET | /api/briefing/morning | get_morning_briefing | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| POST | /api/briefing/morning | force_regenerate_briefing | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| GET | /api/briefing/history | get_briefing_history | Bearer JWT | .agents/agentharness/app/v3/routers/briefing.py |
| POST | /api/monitoring/run | run_monitoring | Bearer JWT | .agents/agentharness/app/v3/routers/config_api.py |
| GET | /api/monitoring/notifications | get_notifications | Bearer JWT | .agents/agentharness/app/v3/routers/notifications.py |
| POST | /api/monitoring/notifications/{notification_id}/dismiss | dismiss_monitoring_notification | Bearer JWT | .agents/agentharness/app/v3/routers/notifications.py |
| POST | /api/agents/collaborate | agent_collaboration | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/capabilities | get_agent_capabilities | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/conversations | list_agent_conversations | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| GET | /api/agents/conversations/{conversation_id} | get_conversation_history | Bearer JWT | .agents/agentharness/app/v3/routers/agents.py |
| POST | /api/email/cleanup/analyze | analyze_email_cleanup | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| GET | /api/email/cleanup/plans | list_cleanup_plans | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| GET | /api/email/cleanup/plans/{plan_id} | get_cleanup_plan | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| PUT | /api/email/cleanup/plans/{plan_id}/approve | approve_cleanup_items | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| POST | /api/email/cleanup/plans/{plan_id}/execute | execute_cleanup_plan | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| GET | /api/email/cleanup/history | get_cleanup_history | Bearer JWT | .agents/agentharness/app/v3/routers/email_cleanup.py |
| GET | /api/memory/global | list_global_memory | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| GET | /api/memory/global/search | search_global_memory | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| POST | /api/memory/global | create_global_memory_fact | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| PUT | /api/memory/global/{fact_id} | update_global_memory_fact | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| DELETE | /api/memory/global/{fact_id} | delete_global_memory_fact | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| POST | /api/memory/global/extract | extract_memory_from_conversation | Bearer JWT | .agents/agentharness/app/v3/routers/memory.py |
| POST | /api/providers/sync-free-keys | sync_free_llm_keys_endpoint | Bearer JWT | .agents/agentharness/app/v3/routers/providers.py |
| GET | /api/providers/free-keys-status | free_keys_status | Bearer JWT | .agents/agentharness/app/v3/routers/providers.py |
| GET | /api/sandbox/status | sandbox_status | Bearer JWT | .agents/agentharness/app/v3/routers/sandbox.py |
| POST | /api/sandbox/execute | sandbox_execute | Bearer JWT | .agents/agentharness/app/v3/routers/sandbox.py |
| GET | /api/intelligence/summary | intelligence_summary | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/skills | intelligence_skills | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/patterns | intelligence_patterns | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/intelligence/agent/{agent_id} | intelligence_agent | Bearer JWT | .agents/agentharness/app/v3/routers/intelligence.py |
| GET | /api/alpaca/status | alpaca_status | Public | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/account | alpaca_account | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/positions | alpaca_positions | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/positions/{symbol} | alpaca_position | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/orders | alpaca_orders | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| POST | /api/alpaca/orders | alpaca_place_order | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| DELETE | /api/alpaca/orders/{order_id} | alpaca_cancel_order | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| DELETE | /api/alpaca/orders | alpaca_cancel_all_orders | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/portfolio/history | alpaca_portfolio_history | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/assets/{symbol} | alpaca_asset | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/quotes/{symbol} | alpaca_quote | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/bars/{symbol} | alpaca_bars | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/clock | alpaca_clock | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| GET | /api/alpaca/calendar | alpaca_calendar | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
| POST | /api/alpaca/sync-positions | alpaca_sync_positions | Bearer JWT | .agents/agentharness/app/v3/routers/alpaca.py |
## Source References

- `.agents/agentharness/app/v3/hub_server.py`
- `.agents/agentharness/app/v3/core/auth.py`
- `.agents/agentharness/app/v3/core/config.py`
- `.agents/agentharness/app/v3/routers/`
