# Markets Agent Registry — Tactical Alpha Division V2

## Overview
This registry documents the 31 operating agents in the Tactical Alpha Market Intelligence Division V2. `markets-project-lead` remains the wrapper/orchestration file and is documented separately from the 31-agent operating count.

## Coordination Notes
- Division command flows through `markets-tactical-alpha`.
- Portfolio strategy flows through `markets-cio` and `markets-cro`.
- Congress Edge / Capitol Trades is an integrated Smart Money subsystem, not a new skill file in this registry.

## Registry Table

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

## Alpaca Execution Tools

Agents in Trading Strategy and Portfolio Management departments have access to the Alpaca execution API:

| Endpoint | Use case |
|----------|---------|
| `GET /api/alpaca/status` | Check if brokerage is configured and ready |
| `GET /api/alpaca/clock` | Verify market is open before placing market orders |
| `GET /api/alpaca/account` | Fetch buying power, equity, and cash |
| `GET /api/alpaca/positions` | Review current holdings |
| `POST /api/alpaca/orders` | Submit a paper or live order with `agent_reason` audit field |
| `GET /api/alpaca/quotes/{symbol}` | Latest bid/ask before sizing |
| `POST /api/alpaca/sync-positions` | Mirror brokerage positions into local `market_positions` |

All execution decisions must satisfy the **Trading Recommendation Contract** before `POST /api/alpaca/orders` is called. The `agent_reason` field is mandatory for audit trail compliance.
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
