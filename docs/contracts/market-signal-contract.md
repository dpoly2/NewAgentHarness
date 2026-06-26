# Market Signal Contract

## Purpose
Defines the standard structured object for any market signal emitted inside Tactical Alpha Division V2. A signal is an informational artifact; it is **not** a formal execution recommendation until it satisfies downstream approval rules.

## Canonical Schema

```json
{
  "signal_id": "uuid",
  "source_agent": "agent_id",
  "ticker": "string",
  "signal_type": "buy|sell|hold|watch|exit",
  "conviction": "high|moderate|low",
  "confidence_score": 0,
  "timeframe": "intraday|swing|position|long-term",
  "entry_zone": {"low": 0.0, "high": 0.0},
  "stop_loss": 0.0,
  "targets": [0.0],
  "risk_reward": 0.0,
  "contributing_scores": {
    "macro_score": 0,
    "sentiment_score": 0,
    "technical_grade": "A-F",
    "smc_score": 0,
    "institutional_confidence": 0,
    "probability_score": 0
  },
  "regime": "bull|bear|sideways|high_vol|low_vol|recovery|correction",
  "reasoning": "string — full explanation",
  "dissenting_views": "string — what would invalidate this signal",
  "requires_cro_approval": false,
  "created_at": "ISO timestamp",
  "expires_at": "ISO timestamp",
  "alpaca_order_id": "uuid — set only if this signal resulted in an Alpaca submission"
}
```

## Field Definitions

| Field | Required | Definition |
| --- | --- | --- |
| `signal_id` | Yes | UUID for traceability across reports, approvals, and execution logs. |
| `source_agent` | Yes | Exact agent ID that originated the signal. |
| `ticker` | Yes | Tradable symbol or asset identifier. |
| `signal_type` | Yes | Lifecycle intent: `buy`, `sell`, `hold`, `watch`, or `exit`. |
| `conviction` | Yes | Human-readable conviction label derived from structured evidence. |
| `confidence_score` | Yes | Integer 0-100 reflecting total confidence. |
| `timeframe` | Yes | Intended holding horizon. |
| `entry_zone` | Yes for `buy`/`sell` | Low/high price range for planned entry. |
| `stop_loss` | Yes for actionable entries | Hard invalidation level. |
| `targets` | Yes for actionable entries | Ordered target prices or exit objectives. |
| `risk_reward` | Yes for actionable entries | Expected reward divided by defined risk. |
| `contributing_scores` | Yes | Core cross-desk evidence bundle. |
| `regime` | Yes | Current regime from the Regime Engine. |
| `reasoning` | Yes | Full explanation combining facts and analysis. |
| `dissenting_views` | Yes | What could invalidate the signal or why desks disagree. |
| `requires_cro_approval` | Yes | Whether the signal is trying to move toward execution consideration. |
| `created_at` | Yes | ISO-8601 timestamp when signal was emitted. |
| `expires_at` | Yes | ISO-8601 timestamp after which the signal must be refreshed. |
| `alpaca_order_id` | No | Set only after a signal is approved and submitted to Alpaca. Links signal to the `alpaca_orders` audit table. |

## Validation Rules

1. `confidence_score` must be an integer between 0 and 100.
2. `entry_zone.low` must be less than or equal to `entry_zone.high`.
3. `targets` must be non-empty for actionable `buy` or `sell` signals.
4. `risk_reward` must be greater than 0 for actionable `buy` or `sell` signals.
5. `source_agent` must match a registered markets agent ID.
6. `technical_grade` must be one of `A`, `B`, `C`, `D`, `F`.
7. `reasoning` must separate observed facts from interpretation where practical.
8. `expires_at` must be later than `created_at`.

## Signal Lifecycle

1. **Emit** — a source agent publishes a valid signal object.
2. **Fuse** — `markets-intelligence-desk`, `markets-technical-analyst`, or `markets-quant` may add supporting context.
3. **Review** — the signal is evaluated against regime, probability, and portfolio context.
4. **Risk Gate** — if `requires_cro_approval=true`, the CRO reviews it.
5. **Escalate or Archive** — approved signals move into recommendation review; stale or invalidated signals expire.

## CRO Approval Threshold

A signal requires **confidence >= 70** before it can be considered for execution review. Meeting this threshold does **not** imply approval; it only permits CRO evaluation if the rest of the contract is complete.
