# Market Operations Center

## Overview

The Tactical Alpha Market Intelligence Division V2 is the ArchonHub market-side operating system: 31 structured-output agents across 9 departments, coordinated by `markets-tactical-alpha`, routed through Inez, and backed by scheduler-driven automation plus Capitol Trades and Alpaca integrations.

## V2 Org Structure

| Layer | Component | Purpose |
| --- | --- | --- |
| Executive | `inez-chief-of-staff` | Executive oversight and David-facing escalation |
| Division Command | `markets-tactical-alpha` | Synthesis, prioritization, executive briefing |
| Portfolio Command | `markets-cio` / `markets-cro` | Allocation, approvals, and risk control |
| Operations Wrapper | `markets-project-lead` | Legacy wrapper, compatibility reports, documentation anchor |

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
Intelligence fusion + technical confirmation
    |
    +--> Trend / SMC / Market Structure / Technical Lead
    |
    +--> Options / Wheel / Swing / Dividend / Trail / Ladder
    |
    v
Regime -> Probability -> Backtesting -> Quant validation
    |
    v
CIO thesis + CRO approval
    |
    v
Portfolio Optimizer / Position Manager / Alpaca Execution Review
    |
    +--> Performance Analytics
    +--> Education / Content / Community
    |
    v
Tactical Alpha Director -> Inez -> David
```

## Automation Schedule

All times are Central Time.

| Time / Cadence | Job ID | Agent | Output |
| --- | --- | --- | --- |
| Mon-Fri 5:30 AM | `markets_v2_overnight_macro` | `markets-macro-analyst` | Overnight macro score, risk-on/off bias, key overnight developments |
| Mon-Fri 5:45 AM | `markets_v2_news_intelligence` | `markets-news-intelligence` | Catalyst list, scored tickers, urgent headlines |
| Mon-Fri 6:00 AM | `markets_v2_sentiment_scan` | `markets-sentiment-intelligence` | Market sentiment score and driver summary |
| Mon-Fri 6:15 AM | `markets_v2_whale_activity` | `markets-whale-tracker` | Institutional confidence score and conviction tickers |
| Mon-Fri 6:30 AM | `markets_v2_insider_scan` | `markets-insider-tracker` | Insider conviction scores from Form 4 review |
| Mon-Fri 6:45 AM | `markets_v2_regime_assessment` | `markets-regime-engine` | Day regime classification, confidence, strategy bias |
| Mon-Fri 7:00 AM | `markets_v2_options_flow` | `markets-options-strategist` | Unusual options flow and wheel candidates |
| Mon-Fri 7:30 AM | `markets_v2_watchlist_generation` | `markets-tactical-alpha` | Ranked 5-10 name watchlist with levels and confidence |
| Mon-Fri 8:00 AM | `markets_v2_probability_scan` | `markets-probability-engine` | Expected value, probability bands, setup filtering |
| Mon-Fri 8:15 AM | `markets_v2_executive_briefing` | `markets-tactical-alpha` | 5-minute executive briefing for Inez / David |
| Mon-Fri 10:00 AM hourly | `markets_v2_hourly_position_review` | `markets-position-manager` | Open-position action sheet |
| Mon-Fri 10:15 AM hourly | `markets_v2_hourly_trailing_stops` | `markets-trailing-trade-manager` | Trailing-stop adjustment recommendations |
| Mon-Fri 10:30 AM hourly | `markets_v2_hourly_news_refresh` | `markets-news-intelligence` | Intraday catalyst refresh |
| Mon-Fri 4:00 PM | `markets_v2_eod_performance` | `markets-performance-analytics` | Daily P&L, win rate, discipline metrics |
| Mon-Fri 4:15 PM | `markets_v2_eod_risk_assessment` | `markets-cro` | Exposure, concentration, drawdown, tomorrow risk flags |
| Mon-Fri 4:30 PM | `markets_v2_eod_journal` | `markets-tactical-alpha` | Trading journal and lessons learned |
| Mon-Fri 4:45 PM | `markets_v2_eod_next_day_plan` | `markets-tactical-alpha` | Next-day game plan |
| Monday 9:30 AM | `markets_v2_weekly_portfolio_review` | `markets-portfolio-optimizer` | Allocation and rebalance priorities |
| Monday 10:00 AM | `markets_v2_weekly_strategy_optimization` | `markets-backtesting-engine` | Drift analysis and strategy changes |
| Monday 10:30 AM | `markets_v2_weekly_marketing_content` | `markets-content-studio` | Weekly education/content package |
| Monday 11:00 AM | `markets_v2_weekly_performance_report` | `markets-community-manager` | Weekly recap and community report |
| 1st Monday 7:30 AM | `markets_v2_monthly_backtest_update` | `markets-backtesting-engine` | Full prior-month backtest refresh |
| 1st Monday 8:00 AM | `markets_v2_monthly_strategy_tuning` | `markets-quant` | Parameter tuning and Monte Carlo recommendations |
| 1st Monday 10:00 AM | `markets_v2_monthly_rebalance` | `markets-portfolio-optimizer` | Formal rebalance memo for CIO approval |
| 1st Monday 11:00 AM | `markets_v2_monthly_curriculum_refresh` | `markets-trading-education` | Curriculum and glossary refresh |
| Mon-Fri 9:00 AM | `capitol_trades_daily_refresh` | Capitol Trades service | Refreshed STOCK Act disclosures and generated signals |
| Mon-Fri 9:30 AM | `capitol_trades_signal_digest` | `markets-intelligence-desk` | Ranked Congress Edge signal digest for CRO |

## Morning Pipeline Diagram

```text
5:30  macro-analyst
  -> 5:45 news-intelligence
  -> 6:00 sentiment-intelligence
  -> 6:15 whale-tracker
  -> 6:30 insider-tracker
  -> 6:45 regime-engine
  -> 7:00 options-strategist
  -> 7:30 tactical-alpha watchlist build
  -> 8:00 probability-engine validation
  -> 8:15 tactical-alpha executive briefing -> Inez -> David
```

## Hourly Loop

From 10:00 AM through 3:30 PM, the scheduler runs a repeating surveillance loop: position review at the top of each hour, trailing-stop management at :15, and intraday news refresh at :30. This keeps open exposure, exits, and sudden catalysts aligned without waiting for a manual check-in.

## End-of-Day Pipeline

The 4:00 PM closeout sequence turns intraday execution into durable learning: performance metrics roll up first, CRO risk review checks exposure drift second, Tactical Alpha journals trade quality third, and the next-day plan packages what matters for the following session.

## Execution Integration

- **Alpaca:** execution review sits after signal fusion, quant validation, strategy packaging, and CRO approval. Alpaca is the execution endpoint, not the research source of truth.
- **Capitol Trades / Congress Edge:** congressional disclosures remain contextual, lagged smart-money inputs. Signals route to CRO review before any Alpaca action.
