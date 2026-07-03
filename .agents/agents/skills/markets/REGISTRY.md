---
type: skills-registry
domain: markets
agent_count: 31
updated: 2026-07-03
source: affaan-m/ECC (adapted) + ArchonHub custom
---
# Market Intelligence Skills Registry

## Available Skills

| Skill | File | Assigned Agents |
|-------|------|-----------------|
| Itô Market Intelligence | ito-market-intelligence/SKILL.md | tactical-alpha, options-strategist, quant |
| Prediction Market Analysis | prediction-market-analysis/SKILL.md | probability-engine, macro-analyst, cro |
| Trade Planner | trade-planner/SKILL.md | tactical-alpha, options-strategist, cro |
| Regime Detection | regime-detection/SKILL.md | regime-engine, quant, technical-analyst |
| Signal Synthesis | signal-synthesis/SKILL.md | tactical-alpha, sentiment-intelligence, macro-analyst |

## Usage

In any market agent task, prepend the relevant skill from the registry:
"Using skill: ito-market-intelligence — [task description]"

This signals the LLM to apply the structured framework from the skill file.
