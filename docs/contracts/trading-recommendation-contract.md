# Trading Recommendation Contract

## Purpose
Defines what constitutes a **formal trade recommendation** inside Tactical Alpha Division V2. Formal recommendations are a stricter object than raw signals and may only exist after multi-desk confirmation.

## Hard Requirements
1. Minimum **3 independent confirming signals** from different departments.
2. A current **Regime Engine assessment**.
3. **Risk Manager / CRO** position-size approval.
4. Full reasoning and explicit dissenting views.
5. Formal recommendations may never be based on a single-agent output alone.

## Prohibited States
- Single-source recommendations
- Missing stop-loss or invalidation criteria
- Missing regime or probability context
- Missing CRO sign-off
- Marketing/education artifacts masquerading as formal recommendations

## Formal Recommendation Schema

```json
{
  "recommendation_id": "uuid",
  "ticker": "string",
  "action": "buy|sell|hold|exit|watch",
  "timeframe": "intraday|swing|position|long-term",
  "confirming_signals": [
    {
      "department": "Market Intelligence",
      "source_agent": "markets-news-intelligence",
      "signal_id": "uuid"
    }
  ],
  "regime_assessment": {
    "regime": "bull|bear|sideways|high_vol|low_vol|recovery|correction",
    "confidence": 0
  },
  "risk_manager_approval": {
    "source_agent": "markets-cro",
    "decision": "approved|reduced",
    "max_position_size_pct": 0.0
  },
  "entry_zone": {"low": 0.0, "high": 0.0},
  "stop_loss": 0.0,
  "targets": [0.0],
  "risk_reward": 0.0,
  "probability_score": 0,
  "reasoning": "string",
  "dissenting_views": "string",
  "cro_sign_off": true,
  "created_at": "ISO timestamp",
  "alpaca_execution": {
    "order_id": "uuid — Alpaca order ID after submission",
    "submitted_at": "ISO timestamp",
    "submitted_by": "agent_id or username",
    "symbol": "string",
    "qty": 0.0,
    "side": "buy|sell",
    "order_type": "market|limit|stop|stop_limit",
    "limit_price": null,
    "stop_price": null,
    "status": "submitted|accepted|filled|cancelled"
  }
}
```

## Validation Rules
- `confirming_signals` must contain at least 3 items from at least 3 different departments.
- `risk_manager_approval.decision` cannot be `watch` or `rejected`.
- `cro_sign_off` must be `true`.
- `reasoning` and `dissenting_views` are both mandatory.
- `risk_reward` must be positive and grounded in the supplied targets and stop.

## Process Notes
- The Tactical Alpha Director may escalate a candidate recommendation, but cannot bypass CRO sign-off.
- The CIO may adjust allocation or posture after the recommendation is formed, but cannot remove the minimum confirmation requirement.
- Recommendation objects should link back to their underlying signal IDs for auditability.
- When a recommendation proceeds to execution, populate `alpaca_execution` with the Alpaca order ID and submission details. This creates an end-to-end audit chain: signal → recommendation → Alpaca order.
- The `alpaca_execution.order_id` must match the `id` field from `POST /api/alpaca/orders` response and the corresponding row in the local `alpaca_orders` table.
