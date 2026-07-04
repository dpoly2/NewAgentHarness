# 03-DATA-CONTRACT

_Generated from the live SQLite database and current source files on 2026-07-03._

## Canonical database

- **Path:** `D:\projects\NewAgentHarness\.agents\agentharness\memory\runs_v3.db`
- **Engine:** SQLite for the inspected live database; several helpers also contain Postgres-aware DDL translation paths.
- **Raw table count:** **62** rows in `sqlite_master` where `type = "table"`.
- **Application-owned table count:** **61** when `sqlite_sequence` is excluded.

## 61 vs 62 discrepancy

The live database contains **62** raw tables because SQLite exposes `sqlite_sequence` whenever AUTOINCREMENT tables exist. That table is not part of the ArchonHub domain model. Excluding it leaves **61** non-system tables, which is the correct application-level count.

## Source ownership

### Core schema owners

- `core\database.py`: `agent_memory`, `agent_registry`, `alpaca_orders`, `automation_documents`, `automation_runs`, `automations`, `clients`, `conversations`, `daily_briefs`, `documents`, `email_cleanup_items`, `email_cleanup_plans`, `email_connectors`, `events_log`, `global_memory`, `hub_config`, `implementation_plans`, `integrations`, `job_queue`, `knowledge_base`, `market_paper_trades`, `market_positions`, `market_trade_theories`, `market_watchlist`, `notifications`, `plan_node_events`, `projects`, `prompt_templates`, `reports`, `runs`, `scheduled_jobs`, `skills`, `todos`, `travel_trips`, `users`, `worker_nodes`, `ws_events`
- `hub_db.py`: `attachments`, `messages`, `projects`, `clients`, `reports`, `skills`, `users`, `todos`, `notifications`, `documents`, `conversations`

### Targeted migrations and add-on modules

- `add_agent_messaging.py`: `agent_messages`, `agent_conversations`, `agent_capabilities`
- `add_feedback_system.py`: `message_feedback`, `corrections`, `user_style_preferences`
- `add_file_uploads.py`: `uploaded_files`, `file_chunks`
- `add_fts_search.py`: `messages_fts`, `messages_fts_config`, `messages_fts_data`, `messages_fts_docsize`, `messages_fts_idx`
- `progressive_intelligence.py`: `agent_skill_levels`, `reflexion_log`, `interaction_patterns`
- `morning_brief.py`: `morning_briefs`
- `run_events.py`: `run_events`

## Domain grouping

### Execution and coordination

`job_queue`, `runs`, `run_events`, `worker_nodes`, `ws_events`, `scheduled_jobs`, `notifications`, `plan_node_events`, `implementation_plans`.

### Agents, skills, and memory

`agent_registry`, `agent_memory`, `skills`, `agent_skill_levels`, `reflexion_log`, `global_memory`, `interaction_patterns`, `user_preferences`, `user_style_preferences`.

### Conversations and collaboration

`conversations`, `messages`, `attachments`, `agent_messages`, `agent_conversations`, `agent_capabilities`, `message_feedback`, `corrections`.

### Projects, documents, and knowledge

`projects`, `clients`, `documents`, `knowledge_base`, `prompt_templates`, `integrations`, `automations`, `automation_runs`, `automation_documents`, `daily_briefs`, `morning_briefs`.

### Market and trading

`alpaca_orders`, `market_paper_trades`, `market_positions`, `market_trade_theories`, `market_watchlist`, `tracked_politicians`, `politician_trades`, `copy_trade_signals`.

### Search and file ingestion

`uploaded_files`, `file_chunks`, `messages_fts`, `messages_fts_config`, `messages_fts_data`, `messages_fts_docsize`, `messages_fts_idx`.

### Operational domain tables

`todos`, `travel_trips`, `email_connectors`, `email_cleanup_plans`, `email_cleanup_items`, `hub_config`, `events_log`, `reports`, `users`.

## Full table inventory

### `agent_capabilities`

Capability catalog for orchestrating specialists.

- **Columns:** `agent_name` TEXT PK, `display_name` TEXT, `description` TEXT, `capabilities_json` TEXT, `dependencies` TEXT, `response_time_avg_ms` INTEGER, `success_rate` REAL, `total_requests` INTEGER, `active` BOOLEAN, `updated_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE agent_capabilities (             agent_name TEXT PRIMARY KEY,             display_name TEXT NOT NULL,             description TEXT,             capabilities_json TEXT NOT NULL,  -- JSON: ["analyze_market", "fetch_prices", etc]             dependencies TEXT,  -- JSON: other agents this agent depends on             response_time_avg_ms INTEGER DEFAULT 0,             success_rate REAL DEFAULT 1.0,             total_requests INTEGER DEFAULT 0,             active BOOLEAN DEFAULT 1,   ...`

### `agent_conversations`

Persisted multi-agent collaboration threads.

- **Columns:** `conversation_id` TEXT PK, `user_id` TEXT, `initiator_agent` TEXT, `participant_agents` TEXT, `goal` TEXT, `status` TEXT, `created_at` TIMESTAMP, `completed_at` TIMESTAMP, `message_count` INTEGER, `result_json` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE agent_conversations (             conversation_id TEXT PRIMARY KEY,             user_id TEXT NOT NULL,             initiator_agent TEXT NOT NULL,             participant_agents TEXT NOT NULL,  -- JSON array of agent names             goal TEXT NOT NULL,             status TEXT DEFAULT 'active',  -- 'active', 'completed', 'failed'             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,             completed_at TIMESTAMP,             message_count INTEGER DEFAULT 0,            ...`

### `agent_memory`

Per-agent key/value memory and run snippets.

- **Columns:** `id` INTEGER PK, `agent_id` TEXT, `key` TEXT, `value` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE agent_memory (             id INTEGER PRIMARY KEY AUTOINCREMENT,             agent_id TEXT,             key TEXT,             value TEXT,             updated_at TEXT,             UNIQUE(agent_id, key)         )`

### `agent_messages`

Message queue for inter-agent requests/responses.

- **Columns:** `message_id` TEXT PK, `conversation_id` TEXT, `sender_agent` TEXT, `recipient_agent` TEXT, `message_type` TEXT, `payload_json` TEXT, `status` TEXT, `created_at` TIMESTAMP, `delivered_at` TIMESTAMP, `completed_at` TIMESTAMP, `error_message` TEXT, `timeout_seconds` INTEGER, `retry_count` INTEGER.
- **SQLite definition excerpt:** `CREATE TABLE agent_messages (             message_id TEXT PRIMARY KEY,             conversation_id TEXT NOT NULL,             sender_agent TEXT NOT NULL,             recipient_agent TEXT NOT NULL,             message_type TEXT NOT NULL,  -- 'request', 'response', 'broadcast', 'error'             payload_json TEXT NOT NULL,             status TEXT DEFAULT 'pending',  -- 'pending', 'delivered', 'processing', 'completed', 'failed'             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      ...`

### `agent_registry`

Registered agents, prompts, config, and metadata.

- **Columns:** `id` TEXT PK, `agent_id` TEXT, `name` TEXT, `type` TEXT, `role` TEXT, `description` TEXT, `project_slug` TEXT, `capabilities` TEXT, `integrations` TEXT, `status` TEXT, `system_prompt` TEXT, `config` TEXT, `metadata` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE agent_registry (             id TEXT PRIMARY KEY,             agent_id TEXT UNIQUE NOT NULL,             name TEXT NOT NULL,             type TEXT DEFAULT 'specialist',             role TEXT DEFAULT '',             description TEXT DEFAULT '',             project_slug TEXT DEFAULT '',             capabilities TEXT DEFAULT '[]',             integrations TEXT DEFAULT '[]',             status TEXT DEFAULT 'active',             system_prompt TEXT DEFAULT '',             config TEXT D...`

### `agent_skill_levels`

Progressive-intelligence skill scoring summary per agent.

- **Columns:** `agent_id` TEXT PK, `total_runs` INTEGER, `successful_runs` INTEGER, `avg_quality` REAL, `skill_level` TEXT, `last_reflexion` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE agent_skill_levels (             agent_id        TEXT PRIMARY KEY,             total_runs      INTEGER DEFAULT 0,             successful_runs INTEGER DEFAULT 0,             avg_quality     REAL    DEFAULT 0.0,             skill_level     TEXT    DEFAULT 'novice',             last_reflexion  TEXT,             updated_at      TEXT         )`

### `alpaca_orders`

Local mirror of submitted/cancelled Alpaca orders.

- **Columns:** `id` TEXT PK, `symbol` TEXT, `side` TEXT, `order_type` TEXT, `qty` REAL, `limit_price` REAL, `stop_price` REAL, `time_in_force` TEXT, `status` TEXT, `agent_reason` TEXT, `submitted_by` TEXT, `alpaca_response` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE alpaca_orders (                 id TEXT PRIMARY KEY,                 symbol TEXT,                 side TEXT,                 order_type TEXT,                 qty REAL,                 limit_price REAL,                 stop_price REAL,                 time_in_force TEXT,                 status TEXT,                 agent_reason TEXT DEFAULT '',                 submitted_by TEXT DEFAULT '',                 alpaca_response TEXT,                 created_at TEXT,                 updat...`

### `attachments`

Message-level attachment metadata.

- **Columns:** `id` TEXT PK, `entity_type` TEXT, `entity_id` TEXT, `filename` TEXT, `original_name` TEXT, `file_path` TEXT, `mime_type` TEXT, `file_size` INTEGER, `uploaded_by` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE attachments (             id TEXT PRIMARY KEY,             entity_type TEXT NOT NULL,             entity_id TEXT NOT NULL,             filename TEXT DEFAULT '',             original_name TEXT DEFAULT '',             file_path TEXT DEFAULT '',             mime_type TEXT DEFAULT '',             file_size INTEGER DEFAULT 0,             uploaded_by TEXT DEFAULT '',             created_at TEXT         )`

### `automation_documents`

Documents produced by automation runs.

- **Columns:** `id` TEXT PK, `automation_id` TEXT, `run_id` TEXT, `title` TEXT, `doc_type` TEXT, `content` TEXT, `file_path` TEXT, `status` TEXT, `reviewed_by` TEXT, `review_notes` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE automation_documents (             id TEXT PRIMARY KEY,             automation_id TEXT DEFAULT '',             run_id TEXT DEFAULT '',             title TEXT DEFAULT '',             doc_type TEXT DEFAULT 'report',             content TEXT DEFAULT '',             file_path TEXT DEFAULT '',             status TEXT DEFAULT 'draft',             reviewed_by TEXT DEFAULT '',             review_notes TEXT DEFAULT '',             created_at TEXT,             updated_at TEXT         )`

### `automation_runs`

Execution history for automations.

- **Columns:** `id` TEXT PK, `automation_id` TEXT, `automation_slug` TEXT, `triggered_by` TEXT, `status` TEXT, `output` TEXT, `error` TEXT, `duration_sec` REAL, `metadata` TEXT, `started_at` TEXT, `completed_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE automation_runs (             id TEXT PRIMARY KEY,             automation_id TEXT NOT NULL,             automation_slug TEXT DEFAULT '',             triggered_by TEXT DEFAULT 'manual',             status TEXT DEFAULT 'running',             output TEXT DEFAULT '',             error TEXT DEFAULT '',             duration_sec REAL DEFAULT 0,             metadata TEXT DEFAULT '{}',             started_at TEXT,             completed_at TEXT,             FOREIGN KEY (automation_id) REFE...`

### `automations`

Automation definitions and trigger settings.

- **Columns:** `id` TEXT PK, `slug` TEXT, `name` TEXT, `description` TEXT, `project_slug` TEXT, `agent_id` TEXT, `trigger_type` TEXT, `trigger_config` TEXT, `steps` TEXT, `status` TEXT, `last_run_at` TEXT, `last_run_status` TEXT, `run_count` INTEGER, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE automations (             id TEXT PRIMARY KEY,             slug TEXT UNIQUE,             name TEXT NOT NULL,             description TEXT DEFAULT '',             project_slug TEXT DEFAULT '',             agent_id TEXT DEFAULT '',             trigger_type TEXT DEFAULT 'manual',             trigger_config TEXT DEFAULT '{}',             steps TEXT DEFAULT '[]',             status TEXT DEFAULT 'active',             last_run_at TEXT,             last_run_status TEXT DEFAULT '',       ...`

### `clients`

Client CRM records linked to projects.

- **Columns:** `id` TEXT PK, `slug` TEXT, `name` TEXT, `business_type` TEXT, `service` TEXT, `contact_name` TEXT, `contact_email` TEXT, `engagement` TEXT, `status` TEXT, `project_slug` TEXT, `notes` TEXT, `created_at` TEXT, `updated_at` TEXT, `phone` TEXT, `website` TEXT, `contact_role` TEXT, `address` TEXT, `tags` TEXT, `metadata` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE clients (             id TEXT PRIMARY KEY,             slug TEXT UNIQUE,             name TEXT,             business_type TEXT DEFAULT '',             service TEXT DEFAULT '',             contact_name TEXT DEFAULT '',             contact_email TEXT DEFAULT '',             engagement TEXT DEFAULT 'retainer',             status TEXT DEFAULT 'active',             project_slug TEXT DEFAULT '',             notes TEXT DEFAULT '',             created_at TEXT,             updated_at TEXT...`

### `conversations`

User/agent conversation threads.

- **Columns:** `id` TEXT PK, `slug` TEXT, `title` TEXT, `created_at` TEXT, `updated_at` TEXT, `project_id` TEXT, `client_id` TEXT, `summary` TEXT, `tags` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE conversations (             id TEXT PRIMARY KEY,             slug TEXT DEFAULT 'global',             title TEXT,             created_at TEXT,             updated_at TEXT         , project_id TEXT DEFAULT '', client_id TEXT DEFAULT '', summary TEXT DEFAULT '', tags TEXT DEFAULT '[]')`

### `copy_trade_signals`

Generated congressional-trade copy signals awaiting/after CRO review.

- **Columns:** `id` TEXT PK, `politician_trade_id` TEXT, `politician_id` TEXT, `politician_name` TEXT, `tracking_reason` TEXT, `ticker` TEXT, `signal_side` TEXT, `signal_strength` TEXT, `copy_reason` TEXT, `estimated_qty` REAL, `status` TEXT, `cro_notes` TEXT, `alpaca_order_id` TEXT, `created_at` TEXT, `reviewed_at` TEXT, `executed_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE copy_trade_signals (                 id TEXT PRIMARY KEY,                 politician_trade_id TEXT,                 politician_id TEXT,                 politician_name TEXT,                 tracking_reason TEXT DEFAULT '',                 ticker TEXT,                 signal_side TEXT,                 signal_strength TEXT DEFAULT 'moderate',                 copy_reason TEXT DEFAULT '',                 estimated_qty REAL DEFAULT 0,                 status TEXT DEFAULT 'pending',    ...`

### `corrections`

User-provided corrections for learning.

- **Columns:** `correction_id` TEXT PK, `message_id` TEXT, `user_id` TEXT, `conversation_id` TEXT, `original_intent` TEXT, `corrected_intent` TEXT, `correction_text` TEXT, `correction_type` TEXT, `applied` BOOLEAN, `created_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE corrections (             correction_id TEXT PRIMARY KEY,             message_id TEXT NOT NULL,             user_id TEXT NOT NULL,             conversation_id TEXT,             original_intent TEXT,  -- What user originally asked             corrected_intent TEXT NOT NULL,  -- What user actually meant             correction_text TEXT NOT NULL,  -- Full correction message             correction_type TEXT DEFAULT 'clarification',  -- 'clarification', 'error', 'misunderstanding'    ...`

### `daily_briefs`

Stored daily briefing artifacts.

- **Columns:** `id` TEXT PK, `content` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE daily_briefs (             id TEXT PRIMARY KEY,             content TEXT,             created_at TEXT         )`

### `documents`

Long-form documents and generated assets.

- **Columns:** `id` TEXT PK, `title` TEXT, `doc_type` TEXT, `content` TEXT, `format` TEXT, `project_slug` TEXT, `client_id` TEXT, `entity_type` TEXT, `entity_id` TEXT, `version` INTEGER, `status` TEXT, `tags` TEXT, `created_by` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE documents (             id TEXT PRIMARY KEY,             title TEXT NOT NULL,             doc_type TEXT DEFAULT 'general',             content TEXT DEFAULT '',             format TEXT DEFAULT 'markdown',             project_slug TEXT DEFAULT '',             client_id TEXT DEFAULT '',             entity_type TEXT DEFAULT '',             entity_id TEXT DEFAULT '',             version INTEGER DEFAULT 1,             status TEXT DEFAULT 'draft',             tags TEXT DEFAULT '[]',    ...`

### `email_cleanup_items`

Per-message cleanup recommendations.

- **Columns:** `id` TEXT PK, `plan_id` TEXT, `email_id` TEXT, `category` TEXT, `subject` TEXT, `from_address` TEXT, `email_date` TIMESTAMP, `size_bytes` INTEGER, `confidence` REAL, `reason` TEXT, `action` TEXT, `approved` INTEGER, `executed` INTEGER, `rolled_back` INTEGER, `created_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE email_cleanup_items (     id TEXT PRIMARY KEY,     plan_id TEXT NOT NULL,     email_id TEXT NOT NULL,     category TEXT NOT NULL,     subject TEXT,     from_address TEXT,     email_date TIMESTAMP,     size_bytes INTEGER DEFAULT 0,     confidence REAL DEFAULT 0.5,     reason TEXT,     action TEXT DEFAULT 'archive',     approved INTEGER DEFAULT 0,     executed INTEGER DEFAULT 0,     rolled_back INTEGER DEFAULT 0,     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )`

### `email_cleanup_plans`

Cleanup plans produced by the email analyzer.

- **Columns:** `id` TEXT PK, `account_id` TEXT, `status` TEXT, `total_emails` INTEGER, `suggested_cleanup_count` INTEGER, `estimated_space_mb` INTEGER, `created_at` TIMESTAMP, `executed_at` TIMESTAMP, `rolled_back_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE email_cleanup_plans (     id TEXT PRIMARY KEY,     account_id TEXT NOT NULL,     status TEXT DEFAULT 'pending',     total_emails INTEGER DEFAULT 0,     suggested_cleanup_count INTEGER DEFAULT 0,     estimated_space_mb INTEGER DEFAULT 0,     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,     executed_at TIMESTAMP,     rolled_back_at TIMESTAMP )`

### `email_connectors`

IMAP/SMTP/OAuth connector records.

- **Columns:** `id` TEXT PK, `label` TEXT, `email_address` TEXT, `provider` TEXT, `auth_type` TEXT, `imap_host` TEXT, `imap_port` INTEGER, `smtp_host` TEXT, `smtp_port` INTEGER, `username` TEXT, `credentials` TEXT, `status` TEXT, `last_error` TEXT, `last_synced` TEXT, `created_at` TEXT, `updated_at` TEXT, `oauth_client_id` TEXT, `oauth_client_secret` TEXT, `token_expires_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE email_connectors (             id TEXT PRIMARY KEY,             label TEXT,             email_address TEXT,             provider TEXT DEFAULT 'imap',             auth_type TEXT DEFAULT 'password',             imap_host TEXT,             imap_port INTEGER DEFAULT 993,             smtp_host TEXT,             smtp_port INTEGER DEFAULT 587,             username TEXT,             credentials TEXT DEFAULT '{}',             status TEXT DEFAULT 'pending',             last_error TEXT,    ...`

### `events_log`

General event log used by automations and agent writes.

- **Columns:** `id` INTEGER PK, `event_type` TEXT, `entity_type` TEXT, `entity_id` TEXT, `actor` TEXT, `summary` TEXT, `detail` TEXT, `level` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE events_log (             id INTEGER PRIMARY KEY AUTOINCREMENT,             event_type TEXT NOT NULL,             entity_type TEXT DEFAULT '',             entity_id TEXT DEFAULT '',             actor TEXT DEFAULT 'system',             summary TEXT DEFAULT '',             detail TEXT DEFAULT '{}',             level TEXT DEFAULT 'info',             created_at TEXT         )`

### `file_chunks`

Chunked document text and embeddings for RAG search.

- **Columns:** `chunk_id` TEXT PK, `file_id` TEXT, `chunk_index` INTEGER, `chunk_text` TEXT, `chunk_tokens` INTEGER, `page_number` INTEGER, `embedding_vector` TEXT, `embedding_model` TEXT, `created_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE file_chunks (             chunk_id TEXT PRIMARY KEY,             file_id TEXT NOT NULL,             chunk_index INTEGER NOT NULL,             chunk_text TEXT NOT NULL,             chunk_tokens INTEGER DEFAULT 0,             page_number INTEGER,  -- For PDFs             embedding_vector TEXT,  -- JSON array of floats             embedding_model TEXT DEFAULT 'text-embedding-3-small',             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                          FOREIGN KEY (f...`

### `global_memory`

Cross-agent/global memory facts.

- **Columns:** `id` TEXT PK, `category` TEXT, `key` TEXT, `value` TEXT, `source` TEXT, `confidence` REAL, `importance` INTEGER, `last_verified` TEXT, `usage_count` INTEGER, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE global_memory (                 id TEXT PRIMARY KEY,                 category TEXT NOT NULL,                 key TEXT NOT NULL,                 value TEXT NOT NULL,                 source TEXT DEFAULT 'user',                 confidence REAL DEFAULT 1.0,                 importance INTEGER DEFAULT 5,                 last_verified TEXT,                 usage_count INTEGER DEFAULT 0,                 created_at TEXT,                 updated_at TEXT,                 UNIQUE(category, ke...`

### `hub_config`

Key/value server configuration and scheduler lease state.

- **Columns:** `key` TEXT PK, `value` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE hub_config (             key TEXT PRIMARY KEY,             value TEXT,             updated_at TEXT         )`

### `implementation_plans`

Structured execution plans.

- **Columns:** `plan_id` TEXT PK, `title` TEXT, `project` TEXT, `status` TEXT, `authored_by` TEXT, `graph_json` TEXT, `preflight_json` TEXT, `version` INTEGER, `run_id` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE implementation_plans (                 plan_id TEXT PRIMARY KEY,                 title TEXT NOT NULL,                 project TEXT DEFAULT '',                 status TEXT DEFAULT 'draft',                 authored_by TEXT DEFAULT 'human',                 graph_json TEXT,                 preflight_json TEXT,                 version INTEGER DEFAULT 1,                 run_id TEXT,                 created_at TEXT,                 updated_at TEXT             )`

### `integrations`

External integration registry.

- **Columns:** `id` TEXT PK, `name` TEXT, `provider` TEXT, `entity_type` TEXT, `entity_id` TEXT, `auth_type` TEXT, `credentials` TEXT, `scope` TEXT, `status` TEXT, `expires_at` TEXT, `last_used_at` TEXT, `metadata` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE integrations (             id TEXT PRIMARY KEY,             name TEXT NOT NULL,             provider TEXT NOT NULL,             entity_type TEXT DEFAULT 'global',             entity_id TEXT DEFAULT '',             auth_type TEXT DEFAULT 'oauth2',             credentials TEXT DEFAULT '{}',             scope TEXT DEFAULT '',             status TEXT DEFAULT 'pending',             expires_at TEXT,             last_used_at TEXT,             metadata TEXT DEFAULT '{}',             crea...`

### `interaction_patterns`

Topic-frequency/proactive-intelligence patterns.

- **Columns:** `id` TEXT PK, `user_id` TEXT, `topic` TEXT, `agent_id` TEXT, `occurrence_count` INTEGER, `last_seen` TEXT, `first_seen` TEXT, `typical_time` TEXT, `proactive_sent` INTEGER.
- **SQLite definition excerpt:** `CREATE TABLE interaction_patterns (             id              TEXT PRIMARY KEY,             user_id         TEXT DEFAULT 'default',             topic           TEXT,             agent_id        TEXT,             occurrence_count INTEGER DEFAULT 1,             last_seen       TEXT,             first_seen      TEXT,             typical_time    TEXT,             proactive_sent  INTEGER DEFAULT 0         )`

### `job_queue`

Queued background jobs claimed by DB workers.

- **Columns:** `id` TEXT PK, `agent_id` TEXT, `project` TEXT, `graph` TEXT, `task` TEXT, `priority` TEXT, `status` TEXT, `max_revisions` INTEGER, `queued_at` TEXT, `started_at` TEXT, `completed_at` TEXT, `job_data` TEXT, `worker_id` TEXT, `claimed_at` TEXT, `heartbeat_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE job_queue (             id TEXT PRIMARY KEY,             agent_id TEXT,             project TEXT,             graph TEXT DEFAULT 'reflexion',             task TEXT,             priority TEXT DEFAULT 'normal',             status TEXT DEFAULT 'queued',             max_revisions INTEGER DEFAULT 2,             queued_at TEXT,             started_at TEXT,             completed_at TEXT,             job_data TEXT DEFAULT '{}'         , worker_id TEXT DEFAULT '', claimed_at TEXT DEFAULT ...`

### `knowledge_base`

Knowledge entries written by users and agents.

- **Columns:** `id` TEXT PK, `title` TEXT, `content` TEXT, `source` TEXT, `source_type` TEXT, `category` TEXT, `tags` TEXT, `project_slug` TEXT, `agent_id` TEXT, `is_active` INTEGER, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE knowledge_base (             id TEXT PRIMARY KEY,             title TEXT NOT NULL,             content TEXT NOT NULL,             source TEXT DEFAULT '',             source_type TEXT DEFAULT 'manual',             category TEXT DEFAULT 'general',             tags TEXT DEFAULT '[]',             project_slug TEXT DEFAULT '',             agent_id TEXT DEFAULT '',             is_active INTEGER DEFAULT 1,             created_at TEXT,             updated_at TEXT         )`

### `market_paper_trades`

Paper-trade history for market experiments.

- **Columns:** `id` TEXT PK, `theory_id` TEXT, `ticker` TEXT, `name` TEXT, `position_type` TEXT, `direction` TEXT, `shares` REAL, `entry_price` REAL, `exit_price` REAL, `current_price` REAL, `target_price` REAL, `stop_price` REAL, `capital_used` REAL, `pnl` REAL, `pnl_pct` REAL, `status` TEXT, `source` TEXT, `agent_id` TEXT, `thesis` TEXT, `analysis` TEXT, `opened_at` TEXT, `closed_at` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE market_paper_trades (             id TEXT PRIMARY KEY,             theory_id TEXT DEFAULT '',             ticker TEXT NOT NULL,             name TEXT DEFAULT '',             position_type TEXT DEFAULT 'equity',             direction TEXT DEFAULT 'long',             shares REAL DEFAULT 0,             entry_price REAL DEFAULT 0,             exit_price REAL DEFAULT 0,             current_price REAL DEFAULT 0,             target_price REAL DEFAULT 0,             stop_price REAL DEFAU...`

### `market_positions`

Tracked market positions and holdings.

- **Columns:** `id` TEXT PK, `ticker` TEXT, `name` TEXT, `position_type` TEXT, `action` TEXT, `shares` REAL, `entry_price` REAL, `current_price` REAL, `target_price` REAL, `stop_price` REAL, `pnl` REAL, `pnl_pct` REAL, `notes` TEXT, `status` TEXT, `project_slug` TEXT, `created_at` TEXT, `updated_at` TEXT, `qty` REAL, `market_value` REAL, `cost_basis` REAL, `side` TEXT, `unrealized_pnl` REAL.
- **SQLite definition excerpt:** `CREATE TABLE market_positions (             id TEXT PRIMARY KEY,             ticker TEXT NOT NULL,             name TEXT DEFAULT '',             position_type TEXT DEFAULT 'equity',             action TEXT DEFAULT 'long',             shares REAL DEFAULT 0,             entry_price REAL DEFAULT 0,             current_price REAL DEFAULT 0,             target_price REAL DEFAULT 0,             stop_price REAL DEFAULT 0,             pnl REAL DEFAULT 0,             pnl_pct REAL DEFAULT 0,           ...`

### `market_trade_theories`

Stored market theses and rationale.

- **Columns:** `id` TEXT PK, `name` TEXT, `description` TEXT, `hypothesis` TEXT, `starting_balance` REAL, `current_balance` REAL, `status` TEXT, `win_count` INTEGER, `loss_count` INTEGER, `total_trades` INTEGER, `total_pnl` REAL, `agent_id` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE market_trade_theories (             id TEXT PRIMARY KEY,             name TEXT NOT NULL,             description TEXT DEFAULT '',             hypothesis TEXT DEFAULT '',             starting_balance REAL DEFAULT 100000,             current_balance REAL DEFAULT 100000,             status TEXT DEFAULT 'active',             win_count INTEGER DEFAULT 0,             loss_count INTEGER DEFAULT 0,             total_trades INTEGER DEFAULT 0,             total_pnl REAL DEFAULT 0,         ...`

### `market_watchlist`

Named watchlist entries and monitoring state.

- **Columns:** `id` TEXT PK, `ticker` TEXT, `name` TEXT, `category` TEXT, `target_price` REAL, `notes` TEXT, `added_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE market_watchlist (             id TEXT PRIMARY KEY,             ticker TEXT NOT NULL UNIQUE,             name TEXT DEFAULT '',             category TEXT DEFAULT 'watchlist',             target_price REAL DEFAULT 0,             notes TEXT DEFAULT '',             added_at TEXT         )`

### `message_feedback`

Thumbs-up/down feedback on messages.

- **Columns:** `feedback_id` TEXT PK, `message_id` TEXT, `user_id` TEXT, `conversation_id` TEXT, `rating` INTEGER, `feedback_text` TEXT, `category` TEXT, `created_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE message_feedback (             feedback_id TEXT PRIMARY KEY,             message_id TEXT NOT NULL,             user_id TEXT NOT NULL,             conversation_id TEXT,             rating INTEGER NOT NULL,  -- 1 = thumbs up, -1 = thumbs down             feedback_text TEXT,  -- Optional comment             category TEXT,  -- 'helpful', 'accurate', 'tone', 'length', 'other'             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                          FOREIGN KEY (message_id) ...`

### `messages`

Conversation messages.

- **Columns:** `id` TEXT PK, `conversation_id` TEXT, `role` TEXT, `content` TEXT, `agent_id` TEXT, `created_at` TEXT, `metadata` TEXT, `tokens_used` INTEGER, `model_used` TEXT, `has_citations` BOOLEAN, `citations` TEXT, `search_query` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE messages (             id TEXT PRIMARY KEY,             conversation_id TEXT,             role TEXT,             content TEXT,             agent_id TEXT DEFAULT '',             created_at TEXT, metadata TEXT DEFAULT '{}', tokens_used INTEGER DEFAULT 0, model_used TEXT DEFAULT '', has_citations BOOLEAN DEFAULT FALSE, citations TEXT, search_query TEXT,             FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE         )`

### `messages_fts`

FTS5 virtual table over message content.

- **Columns:** `content` TEXT.
- **SQLite definition excerpt:** `CREATE VIRTUAL TABLE messages_fts USING fts5(                 content,                 content=messages,                 content_rowid=rowid             )`

### `messages_fts_config`

FTS5 shadow config table.

- **Columns:** `k` TEXT PK, `v` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE 'messages_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID`

### `messages_fts_data`

FTS5 shadow data table.

- **Columns:** `id` INTEGER PK, `block` BLOB.
- **SQLite definition excerpt:** `CREATE TABLE 'messages_fts_data'(id INTEGER PRIMARY KEY, block BLOB)`

### `messages_fts_docsize`

FTS5 shadow docsize table.

- **Columns:** `id` INTEGER PK, `sz` BLOB.
- **SQLite definition excerpt:** `CREATE TABLE 'messages_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB)`

### `messages_fts_idx`

FTS5 shadow index table.

- **Columns:** `segid` TEXT PK, `term` TEXT PK, `pgno` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE 'messages_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID`

### `morning_briefs`

Cached/generated morning briefing history.

- **Columns:** `brief_id` TEXT PK, `user_id` TEXT, `brief_text` TEXT, `stats_json` TEXT, `created_at` TIMESTAMP, `viewed` BOOLEAN, `viewed_at` TIMESTAMP.
- **SQLite definition excerpt:** `CREATE TABLE morning_briefs (         brief_id   TEXT PRIMARY KEY,         user_id    TEXT NOT NULL,         brief_text TEXT NOT NULL,         stats_json TEXT,         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,         viewed     BOOLEAN DEFAULT 0,         viewed_at  TIMESTAMP     )`

### `notifications`

Dashboard/toast notifications.

- **Columns:** `id` INTEGER PK, `text` TEXT, `color` TEXT, `category` TEXT, `created_at` TEXT, `read` INTEGER.
- **SQLite definition excerpt:** `CREATE TABLE notifications (             id INTEGER PRIMARY KEY AUTOINCREMENT,             text TEXT,             color TEXT DEFAULT '#00B8FF',             category TEXT DEFAULT 'system',             created_at TEXT,             read INTEGER DEFAULT 0         )`

### `plan_node_events`

Per-node execution events for implementation plans.

- **Columns:** `id` TEXT PK, `plan_id` TEXT, `node_id` TEXT, `event_type` TEXT, `payload_json` TEXT, `timestamp` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE plan_node_events (                 id TEXT PRIMARY KEY,                 plan_id TEXT NOT NULL,                 node_id TEXT,                 event_type TEXT NOT NULL,                 payload_json TEXT,                 timestamp TEXT,                 FOREIGN KEY (plan_id) REFERENCES implementation_plans(plan_id)             )`

### `politician_trades`

Normalized Capitol Trades disclosures.

- **Columns:** `id` TEXT PK, `politician_id` TEXT, `politician_name` TEXT, `chamber` TEXT, `ticker` TEXT, `asset_name` TEXT, `trade_type` TEXT, `amount_range` TEXT, `amount_min` REAL, `amount_max` REAL, `amount_midpoint` REAL, `transaction_date` TEXT, `disclosure_date` TEXT, `raw_json` TEXT, `ingested_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE politician_trades (                 id TEXT PRIMARY KEY,                 politician_id TEXT,                 politician_name TEXT,                 chamber TEXT,                 ticker TEXT,                 asset_name TEXT DEFAULT '',                 trade_type TEXT,                 amount_range TEXT DEFAULT '',                 amount_min REAL DEFAULT 0,                 amount_max REAL DEFAULT 0,                 amount_midpoint REAL DEFAULT 0,                 transaction_date TEXT...`

### `projects`

Portfolio project records.

- **Columns:** `id` TEXT PK, `slug` TEXT, `name` TEXT, `description` TEXT, `status` TEXT, `lead_agent` TEXT, `tags` TEXT, `created_at` TEXT, `updated_at` TEXT, `client_id` TEXT, `sprint` TEXT, `milestone` TEXT, `url` TEXT, `platform` TEXT, `metadata` TEXT, `notes` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE projects (             id TEXT PRIMARY KEY,             slug TEXT UNIQUE,             name TEXT,             description TEXT DEFAULT '',             status TEXT DEFAULT 'active',             lead_agent TEXT DEFAULT '',             tags TEXT DEFAULT '[]',             created_at TEXT,             updated_at TEXT         , client_id TEXT DEFAULT '', sprint TEXT DEFAULT '', milestone TEXT DEFAULT '', url TEXT DEFAULT '', platform TEXT DEFAULT '', metadata TEXT DEFAULT '{}', notes TE...`

### `prompt_templates`

Reusable prompt snippets and metadata.

- **Columns:** `id` TEXT PK, `title` TEXT, `category` TEXT, `prompt_text` TEXT, `agent_id` TEXT, `project_slug` TEXT, `is_system` INTEGER, `usage_count` INTEGER, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE prompt_templates (                 id TEXT PRIMARY KEY,                 title TEXT NOT NULL,                 category TEXT DEFAULT 'general',                 prompt_text TEXT NOT NULL,                 agent_id TEXT DEFAULT 'inez',                 project_slug TEXT DEFAULT '',                 is_system INTEGER DEFAULT 0,                 usage_count INTEGER DEFAULT 0,                 created_at TEXT,                 updated_at TEXT             )`

### `reflexion_log`

Per-run reflexion scoring and critique history.

- **Columns:** `id` TEXT PK, `agent_id` TEXT, `run_id` TEXT, `task` TEXT, `output` TEXT, `score` REAL, `critique` TEXT, `skill_rewritten` INTEGER, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE reflexion_log (             id          TEXT PRIMARY KEY,             agent_id    TEXT NOT NULL,             run_id      TEXT,             task        TEXT,             output      TEXT,             score       REAL,             critique    TEXT,             skill_rewritten INTEGER DEFAULT 0,             created_at  TEXT         )`

### `reports`

Report definitions and outputs.

- **Columns:** `id` TEXT PK, `title` TEXT, `report_type` TEXT, `content` TEXT, `summary` TEXT, `project_slug` TEXT, `generated_by` TEXT, `job_id` TEXT, `status` TEXT, `generated_at` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE reports (             id TEXT PRIMARY KEY,             title TEXT NOT NULL,             report_type TEXT DEFAULT 'daily',             content TEXT DEFAULT '',             summary TEXT DEFAULT '',             project_slug TEXT DEFAULT '',             generated_by TEXT DEFAULT '',             job_id TEXT DEFAULT '',             status TEXT DEFAULT 'complete',             generated_at TEXT,             created_at TEXT,             updated_at TEXT         )`

### `run_events`

Replayable Inez/agent event stream.

- **Columns:** `id` INTEGER PK, `run_id` TEXT, `conversation_id` TEXT, `type` TEXT, `data` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE run_events (                 id              INTEGER PRIMARY KEY AUTOINCREMENT,                 run_id          TEXT NOT NULL,                 conversation_id TEXT,                 type            TEXT NOT NULL,                 data            TEXT,                 created_at      TEXT NOT NULL             )`

### `runs`

Completed run records and scores.

- **Columns:** `id` INTEGER PK, `run_id` TEXT, `agent_id` TEXT, `project` TEXT, `graph` TEXT, `task` TEXT, `score` REAL, `critique` TEXT, `revision_count` INTEGER, `output` TEXT, `skill_version` INTEGER, `status` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE runs (             id INTEGER PRIMARY KEY AUTOINCREMENT,             run_id TEXT UNIQUE,             agent_id TEXT,             project TEXT,             graph TEXT,             task TEXT,             score REAL DEFAULT 0.0,             critique TEXT DEFAULT '',             revision_count INTEGER DEFAULT 0,             output TEXT DEFAULT '',             skill_version INTEGER DEFAULT 1,             status TEXT DEFAULT 'running',             created_at TEXT         )`

### `scheduled_jobs`

User-defined scheduler jobs.

- **Columns:** `id` TEXT PK, `agent_id` TEXT, `project` TEXT, `graph` TEXT, `task` TEXT, `run_type` TEXT, `cron_expr` TEXT, `interval_sec` INTEGER, `scheduled_at` TEXT, `next_fire` TEXT, `status` TEXT, `created_at` TEXT, `job_data` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE scheduled_jobs (             id TEXT PRIMARY KEY,             agent_id TEXT,             project TEXT,             graph TEXT DEFAULT 'reflexion',             task TEXT,             run_type TEXT DEFAULT 'cron',             cron_expr TEXT,             interval_sec INTEGER,             scheduled_at TEXT,             next_fire TEXT,             status TEXT DEFAULT 'active',             created_at TEXT,             job_data TEXT DEFAULT '{}'         )`

### `skills`

Stored skill/version content.

- **Columns:** `id` INTEGER PK, `agent_id` TEXT, `skill_name` TEXT, `version` INTEGER, `content` TEXT, `avg_score` REAL, `last_critique` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE skills (             id INTEGER PRIMARY KEY AUTOINCREMENT,             agent_id TEXT,             skill_name TEXT,             version INTEGER DEFAULT 1,             content TEXT,             avg_score REAL DEFAULT 0.0,             last_critique TEXT DEFAULT '',             created_at TEXT,             UNIQUE(agent_id)         )`

### `sqlite_sequence`

SQLite internal AUTOINCREMENT bookkeeping table; not part of the application data contract.

- **Columns:** `name` TEXT, `seq` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE sqlite_sequence(name,seq)`

### `todos`

Task tracking shared across the product.

- **Columns:** `id` TEXT PK, `title` TEXT, `description` TEXT, `priority` TEXT, `status` TEXT, `project` TEXT, `due_date` TEXT, `tags` TEXT, `source` TEXT, `created_at` TEXT, `updated_at` TEXT, `assigned_agent` TEXT, `parent_id` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE todos (             id TEXT PRIMARY KEY,             title TEXT NOT NULL,             description TEXT DEFAULT '',             priority TEXT DEFAULT 'medium',             status TEXT DEFAULT 'pending',             project TEXT DEFAULT '',             due_date TEXT DEFAULT '',             tags TEXT DEFAULT '[]',             source TEXT DEFAULT 'user',             created_at TEXT,             updated_at TEXT         , assigned_agent TEXT DEFAULT '', parent_id TEXT DEFAULT '')`

### `tracked_politicians`

Tracked politicians and performance summary.

- **Columns:** `id` TEXT PK, `name` TEXT, `chamber` TEXT, `party` TEXT, `state` TEXT, `tracking_reason` TEXT, `performance_note` TEXT, `track_since` TEXT, `is_active` INTEGER, `total_signals` INTEGER, `approved_signals` INTEGER, `profitable_signals` INTEGER, `total_return_pct` REAL, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE tracked_politicians (                 id TEXT PRIMARY KEY,                 name TEXT NOT NULL,                 chamber TEXT DEFAULT 'both',                 party TEXT DEFAULT '',                 state TEXT DEFAULT '',                 tracking_reason TEXT NOT NULL DEFAULT '',                 performance_note TEXT DEFAULT '',                 track_since TEXT,                 is_active INTEGER DEFAULT 1,                 total_signals INTEGER DEFAULT 0,                 approved_signa...`

### `travel_trips`

Travel project trip records.

- **Columns:** `id` TEXT PK, `name` TEXT, `destination` TEXT, `depart_date` TEXT, `return_date` TEXT, `status` TEXT, `budget` REAL, `spent` REAL, `notes` TEXT, `created_at` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE travel_trips (             id TEXT PRIMARY KEY,             name TEXT,             destination TEXT,             depart_date TEXT,             return_date TEXT,             status TEXT DEFAULT 'planning',             budget REAL DEFAULT 0,             spent REAL DEFAULT 0,             notes TEXT DEFAULT '',             created_at TEXT,             updated_at TEXT         )`

### `uploaded_files`

Uploaded file metadata and parse status.

- **Columns:** `file_id` TEXT PK, `user_id` TEXT, `filename` TEXT, `file_type` TEXT, `mime_type` TEXT, `file_size` INTEGER, `storage_path` TEXT, `parsed_content` TEXT, `parsing_status` TEXT, `parsing_error` TEXT, `uploaded_at` TIMESTAMP, `uploaded_via` TEXT, `conversation_id` TEXT, `message_id` TEXT, `metadata_json` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE uploaded_files (             file_id TEXT PRIMARY KEY,             user_id TEXT NOT NULL,             filename TEXT NOT NULL,             file_type TEXT NOT NULL,  -- 'pdf', 'image', 'spreadsheet', 'document'             mime_type TEXT NOT NULL,             file_size INTEGER NOT NULL,             storage_path TEXT NOT NULL,             parsed_content TEXT,  -- Extracted text/analysis             parsing_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'complete', 'fail...`

### `user_preferences`

Durable explicit/inferred user preferences.

- **Columns:** `id` INTEGER PK, `user_id` INTEGER, `key` TEXT, `value` TEXT, `updated_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE user_preferences (             id INTEGER PRIMARY KEY AUTOINCREMENT,             user_id INTEGER,             key TEXT NOT NULL,             value TEXT,             updated_at TEXT,             UNIQUE(user_id, key)         )`

### `user_style_preferences`

Learned response-style preferences.

- **Columns:** `user_id` TEXT PK, `preferred_length` TEXT, `preferred_formality` TEXT, `use_emojis` BOOLEAN, `citation_density` TEXT, `code_style` TEXT, `avg_positive_response_tokens` INTEGER, `avg_negative_response_tokens` INTEGER, `total_positive_feedback` INTEGER, `total_negative_feedback` INTEGER, `total_corrections` INTEGER, `last_updated` TIMESTAMP, `preferences_json` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE user_style_preferences (             user_id TEXT PRIMARY KEY,             preferred_length TEXT DEFAULT 'medium',  -- 'concise', 'medium', 'detailed'             preferred_formality TEXT DEFAULT 'professional',  -- 'casual', 'professional', 'formal'             use_emojis BOOLEAN DEFAULT 1,             citation_density TEXT DEFAULT 'medium',  -- 'none', 'low', 'medium', 'high'             code_style TEXT DEFAULT 'explained',  -- 'minimal', 'explained', 'verbose'             avg_...`

### `users`

Authenticated users.

- **Columns:** `id` INTEGER PK, `username` TEXT, `email` TEXT, `hashed_password` TEXT, `role` TEXT, `is_active` INTEGER, `created_at` TEXT, `last_login` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE users (             id INTEGER PRIMARY KEY AUTOINCREMENT,             username TEXT UNIQUE NOT NULL,             email TEXT UNIQUE,             hashed_password TEXT NOT NULL,             role TEXT DEFAULT 'user',             is_active INTEGER DEFAULT 1,             created_at TEXT,             last_login TEXT         )`

### `worker_nodes`

Live worker registry with heartbeat/capacity.

- **Columns:** `id` TEXT PK, `hostname` TEXT, `role` TEXT, `capacity` INTEGER, `ollama_url` TEXT, `status` TEXT, `last_heartbeat` TEXT, `started_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE worker_nodes (             id TEXT PRIMARY KEY,             hostname TEXT NOT NULL,             role TEXT NOT NULL,             capacity INTEGER DEFAULT 1,             ollama_url TEXT DEFAULT '',             status TEXT DEFAULT 'active',             last_heartbeat TEXT,             started_at TEXT         )`

### `ws_events`

Durable websocket replay/fan-out log.

- **Columns:** `id` INTEGER PK, `payload_json` TEXT, `created_at` TEXT.
- **SQLite definition excerpt:** `CREATE TABLE ws_events (                 id INTEGER PRIMARY KEY AUTOINCREMENT,                 payload_json TEXT NOT NULL,                 created_at TEXT NOT NULL             )`
