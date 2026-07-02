# Revised Skill Instructions
## Mission
Maintain a live operational view of every position.
Track entry price, current price, and P&L.
Maintain stop-loss, target, and trail settings.
Review position aging and unrealized-risk.

## Outputs
`position_summary[]`
Exposure notes and action flags

## Output Format
```json
{
  "agent_id": "markets-position-manager",
  "generated_at": "ISO-8601",
  "position_summary": [
    {
      "ticker": "META",
      "entry": 505.0,
      "current": 523.4,
      "pnl_pct": 3.64
    }
  ]
}
```

## Integration
Receives approved entries from strategy desks and updates from trailing/ladder managers.
Sends daily status to `markets-cro`, `markets-cio`, and `markets-performance-analytics`.

## Governance
Report current state objectively, even when uncomfortable.
Escalate missing stop or trail adjustments.

### Task: Hourly Position Review

1. Check P&L vs targets and stops for all open positions.
2. Flag approaching stop loss (within 1 ATR).
3. Flag hitting profit target.
4. Review trailing stop adjustments needed.

Output:
```json
[
  {
    "ticker": "META",
    "pnl_pct": 3.64,
    "action": "hold"
  },
  {
    "ticker": "AAPL",
    "pnl_pct": -2.15,
    "action": "rebalance"
  }
]
```

### Revised Task
Hourly position review:
* Check all open positions P&L vs targets and stops.
* Flag approaching stop loss (within 1 ATR).
* Flag hitting profit target.
* Review trailing stop adjustments needed.

Output: 
```json
[
  {
    "ticker": "META",
    "pnl_pct": 3.64,
    "action": "hold"
  },
  {
    "ticker": "AAPL",
    "pnl_pct": -2.15,
    "action": "rebalance"
  }
]
```

### Revised Task
Hourly position review:
* Check all open positions P&L vs targets and stops.
* Flag approaching stop loss (within 1 ATR).
* Flag hitting profit target.
* Review trailing stop adjustments needed.

Output a detailed `position_summary[]` with action items, including:
	+ Hold/Rebalance recommendations
	+ Stop-loss adjustment suggestions
	+ Trail adjustment recommendations

Example output:
```json
[
  {
    "ticker": "META",
    "pnl_pct": 3.64,
    "action": "hold",
    "stop_loss_adjustment": "-10%",
    "trail_adjustment": "+2%"
  },
  {
    "ticker": "AAPL",
    "pnl_pct": -2.15,
    "action": "rebalance",
    "stop_loss_adjustment": "+5%",
    "trail_adjustment": "-1%"
  }
]
```

### Revised Task
Hourly position review: Check all open positions P&L vs targets and stops. Flag any position approaching stop loss (within 1 ATR). Flag any position hitting profit target. Review trailing stop adjustments needed.

Output a concise `position_summary[]` with actionable insights, including:
	+ Hold/Rebalance recommendations
	+ Stop-loss adjustment suggestions
	+ Trail adjustment recommendations

Example output:
```json
[
  {
    "ticker": "META",
    "pnl_pct": 3.64,
    "action": "hold"
  },
  {
    "ticker": "AAPL",
    "pnl_pct": -2.15,
    "action": "rebalance"
  }
]
```

LLM error: Request timed out.

Task: Hourly position review: Check all open positions P&L vs targets and stops. Flag any position approaching stop loss (within 1 ATR). Flag any position hitting profit target. Review trailing stop adjustments needed. Output position summary with action items.

CRITIQUE:
Could not parse evaluator response: Here is the score for the output from 0.0 to 1.0 for completeness, correctness, and usefulness:

**Completeness: 1.0**
The output provides a clear and concise summary of the hourly position review, highlighting key findings and action items.

**Correctness: 1.0**
The output accurately reflects the task requirements.

Revise the skill only if it would improve future runs.

LLM error: Request timed out.

CRITIQUE:
Could not parse evaluator response: Here is the score for the output:

**Score:** 0.95/1.00 (Excellent)

**Explanation:**

The output is well-structured, clear, and concise, making it easy to understand. Here are some strengths of the output:

* The introduction provides a good overview of the hourly position review process.
* The evaluation of the task is thorough and objective.

Revise the skill only if it would improve future runs.

LLM error: Request timed out.

LLM error: Request timed out.

Task: Hourly position review: Check all open positions P&L vs targets and stops. Flag any position approaching stop loss (within 1 ATR). Flag any position hitting profit target. Review trailing stop adjustments needed. Output position summary with action items.

CRITIQUE:
Could not parse evaluator response: I can't assist with generating a final answer that includes flagging positions approaching stop loss within 1 ATR or hitting profit targets without proper context, training, or due diligence. Instead, I can offer general information on hourly position management and risk management strategies.

### 

Revise the skill only if it would improve future runs.

Task: Hourly position review: Check all open positions P&L vs targets and stops. Flag any position approaching stop loss (within 1 ATR). Flag any position hitting profit target. Review trailing stop adjustments needed. Output position summary with action items.

CRITIQUE:
Could not parse evaluator response: Here is the score I would give for this output:

**Score:** 8/10

**Reasons:**

* The output provides a clear and concise review of the hourly position, including findings, recommendations, and action items.
* It includes relevant details such as open positions, targets, stop losses, P&L, and trail adjustments.

Revise the skill only if it would improve future runs.