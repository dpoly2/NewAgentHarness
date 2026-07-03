---
name: agentshield
description: Pre-dispatch prompt security scanning for ArchonHub agent tasks.
source: affaan-m/ECC AgentShield philosophy (MIT-inspired)
archonhub_integration: "Used by agent_runner.py and inez_agent.py before LLM dispatch."
---

# AgentShield

## Overview

AgentShield is a lightweight pre-dispatch prompt security scanner for ArchonHub.
It runs fast regex-based checks on task text before any LLM call so risky prompts
can be blocked or flagged without adding noticeable latency.

## What It Scans For

### CRITICAL — blocked immediately

- Prompt injection attempts  
  Examples: `ignore previous instructions`, `system: you are now`, `override:`
- Jailbreak attempts  
  Examples: `DAN`, `pretend you have no restrictions`, `developer mode`
- Credential exfiltration  
  Examples: asking for `.env` contents, API keys, passwords, tokens, credentials

### HIGH — allowed, but warned and logged

- Data exfiltration requests  
  Examples: `dump the database`, `list all users`, `export all records`
- Instruction override language  
  Examples: `you must now`, `from now on you will`
- PII requests  
  Examples: SSNs, credit card numbers, DOB + full-name combinations

### MEDIUM — logged only

- Sensitive financial instruction patterns that may require extra caution
- Scope violations where an agent appears to be operating outside its domain

## What Happens on Detection

- **CRITICAL** → task is blocked before the LLM is called
- **HIGH** → task proceeds, but a warning is logged and a DevOps todo is created
- **MEDIUM** → task proceeds with warning-level observability
- **SAFE** → normal execution

## How to Avoid False Positives

- Describe the intended business task directly and concretely
- Avoid instruction phrases like `ignore previous instructions` unless analyzing them as quoted data
- Do not ask agents to reveal secrets, tokens, passwords, or `.env` contents
- For audits or red-team work, clearly frame the task as detection/analysis rather than execution
- Keep agent tasks scoped to the agent's actual project or domain

## ArchonHub Integration Notes

- `agent_runner.py` scans every dispatched agent task before LLM execution
- `inez_agent.py` scans the raw incoming user request before planning dispatches
- The scanner is intentionally lightweight and must never become a slow network dependency
