---
name: brainstorming
description: "Use before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
source: obra/superpowers (MIT License)
archonhub_integration: "Inez invokes this skill for complex multi-step requests before dispatching implementation agents."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST complete these steps in order:

1. **Explore project context** — check files, docs, recent state
2. **Ask clarifying questions** — one at a time; understand purpose, constraints, success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Write design doc** — save to `.agents/agents/projects/<project>/specs/YYYY-MM-DD-<topic>-design.md` and commit
6. **Spec self-review** — quick inline check for placeholders, contradictions, ambiguity, scope
7. **User reviews written spec** — ask user to review the spec file before proceeding
8. **Transition to implementation** — invoke executing-plans skill to create implementation plan

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design, get approval before moving on
- **Be flexible** - Go back and clarify when something doesn't make sense

## Process Flow

```
Explore context → Ask questions (one at a time) → Propose 2-3 approaches
→ Present design (section by section) → User approves?
  No → Revise
  Yes → Write spec doc → Self-review → User reviews spec
    Changes → Revise
    Approved → Invoke executing-plans
```

## ArchonHub-Specific Usage

When Inez receives a complex multi-step request:
1. Inez flags it as `requires_spec: true` in the dispatch JSON
2. The brainstorming agent (`archon-brainstormer`) is dispatched first
3. All implementation agents are HELD until `spec_approved: true` is set
4. On approval, spec is saved to the plan inbox for autoloading
