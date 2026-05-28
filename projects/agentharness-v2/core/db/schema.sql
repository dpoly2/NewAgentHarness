-- AgentHarness v2 Database Schema
-- SQLite via better-sqlite3

CREATE TABLE IF NOT EXISTS conversations (
  id          TEXT PRIMARY KEY,
  slug        TEXT DEFAULT 'global',     -- project scope or 'global'
  title       TEXT,
  created_at  TEXT DEFAULT (datetime('now')),
  updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id              TEXT PRIMARY KEY,
  conversation_id TEXT REFERENCES conversations(id),
  role            TEXT NOT NULL,         -- 'user' | 'assistant' | 'agent' | 'system'
  content         TEXT NOT NULL,
  agent_id        TEXT,
  model           TEXT,
  tokens          INTEGER DEFAULT 0,
  created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id           TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT,
  agent_id     TEXT NOT NULL,
  project_slug TEXT DEFAULT 'global',
  status       TEXT DEFAULT 'queued',    -- queued|running|completed|failed|cancelled
  result       TEXT,
  tokens       INTEGER DEFAULT 0,
  duration_ms  INTEGER DEFAULT 0,
  spawned_by   TEXT,                     -- message id that created this
  created_at   TEXT DEFAULT (datetime('now')),
  updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS todos (
  id           TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT,
  priority     TEXT DEFAULT 'medium',    -- low|medium|high|urgent
  status       TEXT DEFAULT 'pending',   -- pending|in_progress|done|cancelled
  project_slug TEXT DEFAULT 'global',
  due_date     TEXT,
  source       TEXT,                     -- 'agent'|'user'|'automation'
  source_agent TEXT,
  tags         TEXT DEFAULT '[]',        -- JSON array
  created_at   TEXT DEFAULT (datetime('now')),
  updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_memory (
  id         TEXT PRIMARY KEY,
  agent_id   TEXT NOT NULL,
  key        TEXT NOT NULL,
  value      TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(agent_id, key)
);

CREATE TABLE IF NOT EXISTS projects (
  slug         TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  status       TEXT DEFAULT 'active',
  status_label TEXT,
  lead_agent   TEXT,
  last_synced  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
  id           TEXT PRIMARY KEY,
  type         TEXT,                     -- 'alert'|'task'|'todo'|'briefing'|'info'
  message      TEXT NOT NULL,
  project_slug TEXT,
  priority     TEXT DEFAULT 'medium',
  read         INTEGER DEFAULT 0,
  created_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_briefs (
  id             TEXT PRIMARY KEY,
  content        TEXT NOT NULL,
  generated_at   TEXT DEFAULT (datetime('now')),
  acknowledged   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS automations (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  schedule    TEXT,
  enabled     INTEGER DEFAULT 1,
  last_run    TEXT,
  next_run    TEXT,
  type        TEXT,
  config      TEXT DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON agent_tasks(project_slug);
CREATE INDEX IF NOT EXISTS idx_todos_project ON todos(project_slug);
CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_notifs_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_memory_agent ON agent_memory(agent_id);
