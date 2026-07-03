---
name: ito-market-intelligence
description: Regime-aware market-intelligence framework for ArchonHub agents that converts multi-source market data into actionable thesis JSON.
domain: markets
source: affaan-m/ECC (ito-market-intelligence, ito-basket-compare, ito-prediction-market-skill-pack) adapted for ArchonHub
---

# Itô Market Intelligence

Use this skill when a market agent needs to turn scattered market evidence into a disciplined trade thesis instead of a loose narrative. It adapts ECC's Itô prediction-market research style into ArchonHub's Tactical Alpha workflow, where the goal is to combine price action, smart-money activity, policy lag, and event probabilities into a thesis object that downstream agents can stress test, size, or reject.

## Core Objective

Model the market as a drift-diffusion process: expected direction comes from **drift** (macro trend, earnings direction, policy posture, factor leadership), while near-term path risk comes from **diffusion** (realized volatility, implied volatility, event risk, liquidity shocks, and gamma pressure). Do not confuse a strong directional story with a smooth path. Every thesis must state both the expected move and the path risk that could invalidate timing.

## Inputs To Gather

1. **Micro timeframe structure (1m/5m/15m):** opening drive, VWAP behavior, liquidity sweeps, relative volume, momentum failures, and whether buyers/sellers are defending key levels.
2. **Macro timeframe structure (daily/weekly):** trend quality, higher-timeframe support and resistance, gap context, weekly range position, and sector leadership.
3. **Regime context:** trending bull, trending bear, mean-reverting, or high-volatility. Use the regime as a weighting layer, not a label.
4. **Smart money flow:** dark-pool prints, block trades, unusual options flow, insider activity, and broad ETF rotation.
5. **Congress/insider lag:** treat Capitol Trades and similar disclosures as delayed information. Use them to identify persistent theme alignment, not immediate triggers.
6. **Catalyst map:** earnings, CPI, payrolls, FOMC, Treasury auctions, product launches, regulatory headlines, and geopolitical shocks.

## Regime-Aware Weighting Rules

- **Trending bull:** overweight higher highs, breadth thrusts, call flow, and pullback entries near support.
- **Trending bear:** overweight failed bounces, put flow, weak breadth, and rejection at resistance.
- **Mean-reverting:** overweight stretch indicators, faded extremes, and liquidity reversion to VWAP/value.
- **High-volatility:** reduce confidence unless multiple independent signals align; widen risk assumptions and shorten holding windows.

When signals conflict, explicitly state which ones are structural and which are transient. Example: bullish weekly trend plus bearish intraday gamma pin equals "higher-timeframe long bias, poor immediate timing."

## Itô Synthesis Workflow

1. Define the instrument, horizon, catalyst window, and venue context.
2. Estimate drift drivers: macro impulse, earnings trajectory, factor tailwinds, and breadth confirmation.
3. Estimate diffusion drivers: realized volatility, IV expansion/compression, event calendar density, gap risk, and liquidity conditions.
4. Check whether smart-money evidence confirms or contradicts the base thesis.
5. Compare micro structure versus macro structure; if they disagree, downgrade conviction and state the preferred timeframe.
6. Run a disclosure-lag check: ask whether Congress/insider activity supports the same theme over a multi-session horizon.
7. Produce a thesis only if at least three distinct evidence clusters align.

## Output Contract

Return JSON that downstream agents can use directly:

```json
{
  "agent_id": "markets-tactical-alpha",
  "skill": "ito-market-intelligence",
  "ticker": "NVDA",
  "timeframe": "swing|day|position",
  "regime": "trending_bull|trending_bear|mean_reverting|high_volatility",
  "drift_view": "string",
  "diffusion_view": "string",
  "signal_summary": {
    "technical": "bullish|neutral|bearish",
    "macro": "bullish|neutral|bearish",
    "smart_money": "bullish|neutral|bearish",
    "disclosure_lag": "supportive|mixed|unsupportive"
  },
  "entry_zone": {"low": 0, "high": 0},
  "exit_plan": {"target_1": 0, "target_2": 0, "invalidation": 0},
  "risk_notes": ["string"],
  "conviction": 1,
  "confidence_pct": 0,
  "thesis": "string"
}
```

## Guardrails

- Separate observable facts, market-implied signals, and interpretation.
- Congressional disclosures, dark-pool prints, and options flow are contextual evidence, never standalone authority.
- If liquidity is poor, volatility is event-driven, or regime evidence is mixed, say so clearly and lower conviction.
- Always provide invalidation criteria; no thesis is complete without a reason it could be wrong.
