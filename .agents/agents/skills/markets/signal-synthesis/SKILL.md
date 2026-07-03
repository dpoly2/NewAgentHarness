---
name: signal-synthesis
description: Combine technical, macro, sentiment, and smart-money evidence into a conviction scorecard with contradiction handling for ArchonHub market agents.
domain: markets
source: ArchonHub custom informed by affaan-m/ECC market-research and Itô signal frameworks
---

# Signal Synthesis

Use this skill whenever multiple desks have produced partial answers and an agent must decide whether the evidence is strong enough to escalate. Tactical Alpha works only if signals are fused deliberately; otherwise the system becomes a noisy pile of isolated observations. This skill creates a common scoring language across technical, macro, sentiment, fundamental, and smart-money inputs.

## Signal Families

Score five evidence families:

1. **Technical** — trend, market structure, momentum, volume, support/resistance, relative strength.
2. **Fundamental / Macro** — earnings quality, valuation context, economic data, rates, liquidity, policy, sector tailwinds/headwinds.
3. **Sentiment** — news tone, social velocity, fear/greed, put/call extremes, crowding risk.
4. **Smart Money** — options flow, dark-pool prints, insider transactions, Congress disclosures, ETF rotation.
5. **Catalyst / Timing** — earnings, macro releases, product events, legal decisions, rebalance windows, seasonal flows.

## Weighting Rules

Weight signals by regime:

- trending environments favor technical continuation and smart-money confirmation
- mean-reverting environments favor sentiment extremes and stretched technicals
- high-volatility environments require stronger catalyst and risk-control evidence
- macro-sensitive tapes raise the weight on rates, dollar, and policy signals

Each family receives:
- direction: bullish, neutral, bearish
- strength score: 0-100
- reliability modifier: high, medium, low

## Consensus Rule

A signal package is eligible for CRO dispatch only if **three or more independent evidence families confirm the same directional thesis**. "Independent" means they are not all downstream reflections of the same event. Example: price breakout, call flow, and bullish social chatter may all stem from a single earnings rumor; that counts as weaker independence than breakout + breadth thrust + policy tailwind.

## Contradiction Handling

Do not smooth over contradictions. If macro is bearish but technicals are bullish, report:

- what conflicts
- which timeframe each signal belongs to
- which signal is leading vs lagging
- what evidence would resolve the contradiction

Common contradiction patterns:
- bullish price, weak breadth
- positive sentiment, bearish options skew
- strong fundamentals, poor timing
- smart-money buying into a macro headwind

When contradictions persist, lower conviction and move the recommendation to watch-only or smaller-size language.

## Scoring Workflow

1. Normalize each desk output into a common direction and strength scale.
2. Apply regime multipliers.
3. Count confirming families and dissenting families.
4. Identify whether the disagreement is timeframe-based, data-quality-based, or thesis-based.
5. Assign conviction from 1 to 5 and confidence from 0 to 100.
6. Recommend one of three states: escalate, monitor, or reject.

## Output Contract

Return JSON:

```json
{
  "skill": "signal-synthesis",
  "ticker": "MSFT",
  "regime": "trending_bull",
  "signal_scorecard": {
    "technical": {"direction": "bullish", "strength": 78, "reliability": "high"},
    "macro": {"direction": "neutral", "strength": 55, "reliability": "medium"},
    "sentiment": {"direction": "bullish", "strength": 64, "reliability": "medium"},
    "smart_money": {"direction": "bullish", "strength": 71, "reliability": "high"},
    "catalyst": {"direction": "bullish", "strength": 67, "reliability": "medium"}
  },
  "confirming_signals": 4,
  "dissenting_signals": 1,
  "conviction_level": 4,
  "confidence_pct": 76,
  "state": "escalate|monitor|reject",
  "contradictions": ["string"],
  "summary": "string"
}
```

## Guardrails

- At least three confirming signals are required for formal dispatch.
- Weak data quality downgrades confidence even when direction agrees.
- Always distinguish between a conflict in direction and a conflict in timeframe.
- The goal is clarity, not forced consensus.
