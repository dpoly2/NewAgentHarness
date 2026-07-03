---
name: executing-plans
description: Use when you have a written implementation plan to execute with review checkpoints.
source: obra/superpowers (MIT License)
archonhub_integration: "Used by ArchonHub agents when a plan doc exists in the plan inbox (.agents/agentharness/memory/incoming_files/)."
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load and Review Plan
1. Read plan file from plan inbox or provided path
2. Review critically — identify any questions or concerns
3. If concerns: Raise them before starting
4. If no concerns: Create todos for the plan items and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as `in_progress`
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as `completed`
5. Emit `db_write` with progress update

### Step 3: Complete

After all tasks complete and verified:
- Report completion with summary of what was done
- List any follow-up todos created
- Save updated agent memory

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Stop when blocked, don't guess

## ArchonHub Integration

Plans land in `.agents/agentharness/memory/incoming_files/` via the plan autoloader.
The autoloader detects `.md` files with YAML frontmatter `type: plan` and dispatches this skill.
Progress is tracked in the `todos` table with `project` matching the plan's project slug.
