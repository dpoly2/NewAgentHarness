# Market Report Contract

## Purpose
Standardizes recurring market reports across the Tactical Alpha Division V2 so downstream consumers can rely on consistent sections, disclaimers, and structured payloads.

## Shared Disclaimer Requirements
Every report must include:
- Educational / informational purpose statement
- Not individualized investment advice statement
- Clear timestamp and market-data freshness note
- Uncertainty disclosure when material inputs are stale, conflicting, or incomplete

## Daily Pre-Market Report Schema

### Required Fields
- `report_type`: `daily_pre_market`
- `generated_at`
- `market_regime`
- `overnight_macro_summary`
- `futures_snapshot`
- `economic_calendar`
- `top_catalysts[]`
- `top_watchlist[]`
- `pending_cro_review[]`
- `risk_posture`
- `disclaimer`

### Optional Fields
- `sector_strength`
- `options_flow_summary`
- `international_markets`
- `community_safe_summary`

## Evening Recap Schema

### Required Fields
- `report_type`: `evening_recap`
- `generated_at`
- `market_close_summary`
- `winning_themes[]`
- `losing_themes[]`
- `position_updates[]`
- `discipline_notes`
- `next_day_watch`
- `disclaimer`

### Optional Fields
- `notable_news_after_close[]`
- `trailing_stop_changes[]`
- `journal_prompt`

## Weekly Review Schema

### Required Fields
- `report_type`: `weekly_review`
- `generated_at`
- `weekly_regime_summary`
- `portfolio_performance`
- `top_contributors[]`
- `bottom_contributors[]`
- `strategy_learnings[]`
- `risk_summary`
- `next_week_priorities[]`
- `disclaimer`

### Optional Fields
- `backtest_changes[]`
- `marketing_topics[]`
- `education_content_candidates[]`

## Monthly Performance Report Schema

### Required Fields
- `report_type`: `monthly_performance`
- `generated_at`
- `monthly_return`
- `benchmark_comparison`
- `performance_report`
- `discipline_score`
- `drawdown_summary`
- `rebalance_recommendations[]`
- `strategy_adjustments[]`
- `disclaimer`

### Optional Fields
- `content_refresh_plan`
- `curriculum_refresh_plan`
- `automation_improvements[]`

## Schema Guidance
- Reports may embed structured objects from `market-signal-contract.md` and `trading-recommendation-contract.md`.
- Any missing required field should fail validation and be flagged to `markets-automation-center`.
- Optional sections should be omitted rather than populated with invented data.
