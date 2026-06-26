# Tactical Alpha Market Intelligence Division V2

**Created:** 2026-06-25
**Project:** markets
**Operating Model:** 31 operating agents across 9 departments, coordinated by `markets-project-lead` and led by `markets-tactical-alpha`.

## V2 Org Chart

| Layer | Role | Agent / System | Notes |
| --- | --- | --- | --- |
| Executive Oversight | Chief of Staff | `inez-chief-of-staff` | Receives daily executive briefing and escalations |
| Division Command | Market Director AI | `markets-tactical-alpha` | Runs Tactical Alpha Division V2 |
| Portfolio Command | CIO | `markets-cio` | Strategy, allocation, benchmark accountability |
| Risk Command | CRO | `markets-cro` | VaR, correlation, drawdown, approval gate |
| Program Coordination | Project Lead | `markets-project-lead` | Wrapper/orchestration file, not counted in 31 |

## Agent ID Registry (31 operating agents)

| agent_id | Department | Role | Primary Output |
| --- | --- | --- | --- |
| `markets-tactical-alpha` | Division Command | Tactical Alpha Director | `executive_briefing` |
| `markets-cio` | Portfolio Management | Portfolio Manager / CIO | `cio_directive` |
| `markets-cro` | Portfolio Management | Chief Risk Officer / Risk Manager | `risk_ruling` |
| `markets-macro-analyst` | Market Intelligence | Macro Intelligence Agent | `macro_brief` |
| `markets-intelligence-desk` | Market Intelligence | Market Intelligence Desk | `intelligence_fusion` |
| `markets-options-strategist` | Trading Strategy | Options Strategist | `options_strategy_plan` |
| `markets-quant` | Quantitative Intelligence | Quantitative Intelligence Lead | `quant_summary` |
| `markets-technical-analyst` | Technical Analysis | Technical Analysis Lead | `technical_synthesis` |
| `markets-equity-analyst` | Market Intelligence | Equity Research Analyst | `equity_research_packet` |
| `markets-news-intelligence` | Market Intelligence | News Intelligence Agent | `news_catalyst` |
| `markets-sentiment-intelligence` | Market Intelligence | Sentiment Intelligence Agent | `sentiment_snapshot` |
| `markets-whale-tracker` | Smart Money Intelligence | Whale & Dark Pool Intelligence | `whale_flow_report` |
| `markets-insider-tracker` | Smart Money Intelligence | Insider Transaction Intelligence | `insider_report` |
| `markets-trend-engine` | Technical Analysis | Trend & Momentum Engine | `trend_report` |
| `markets-smc-engine` | Technical Analysis | Smart Money Concepts Engine | `smc_report` |
| `markets-market-structure` | Technical Analysis | Market Structure AI | `market_structure_report` |
| `markets-trailing-trade-manager` | Trading Strategy | Trailing Trade Manager | `trailing_plan` |
| `markets-ladder-buy-manager` | Trading Strategy | Ladder Buy Manager | `ladder_buy_plan` |
| `markets-options-wheel` | Trading Strategy | Options Wheel Division | `wheel_recommendation` |
| `markets-swing-trading` | Trading Strategy | Swing Trading AI | `swing_setups` |
| `markets-dividend-strategy` | Trading Strategy | Dividend Strategy AI | `dividend_analysis` |
| `markets-regime-engine` | Quantitative Intelligence | Market Regime Engine | `regime_report` |
| `markets-probability-engine` | Quantitative Intelligence | AI Probability Engine | `probability_report` |
| `markets-backtesting-engine` | Quantitative Intelligence | Backtesting Engine | `backtest_report` |
| `markets-portfolio-optimizer` | Portfolio Management | Portfolio Optimizer | `allocation_recommendation` |
| `markets-position-manager` | Portfolio Management | Position Manager | `position_summary` |
| `markets-trading-education` | Marketing Division | Trading Education AI | `educational_content` |
| `markets-content-studio` | Marketing Division | Content Studio | `content_pieces` |
| `markets-community-manager` | Marketing Division | Community Manager | `community_reports` |
| `markets-performance-analytics` | Performance Analytics | Performance Analytics | `performance_report` |
| `markets-automation-center` | Automation Center | Automation Center | `automation_runbook` |

## Department Breakdown

| Department | Agent IDs |
| --- | --- |
| Market Intelligence | `markets-macro-analyst`, `markets-intelligence-desk`, `markets-equity-analyst`, `markets-news-intelligence`, `markets-sentiment-intelligence` |
| Smart Money Intelligence | `markets-whale-tracker`, `markets-insider-tracker` |
| Technical Analysis | `markets-technical-analyst`, `markets-trend-engine`, `markets-smc-engine`, `markets-market-structure` |
| Trading Strategy | `markets-options-strategist`, `markets-trailing-trade-manager`, `markets-ladder-buy-manager`, `markets-options-wheel`, `markets-swing-trading`, `markets-dividend-strategy` |
| Quantitative Intelligence | `markets-quant`, `markets-regime-engine`, `markets-probability-engine`, `markets-backtesting-engine` |
| Portfolio Management | `markets-cio`, `markets-cro`, `markets-portfolio-optimizer`, `markets-position-manager` |
| Marketing Division | `markets-trading-education`, `markets-content-studio`, `markets-community-manager` |
| Performance Analytics | `markets-performance-analytics` |
| Automation Center | `markets-automation-center` |

**Division leadership note:** `markets-tactical-alpha` sits above the 9 departments as the Market Director AI, while `markets-equity-analyst` operates inside the Market Intelligence layer as the division's equity-research specialist.

**Existing integrated subsystem:** Congress Edge / Capitol Trades bot remains part of Smart Money Intelligence and is treated as a data/execution integration rather than a new skill file in this V2 package.

## Multi-Agent Pipeline Flow

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

## Automation Schedule

| Cadence | Tasks |
| --- | --- |
| Every Morning | Overnight macro summary, global futures scan, economic calendar, breaking news, whale flow, options flow, sector strength, watchlist generation, executive briefing draft |
| Every Hour | Position review, trailing stop updates, news refresh, volatility shift check, institutional flow refresh, pending-signal queue check |
| End of Day | Journal update, strategy review, performance metrics, risk assessment, next-day planning |
| Weekly | Portfolio review, strategy optimization, marketing plan, AI evaluation, top/bottom contributor review |
| Monthly | Backtest refresh, strategy tuning, rebalance recommendations, curriculum/content refresh, discipline trend review |

## Governance Principles

1. Separate facts, analysis, and opinions in every report.
2. Require multiple independent signals before any formal recommendation.
3. Disclose uncertainty and dissenting views instead of smoothing them away.
4. Every actionable setup must include predefined exits and invalidation criteria.
5. Congressional disclosures are contextual, not predictive, and never sufficient on their own.
6. CRO approval is mandatory before execution consideration.
7. Marketing outputs must remain educational and compliance-aware.

## V3 Roadmap

- AI Vision System for chart and flow-image interpretation
- Voice Market Assistant for spoken briefings and hands-free review
- Autonomous Research Lab for deeper theme incubation and memo generation
- AI Simulation Engine for strategy stress testing and synthetic scenarios
- Personal Trade Coach for discipline reinforcement and post-trade feedback
- Multi-Agent Collaboration pipeline upgrades for adaptive routing and feedback loops
