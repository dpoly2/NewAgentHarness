# Endpoint Reference

Compact generated index of all current routes in `hub_server.py`.

## Route counts by group

| Group | Count |
| --- | --- |
| / | 1 |
| /ws | 1 |
| agents | 8 |
| auth | 3 |
| automations | 9 |
| briefing | 3 |
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
| feedback | 3 |
| files | 5 |
| health | 1 |
| import | 1 |
| inez | 5 |
| integrations | 4 |
| intelligence | 4 |
| knowledge | 5 |
| memory | 8 |
| messages | 1 |
| models | 4 |
| monitoring | 1 |
| notifications | 5 |
| projects | 5 |
| prompt-templates | 5 |
| providers | 2 |
| queue | 3 |
| reports | 5 |
| runs | 3 |
| sandbox | 2 |
| scheduler | 4 |
| search | 1 |
| skills | 3 |
| stats | 1 |
| todos | 5 |
| trips | 5 |
| users | 5 |

## Full route table

| Method | Path | Handler | Auth | Line |
| --- | --- | --- | --- | --- |
| GET | / | root | Public | 1623 |
| POST | /api/auth/login | login | Public | 1628 |
| POST | /api/auth/register | register | Public | 1644 |
| GET | /api/auth/me | me | Bearer JWT | 1658 |
| GET | /api/health | health | Public | 1663 |
| POST | /api/runs | create_run | Bearer JWT | 1693 |
| GET | /api/runs | list_runs | Bearer JWT | 1700 |
| POST | /api/runs/{run_id}/cancel | cancel_run | Bearer JWT | 1712 |
| GET | /api/queue | get_queue | Bearer JWT | 1722 |
| POST | /api/queue/pause | pause_queue | Bearer JWT | 1731 |
| POST | /api/queue/resume | resume_queue | Bearer JWT | 1738 |
| GET | /api/todos | get_todos | Bearer JWT | 1745 |
| POST | /api/todos | create_todo | Bearer JWT | 1762 |
| GET | /api/todos/{id} | get_todo | Bearer JWT | 1786 |
| PUT | /api/todos/{id} | update_todo | Bearer JWT | 1795 |
| DELETE | /api/todos/{id} | delete_todo | Bearer JWT | 1807 |
| GET | /api/notifications | list_notifications | Bearer JWT | 1816 |
| POST | /api/notifications/read | mark_notifications_read | Bearer JWT | 1826 |
| DELETE | /api/notifications | clear_notifications | Bearer JWT | 1838 |
| GET | /api/trips | list_trips | Bearer JWT | 1850 |
| POST | /api/trips | create_trip | Bearer JWT | 1856 |
| GET | /api/trips/{id} | get_trip | Bearer JWT | 1877 |
| PUT | /api/trips/{id} | update_trip | Bearer JWT | 1886 |
| DELETE | /api/trips/{id} | delete_trip | Bearer JWT | 1897 |
| GET | /api/connectors | list_connectors | Bearer JWT | 1905 |
| POST | /api/connectors | create_connector | Bearer JWT | 1911 |
| GET | /api/connectors/{id} | get_connector | Bearer JWT | 1939 |
| PUT | /api/connectors/{id} | update_connector | Bearer JWT | 1948 |
| DELETE | /api/connectors/{id} | delete_connector | Bearer JWT | 1959 |
| POST | /api/connectors/{id}/test | test_connector_endpoint | Bearer JWT | 1967 |
| GET | /api/connectors/oauth/google/init | google_oauth_init | Public | 1989 |
| GET | /api/connectors/oauth/google/callback | google_oauth_callback | Public | 2009 |
| GET | /api/connectors/oauth/gmail/init | gmail_oauth_init | Public | 2056 |
| GET | /api/connectors/oauth/gmail/callback | gmail_oauth_callback | Public | 2061 |
| GET | /api/connectors/oauth/microsoft/init | microsoft_oauth_init | Public | 2066 |
| GET | /api/connectors/oauth/microsoft/callback | microsoft_oauth_callback | Public | 2086 |
| GET | /api/projects | list_projects | Bearer JWT | 2133 |
| POST | /api/projects | create_project | Bearer JWT | 2139 |
| GET | /api/projects/{id} | get_project | Bearer JWT | 2159 |
| PUT | /api/projects/{id} | update_project | Bearer JWT | 2168 |
| DELETE | /api/projects/{id} | delete_project | Bearer JWT | 2179 |
| GET | /api/clients | list_clients | Bearer JWT | 2187 |
| POST | /api/clients | create_client | Bearer JWT | 2193 |
| GET | /api/clients/{id} | get_client | Bearer JWT | 2216 |
| PUT | /api/clients/{id} | update_client | Bearer JWT | 2225 |
| DELETE | /api/clients/{id} | delete_client | Bearer JWT | 2236 |
| GET | /api/conversations | list_conversations | Bearer JWT | 2244 |
| POST | /api/conversations | create_conversation | Bearer JWT | 2250 |
| GET | /api/conversations/{id}/messages | list_messages | Bearer JWT | 2265 |
| POST | /api/conversations/{id}/messages | create_message | Bearer JWT | 2273 |
| GET | /api/search | search_conversations | Bearer JWT | 2294 |
| GET | /api/memory/agents/{agent_id} | get_memory | Bearer JWT | 2381 |
| PUT | /api/memory/agents/{agent_id} | update_memory | Bearer JWT | 2387 |
| GET | /api/prompt-templates | list_prompt_templates | Bearer JWT | 2395 |
| POST | /api/prompt-templates | create_prompt_template | Bearer JWT | 2435 |
| PUT | /api/prompt-templates/{template_id} | update_prompt_template | Bearer JWT | 2485 |
| DELETE | /api/prompt-templates/{template_id} | delete_prompt_template | Bearer JWT | 2548 |
| POST | /api/prompt-templates/{template_id}/use | use_prompt_template | Bearer JWT | 2575 |
| POST | /api/inez/chat | inez_chat | Bearer JWT | 2609 |
| GET | /api/inez/brief | inez_morning_brief | Bearer JWT | 2740 |
| GET | /api/inez/status | inez_status | Bearer JWT | 2757 |
| GET | /api/inez/memory | inez_memory | Bearer JWT | 2775 |
| DELETE | /api/inez/memory/facts/{key} | delete_inez_fact | Bearer JWT | 2832 |
| GET | /api/briefs | list_briefs | Bearer JWT | 2844 |
| POST | /api/briefs | create_brief | Bearer JWT | 2853 |
| DELETE | /api/briefs/{id} | delete_brief | Bearer JWT | 2865 |
| GET | /api/skills | list_skills | Bearer JWT | 2873 |
| GET | /api/skills/{agent_id} | get_skill | Bearer JWT | 2886 |
| PUT | /api/skills/{agent_id} | update_skill | Bearer JWT | 2892 |
| GET | /api/scheduler | list_scheduler | Bearer JWT | 2900 |
| POST | /api/scheduler | create_scheduler_job | Bearer JWT | 2912 |
| DELETE | /api/scheduler/{id} | delete_scheduler_job | Bearer JWT | 2951 |
| POST | /api/scheduler/{id}/trigger | trigger_scheduler_job | Bearer JWT | 2965 |
| GET | /api/config | get_config | Admin JWT | 2976 |
| PUT | /api/config | update_config | Admin JWT | 2982 |
| GET | /api/stats | get_stats | Bearer JWT | 2993 |
| GET | /api/briefing | get_briefing | Bearer JWT | 2999 |
| GET | /api/users | list_users | Admin JWT | 3005 |
| POST | /api/users | create_user_endpoint | Admin JWT | 3016 |
| GET | /api/users/{id} | get_user | Admin JWT | 3024 |
| PUT | /api/users/{id} | update_user | Admin JWT | 3033 |
| DELETE | /api/users/{id} | delete_user | Admin JWT | 3045 |
| GET | /api/agents | list_agents_endpoint | Bearer JWT | 3057 |
| POST | /api/agents | upsert_agent_endpoint | Bearer JWT | 3075 |
| GET | /api/agents/{agent_id} | get_agent_endpoint | Bearer JWT | 3123 |
| PUT | /api/agents/{agent_id} | update_agent_endpoint | Bearer JWT | 3132 |
| DELETE | /api/agents/{agent_id} | delete_agent_endpoint | Bearer JWT | 3155 |
| GET | /api/automations | list_automations | Bearer JWT | 3173 |
| POST | /api/automations | create_automation | Bearer JWT | 3188 |
| GET | /api/automations/{id} | get_automation | Bearer JWT | 3202 |
| PUT | /api/automations/{id} | update_automation | Bearer JWT | 3210 |
| DELETE | /api/automations/{id} | delete_automation | Bearer JWT | 3220 |
| POST | /api/automations/{id}/trigger | trigger_automation | Bearer JWT | 3227 |
| GET | /api/automations/{id}/runs | list_automation_runs | Bearer JWT | 3244 |
| GET | /api/automations/{id}/documents | list_automation_docs | Bearer JWT | 3250 |
| POST | /api/automations/{id}/documents | create_automation_doc | Bearer JWT | 3256 |
| GET | /api/knowledge | list_knowledge | Bearer JWT | 3275 |
| POST | /api/knowledge | create_knowledge | Bearer JWT | 3309 |
| GET | /api/knowledge/{id} | get_knowledge | Bearer JWT | 3322 |
| PUT | /api/knowledge/{id} | update_knowledge | Bearer JWT | 3330 |
| DELETE | /api/knowledge/{id} | delete_knowledge | Bearer JWT | 3342 |
| GET | /api/documents | list_documents | Bearer JWT | 3354 |
| POST | /api/documents | create_document | Bearer JWT | 3372 |
| GET | /api/documents/{id} | get_document | Bearer JWT | 3386 |
| PUT | /api/documents/{id} | update_document | Bearer JWT | 3394 |
| DELETE | /api/documents/{id} | delete_document_ep | Bearer JWT | 3404 |
| GET | /api/integrations | list_integrations | Bearer JWT | 3416 |
| POST | /api/integrations | upsert_integration | Bearer JWT | 3436 |
| GET | /api/integrations/{id} | get_integration | Admin JWT | 3449 |
| DELETE | /api/integrations/{id} | delete_integration | Admin JWT | 3457 |
| GET | /api/events | list_events | Bearer JWT | 3467 |
| GET | /api/context | get_full_context | Bearer JWT | 3486 |
| GET | /api/reports | list_reports_endpoint | Bearer JWT | 3515 |
| GET | /api/reports/types/summary | report_types_summary | Bearer JWT | 3531 |
| GET | /api/reports/{report_id} | get_report_endpoint | Bearer JWT | 3541 |
| DELETE | /api/reports/{report_id} | delete_report_endpoint | Admin JWT | 3552 |
| POST | /api/reports/run | run_report_endpoint | Admin JWT | 3562 |
| GET | /api/models | list_models | Bearer JWT | 3581 |
| PUT | /api/models/toggle | toggle_model | Admin JWT | 3589 |
| POST | /api/models/route | route_model | Bearer JWT | 3598 |
| GET | /api/models/providers | list_providers | Bearer JWT | 3612 |
| POST | /api/import | run_data_import | Admin JWT | 3638 |
| WEBSOCKET | /ws | websocket_endpoint | WS auth message | 3656 |
| POST | /api/files/upload | upload_file | Public | 3715 |
| GET | /api/files/{file_id} | get_file | Public | 3761 |
| GET | /api/files | list_files | Public | 3784 |
| POST | /api/files/{file_id}/embed | embed_file | Public | 3804 |
| GET | /api/files/search | search_documents | Public | 3827 |
| POST | /api/messages/{message_id}/feedback | submit_feedback | Public | 3854 |
| POST | /api/corrections | submit_correction | Public | 3910 |
| GET | /api/feedback/stats | get_feedback_stats | Public | 3967 |
| GET | /api/feedback/analyze | analyze_feedback | Public | 4017 |
| GET | /api/feedback/preferences | get_user_preferences | Public | 4034 |
| GET | /api/briefing/morning | get_morning_briefing | Public | 4053 |
| GET | /api/briefing/history | get_briefing_history | Public | 4098 |
| POST | /api/monitoring/run | run_monitoring | Public | 4127 |
| GET | /api/notifications | get_notifications | Public | 4141 |
| POST | /api/notifications/{notification_id}/dismiss | dismiss_notification | Public | 4186 |
| POST | /api/agents/collaborate | agent_collaboration | Public | 4209 |
| GET | /api/agents/capabilities | get_agent_capabilities | Public | 4239 |
| GET | /api/agents/conversations/{conversation_id} | get_conversation_history | Public | 4257 |
| POST | /api/email/cleanup/analyze | analyze_email_cleanup | Public | 4276 |
| GET | /api/email/cleanup/plans | list_cleanup_plans | Public | 4301 |
| GET | /api/email/cleanup/plans/{plan_id} | get_cleanup_plan | Public | 4324 |
| PUT | /api/email/cleanup/plans/{plan_id}/approve | approve_cleanup_items | Public | 4343 |
| POST | /api/email/cleanup/plans/{plan_id}/execute | execute_cleanup_plan | Public | 4375 |
| GET | /api/email/cleanup/history | get_cleanup_history | Public | 4396 |
| GET | /api/memory/global | list_global_memory | Bearer JWT | 4427 |
| GET | /api/memory/global/search | search_global_memory | Bearer JWT | 4444 |
| POST | /api/memory/global | create_global_memory_fact | Bearer JWT | 4466 |
| PUT | /api/memory/global/{fact_id} | update_global_memory_fact | Bearer JWT | 4491 |
| DELETE | /api/memory/global/{fact_id} | delete_global_memory_fact | Bearer JWT | 4518 |
| POST | /api/memory/global/extract | extract_memory_from_conversation | Bearer JWT | 4532 |
| POST | /api/providers/sync-free-keys | sync_free_llm_keys_endpoint | Bearer JWT | 4554 |
| GET | /api/providers/free-keys-status | free_keys_status | Bearer JWT | 4571 |
| GET | /api/sandbox/status | sandbox_status | Bearer JWT | 4605 |
| POST | /api/sandbox/execute | sandbox_execute | Bearer JWT | 4615 |
| GET | /api/intelligence/summary | intelligence_summary | Bearer JWT | 4658 |
| GET | /api/intelligence/skills | intelligence_skills | Bearer JWT | 4668 |
| GET | /api/intelligence/patterns | intelligence_patterns | Bearer JWT | 4679 |
| GET | /api/intelligence/agent/{agent_id} | intelligence_agent | Bearer JWT | 4693 |

## Source

- `.agents/agentharness/app/v3/hub_server.py`
