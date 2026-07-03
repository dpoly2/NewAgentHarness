---
name: obsidian-cli
description: Use Obsidian CLI to append notes, search vault content, and create or update notes from ArchonHub agents.
---

# Obsidian CLI

Obsidian CLI is the `obsidian-cli` npm package that controls a running Obsidian Desktop app through Obsidian's URI/CLI support. The upstream skill covers 130+ commands; for ArchonHub, this local skill focuses on the note append and vault search flows needed for agent memory.

## Requirements

- Obsidian Desktop **v1.12+**
- Obsidian CLI enabled in Obsidian settings
- Obsidian Desktop running
- CLI installed globally:

```bash
npm install -g obsidian-cli
```

## Key Commands for ArchonHub Agents

### Append to today's daily note

```bash
obsidian daily:append --text "Agent memory entry"
```

Use this to journal agent work summaries into the current daily note.

### Search the vault

```bash
obsidian search --query "markets-cro" --vault "My Vault"
```

Use this to find prior context, references, or related notes for an agent, task, or project.

### Create a note

```bash
obsidian note:create --title "Research Brief" --content "# Research Brief"
```

Use this to create new structured notes from agent output.

### Append to an existing note

```bash
obsidian note:append --title "Research Brief" --text "- Added new findings"
```

Use this to grow long-lived notes without replacing prior content.

## ArchonHub Integration

ArchonHub wires Obsidian CLI into `hub_nodes.py` as a **best-effort enhancement**:

- `node_save_memory` appends each completed agent run to today's daily note.
- `node_load_memory` can search the vault for the current `agent_id` and append the top search results into `memory_context`.

The daily-note format used by `node_save_memory` is:

```markdown
## [AGENT_ID] — [TIMESTAMP]
**Task:** [task truncated to 200 chars]
**Score:** [score as percentage]
**Summary:** [first 300 chars of output]
```

This gives ArchonHub agents lightweight journaling in Obsidian without replacing the existing SQLite/local memory path.

## Graceful Degradation

Obsidian integration must never break the agent pipeline.

- Check CLI availability with `shutil.which("obsidian")`
- Use short `subprocess.run(..., timeout=5)` calls
- Catch all exceptions
- Log at DEBUG only
- If Obsidian CLI is unavailable or fails, skip silently and continue normal ArchonHub execution

## Notes

- Windows may require the `Obsidian.com` CLI redirector beside `Obsidian.exe`
- Run from a normal user terminal; elevated/admin terminals can fail silently on Windows
- Search and append operations should be treated as optional context enrichment, not a required persistence layer
