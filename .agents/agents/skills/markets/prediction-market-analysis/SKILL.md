---
name: prediction-market-analysis
description: Compare prediction-market probabilities with listed-market pricing to find macro and sector divergences for ArchonHub trade baskets.
domain: markets
source: affaan-m/ECC (prediction-market-oracle-research, ito-basket-compare, prediction-market-risk-review) adapted for ArchonHub
---

# Prediction Market Analysis

Use this skill when ArchonHub needs to treat prediction markets as a macro-sentiment sensor rather than a source of truth. ECC's original skills frame prediction markets as informational inputs; this adaptation extends that idea into a comparative market workflow for Tactical Alpha. The objective is to compare **event probabilities** from venues like Polymarket, Kalshi, and PredictIt against **listed-market pricing** such as options-implied moves, rate-path expectations, sector ETF behavior, and single-name skew.

## What This Skill Solves

Prediction markets are often early at surfacing consensus around elections, Fed outcomes, policy timing, macro stress, or sector catalysts. Options markets are often better at encoding hedging demand, convexity, and distribution tails. When the two disagree, there may be an exploitable informational edge or a warning that one venue is thin, stale, or distorted.

## Research Workflow

1. Define the macro question clearly: election odds, Fed cut timing, tariff odds, recession probability, approval of a policy, commodity supply disruption, or company-specific binary event.
2. Collect market-implied probabilities from at least one prediction venue and time-stamp them.
3. Collect comparison pricing from listed markets:
   - options implied move or skew
   - sector ETF relative strength
   - futures term structure when relevant
   - rates, credit, FX, or volatility derivatives for macro questions
4. Identify whether the venue prices are directionally aligned, magnitude-aligned, or divergent.
5. Stress-test the prediction-market signal for liquidity, spread, market age, resolution ambiguity, and crowding.
6. Translate the divergence into a ranked basket of possible expressions rather than a single forced trade.

## Basket Comparison Framework

For each thesis, compare three layers:

- **Sector basket:** SPY, QQQ, IWM, XLF, XLE, XLV, SMH, KRE, TLT, or other relevant ETFs.
- **Single names:** market leaders, laggards, or event-exposed stocks tied to the thesis.
- **Macro derivatives:** rates, vol, commodities, currencies, or index options when they better express the event.

Ask four questions:
1. Where is the cleanest expression?
2. Where is the market already crowded?
3. Which vehicle offers the best asymmetry after volatility cost?
4. Which basket diversifies event-specific noise?

## Divergence Rules

- If prediction probability is materially above options-implied probability, treat it as a **consensus lead** that needs confirmation from breadth, volume, or macro data.
- If prediction probability is materially below options-implied probability, treat listed markets as pricing hidden tail risk or hedging demand.
- If venues agree but underlying baskets do not, investigate whether the issue is sector dispersion, single-name concentration, or liquidity distortions.
- If prediction-market liquidity is thin, downgrade the signal even if it looks compelling.

## Ranking Logic

Rank each basket using a **Sharpe-adjusted expected value lens**:

- expected directional payoff
- probability-weighted outcome map
- volatility or premium cost
- liquidity quality
- diversification benefit
- catalyst timing clarity

Higher rank requires both favorable expected value and cleaner implementation characteristics.

## Output Contract

Return JSON:

```json
{
  "skill": "prediction-market-analysis",
  "event": "Fed September cut",
  "prediction_markets": [
    {"venue": "Kalshi", "probability_pct": 62, "timestamp": "ISO-8601"}
  ],
  "options_implied_probability_pct": 48,
  "divergence_pct": 14,
  "signal_quality": "strong|mixed|weak",
  "basket_rankings": [
    {
      "instrument": "TLT",
      "type": "etf|single_name|macro_derivative",
      "expected_value": 0.42,
      "sharpe_adjusted_ev": 0.31,
      "thesis_role": "primary|secondary|hedge"
    }
  ],
  "key_caveats": ["string"],
  "summary": "string"
}
```

## Guardrails

- Prediction markets are evidence, not authority.
- Call out venue rules, liquidity issues, and stale pricing.
- Do not hide disagreement between venues or between prediction and listed markets.
- If the divergence cannot be mapped cleanly into a basket, say the edge is observational only.
