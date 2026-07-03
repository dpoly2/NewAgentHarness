---
name: trade-planner
description: Convert a validated market thesis into a scenario-based execution plan with sizing, options structure, and CRO-ready JSON.
domain: markets
source: affaan-m/ECC (ito-trade-planner, prediction-market-risk-review) adapted for ArchonHub
---

# Trade Planner

Use this skill after a thesis has already been formed and at least one independent desk has validated the setup. ECC's trade-planner skill is intentionally non-advisory; ArchonHub's version keeps the same disciplined worksheet mindset but upgrades it into a formal pre-execution planning package for Tactical Alpha. The purpose is not to force action. The purpose is to convert a thesis into a complete risk-defined plan that the CRO can approve, reduce, or reject.

## Planning Objective

Every trade plan must answer five questions before capital is considered:
1. **Why this setup?**
2. **Why this instrument?**
3. **Why now?**
4. **How much can be lost if wrong?**
5. **What changes the thesis?**

If any answer is weak, incomplete, or hand-wavy, the plan is not ready.

## Workflow

1. Restate the thesis in neutral terms with ticker, timeframe, catalyst, and regime.
2. Select the instrument: shares, calls, puts, spreads, collars, calendars, or defined-risk combinations.
3. Build the entry logic: breakout, pullback, reclaim, mean-reversion, event reaction, or staggered scale-in.
4. Define invalidation and stop placement based on structure, not emotion.
5. Set targets across base, bull, and bear scenarios.
6. Size the position using **fractional Kelly** as a ceiling, then reduce further for correlation, drawdown state, and event risk.
7. Run the pre-trade checklist.
8. Package the result into structured JSON for CRO review.

## Position Sizing Rules

Start from expected edge and payoff asymmetry, but never use full Kelly. Apply:

- **Fractional Kelly default:** 0.25x to 0.50x Kelly
- **Drawdown constraint:** automatically cut size if portfolio drawdown is elevated
- **Correlation haircut:** reduce size for names/themes already represented in the book
- **Volatility haircut:** reduce size when IV or realized vol is abnormally elevated
- **Binary event haircut:** shrink size materially near earnings, Fed, CPI, or legal/regulatory events

## Options Construction Rules

For directional conviction with event risk, prefer structures with known max loss:

- call debit spreads for bullish defined-risk expression
- put debit spreads for bearish defined-risk expression
- calendars when event timing and IV term structure matter
- collars or diagonals when hedging an existing core position
- avoid naked short premium unless a separate mandate explicitly allows it

## Pre-Trade Checklist

Confirm all of the following:
- average daily volume and options open interest are sufficient
- bid-ask spread is acceptable for the intended size
- IV rank/percentile fits the structure chosen
- earnings or major macro event proximity is explicit
- stop and target are placed before execution
- thesis dependency on a single data point is not excessive
- at least one dissenting scenario has been documented

## Scenario Matrix

Model three cases:
- **Base:** expected path with normal volatility
- **Bull:** favorable catalyst plus trend acceleration
- **Bear:** thesis failure, liquidity vacuum, or macro shock

For each case specify probability, expected price path, P/L expectation, and action trigger.

## Output Contract

Return JSON:

```json
{
  "skill": "trade-planner",
  "ticker": "AAPL",
  "regime": "trending_bull",
  "instrument": "call_debit_spread",
  "entry": {"trigger": "breakout above 0", "entry_zone": {"low": 0, "high": 0}},
  "size": {"kelly_fraction": 0.18, "applied_fraction": 0.06, "max_portfolio_risk_pct": 1.0},
  "risk": {"stop_loss": 0, "max_loss": 0, "drawdown_constraint": "string"},
  "targets": {"base": 0, "bull": 0, "bear": 0},
  "options_structure": {"legs": ["string"], "expiry": "YYYY-MM-DD", "iv_rank": 0},
  "pre_trade_checklist": {"liquidity": true, "spread_ok": true, "event_checked": true, "dissent_logged": true},
  "cro_notes": ["string"]
}
```

## Guardrails

- No undefined-risk structures for this division.
- No plan without invalidation.
- No sizing recommendation without correlation and drawdown context.
- If liquidity or event risk is poor, downgrade the plan to watch-only rather than forcing a trade.
