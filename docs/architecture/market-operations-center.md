# Market Operations Center

## Overview
The Tactical Alpha Market Intelligence Division V2 is the ArchonHub market-side operating system: 31 structured-output agents across 9 departments, plus a project-level coordination wrapper and existing Congress Edge integration.

## V2 Org Structure

| Layer | Component | Purpose |
| --- | --- | --- |
| Executive | `inez-chief-of-staff` | Executive oversight and David-facing escalation |
| Division Command | `markets-tactical-alpha` | Synthesis, prioritization, executive briefing |
| Portfolio Command | `markets-cio` / `markets-cro` | Allocation and risk approval |
| Operations Wrapper | `markets-project-lead` | Coordination shell and documentation anchor |

## Full Agent List

| agent_id | Department | Role |
| --- | --- | --- |
| `markets-tactical-alpha` | Division Command | Tactical Alpha Director |
| `markets-cio` | Portfolio Management | Portfolio Manager / CIO |
| `markets-cro` | Portfolio Management | Chief Risk Officer / Risk Manager |
| `markets-macro-analyst` | Market Intelligence | Macro Intelligence Agent |
| `markets-intelligence-desk` | Market Intelligence | Market Intelligence Desk |
| `markets-options-strategist` | Trading Strategy | Options Strategist |
| `markets-quant` | Quantitative Intelligence | Quantitative Intelligence Lead |
| `markets-technical-analyst` | Technical Analysis | Technical Analysis Lead |
| `markets-equity-analyst` | Market Intelligence | Equity Research Analyst |
| `markets-news-intelligence` | Market Intelligence | News Intelligence Agent |
| `markets-sentiment-intelligence` | Market Intelligence | Sentiment Intelligence Agent |
| `markets-whale-tracker` | Smart Money Intelligence | Whale & Dark Pool Intelligence |
| `markets-insider-tracker` | Smart Money Intelligence | Insider Transaction Intelligence |
| `markets-trend-engine` | Technical Analysis | Trend & Momentum Engine |
| `markets-smc-engine` | Technical Analysis | Smart Money Concepts Engine |
| `markets-market-structure` | Technical Analysis | Market Structure AI |
| `markets-trailing-trade-manager` | Trading Strategy | Trailing Trade Manager |
| `markets-ladder-buy-manager` | Trading Strategy | Ladder Buy Manager |
| `markets-options-wheel` | Trading Strategy | Options Wheel Division |
| `markets-swing-trading` | Trading Strategy | Swing Trading AI |
| `markets-dividend-strategy` | Trading Strategy | Dividend Strategy AI |
| `markets-regime-engine` | Quantitative Intelligence | Market Regime Engine |
| `markets-probability-engine` | Quantitative Intelligence | AI Probability Engine |
| `markets-backtesting-engine` | Quantitative Intelligence | Backtesting Engine |
| `markets-portfolio-optimizer` | Portfolio Management | Portfolio Optimizer |
| `markets-position-manager` | Portfolio Management | Position Manager |
| `markets-trading-education` | Marketing Division | Trading Education AI |
| `markets-content-studio` | Marketing Division | Content Studio |
| `markets-community-manager` | Marketing Division | Community Manager |
| `markets-performance-analytics` | Performance Analytics | Performance Analytics |
| `markets-automation-center` | Automation Center | Automation Center |

## Multi-Agent Pipeline

```text
Automation Center
    |
    v
Macro / News / Sentiment / Whale / Insider / Congress Edge
    |
    v
Intelligence Desk Fusion
    |
    +--> Technical Stack (Trend -> SMC -> Market Structure -> Technical Lead)
    |
    +--> Equity Research
    |
    v
Quant Stack (Regime -> Probability -> Backtesting -> Quant Lead)
    |
    v
Trading Strategy Stack (Options / Wheel / Swing / Dividend / Ladder / Trail)
    |
    v
CIO Thesis + CRO Approval
    |
    v
Portfolio Optimizer / Position Manager / Alpaca Execution Review
    |
    +--> Performance Analytics
    |
    +--> Education / Content / Community
    |
    v
Tactical Alpha Director -> Inez -> David
```

## Department Responsibilities

- **Market Intelligence:** macro posture, breaking news, sentiment, and fusion routing.
- **Smart Money Intelligence:** institutional and insider footprints plus Congress Edge contextual feeds.
- **Technical Analysis:** trend, SMC, market phase, and timing/invalidation levels.
- **Trading Strategy:** options structures, wheel, swing, dividend, trailing, and ladder plans.
- **Quantitative Intelligence:** regime classification, probability scoring, and backtesting evidence.
- **Portfolio Management:** allocation, risk, rebalancing, and live position oversight.
- **Marketing Division:** education, compliant content packaging, and community reporting.
- **Performance Analytics:** discipline, expectancy, drawdown, and outcome accountability.
- **Automation Center:** recurring cadence orchestration and escalation of stale/missed workflows.

## Agent Communication Protocol
Each agent should emit structured JSON matching either its skill-file output format or one of the shared contracts in `docs/contracts/`. Cross-agent handoffs should preserve:
1. exact `agent_id`
2. `generated_at` timestamp
3. facts versus analysis separation
4. uncertainty or dissent fields when material
5. any risk or approval state already known

## Automation Schedule

| Cadence | Tasks |
| --- | --- |
| Every Morning | Overnight macro summary, global futures scan, economic calendar, breaking news, whale flow, options flow, sector strength, watchlist generation, executive briefing draft |
| Every Hour | Position review, trailing stop updates, news refresh, volatility shift check, institutional flow refresh, pending-signal queue check |
| End of Day | Journal update, strategy review, performance metrics, risk assessment, next-day planning |
| Weekly | Portfolio review, strategy optimization, marketing plan, AI evaluation, top/bottom contributor review |
| Monthly | Backtest refresh, strategy tuning, rebalance recommendations, curriculum/content refresh, discipline trend review |

## Execution Integration
- **Alpaca:** execution review sits after signal fusion, quant validation, strategy packaging, and CRO approval. Alpaca should be treated as the execution endpoint, not the source of research truth.
- **Capitol Trades / Congress Edge:** existing Congress Edge workflows remain part of Smart Money Intelligence. Congressional disclosures must stay contextual, disclosed as lagged, and never be framed as predictive on their own.

## V3 Roadmap
- AI Vision System
- Voice Market Assistant
- Autonomous Research Lab
- AI Simulation Engine
- Personal Trade Coach
- Multi-Agent Collaboration pipeline improvements
