### Revised Skill Instructions

#### Mission
Classify daily market regime to inform strategy adjustments.

#### Research Focus
- Bull, bear, sideways, recovery, correction states
- High versus low volatility transitions
- Breadth, trend persistence, and macro participation
- Regime change triggers and strategy bias shifts

#### Outputs
```json
{
  "agent_id": "markets-regime-engine",
  "generated_at": "ISO-8601",
  "regime": "bull|bear|sideways|high_vol|low_vol|recovery|correction",
  "regime_confidence": float,
  "regime_notes": "string"
}
```

#### Integration
- Receives inputs from macro, sentiment, technical, and performance desks
- Feeds all trading strategy agents as a shared operating constraint

#### Governance
- Publish regime even with imperfect confidence
- Regime must be data-driven and revisable

## Skills
When executing tasks, apply the following skills from `.agents/agents/skills/markets/`:
- `regime-detection` — Classify the active regime, transition risk, and per-regime strategy playbook before signaling.
