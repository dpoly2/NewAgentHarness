---
name: regime-detection
description: Identify the active market regime, transition risk, and preferred playbook before ArchonHub agents issue market recommendations.
domain: markets
source: ArchonHub custom informed by Tactical Alpha Division V2 and ECC market-signal practices
---

# Regime Detection

Use this skill to classify the operating environment before weighting any technical, macro, or flow signal. Most false positives in trading come from using the right signal in the wrong regime. A breakout model behaves differently in a steady bull trend than in a choppy mean-reversion tape; smart-money flow also carries different meaning when volatility is expanding versus compressing.

## Four-Regime Model

Classify the market into one of four primary states:

1. **Trending Bull** — rising price structure, supportive breadth, orderly pullbacks, benign volatility, and constructive macro backdrop.
2. **Trending Bear** — lower highs/lows, failed rallies, defensive leadership, tightening liquidity, and risk-off macro behavior.
3. **Mean-Reverting** — range-bound action, repeated failures at extremes, mixed breadth, compressed realized trend, and two-way positioning.
4. **High-Volatility** — unstable price discovery, sharp intraday swings, frequent gap risk, wide breadth dispersion, and fast narrative rotation.

## Inputs

Evaluate the regime using a blend of market internals and macro overlay:

- VIX spot level and VIX term structure (contango vs backwardation)
- put/call ratio and whether the move is driven by hedging panic or complacency
- breadth: advance/decline line, up/down volume, new highs/lows, McClellan oscillator
- trend persistence: moving-average slope, ADX, and follow-through quality
- realized volatility versus implied volatility
- sector leadership and participation quality
- Fed policy regime: hiking, cutting, or paused
- macro stress markers: yields, credit spreads, dollar strength, and commodity shocks

## Transition Detection

Do not only label the current state. Detect **transition risk**.

### Early Signals
- VIX term structure flattening before price weakness
- breadth divergence against index highs
- repeated failed breakouts or failed breakdowns
- defensive sectors outperforming while indices remain near highs
- policy repricing in FedWatch or rates futures

### Confirmation Rules
Require at least two confirmations before formally changing regime:
- price structure break on the daily timeframe
- breadth deterioration or thrust confirmation
- volatility regime shift lasting more than one session
- macro catalyst that plausibly changes discount-rate or growth expectations

## Per-Regime Playbook

- **Trending Bull:** momentum continuation, buy-the-dip, bullish debit spreads, high-beta leaders, trend pullbacks.
- **Trending Bear:** rallies into resistance, bearish debit spreads, defensive rotation, reduced gross exposure.
- **Mean-Reverting:** fades at extremes, tighter targets, smaller size, quicker exits, premium-selling only if separate risk mandate allows.
- **High-Volatility:** wait for confirmation, reduce size, widen expected ranges, prefer hedged or defined-risk structures.

## Output Contract

Return JSON:

```json
{
  "skill": "regime-detection",
  "regime": "trending_bull|trending_bear|mean_reverting|high_volatility",
  "confidence_pct": 0,
  "fed_overlay": "hiking|cutting|paused",
  "vix_term_structure": "contango|flat|backwardation",
  "breadth_state": "strong|mixed|weak",
  "transition_risk": "low|medium|high",
  "early_signals": ["string"],
  "confirmation_rules_met": ["string"],
  "preferred_playbook": ["string"],
  "notes": "string"
}
```

## Guardrails

- Regime calls must be evidence-led, not narrative-led.
- If evidence is mixed, publish the uncertainty instead of forcing certainty.
- A regime label is only useful if it changes signal weighting or execution behavior.
