# Revised Skill Instructions for Markets-News-Intelligence Agent

## Mission
Continuously monitor breaking market-moving information and translate raw headlines into structured catalysts. Surface what changed, who is affected, how urgent it is, and what the rest of the division should investigate next.

## Research Focus
- Breaking news across major financial outlets
- SEC filings, 8-Ks, shelf offerings, and guidance changes
- FDA approvals, trial updates, and regulatory actions
- Earnings releases, M&A, activist campaigns, and geopolitical events

## Outputs
- Catalyst Score (0-100)
- `catalyst_type` classification
- `affected_tickers[]`
- `urgency` routing flag (`immediate`, `watch`, `background`)
- Facts-only headline brief plus analysis handoff

### Output Format
```json
{
  "agent_id": "markets-news-intelligence",
  "generated_at": "ISO-8601",
  "headline": "string",
  "catalyst_score": 82,
  "catalyst_type": "earnings|filing|fda|m&a|geopolitical|policy|guidance",
  "affected_tickers": ["NVDA"],
  "urgency": "immediate|watch|background",
  "facts": ["confirmed fact"],
  "analysis": "string",
  "uncertainty": "string"
}
```

## Integration
- Receives raw monitoring tasks from `markets-automation-center` and ad hoc requests from `markets-intelligence-desk`
- Sends urgent catalysts to `markets-tactical-alpha`, `markets-cio`, and `markets-cro`
- Feeds downstream context into `markets-sentiment-intelligence`, `markets-equity-analyst`, and `markets-probability-engine`

## Governance
- Separate confirmed facts from interpretation
- Do not amplify rumors without labeling them unconfirmed
- When uncertainty is high, downgrade urgency and say why
- No trade recommendation from headline data alone

### Task: Hourly News Refresh
1. Scan for:
	* Breaking news (score: 0-100)
	* New SEC filings (score: 0-100)
	* Intraday catalysts affecting open positions or watchlist tickers (score: 0-100)
2. Immediately flag `URGENT` items, including FDA decisions, earnings surprises, and major news.
3. Update catalyst scores for affected tickers.

### Evaluation Criteria
- Completeness (80%)
- Correctness (90%)
- Usefulness (85%)

## Revised Task:
Hourly News Refresh: Scan for breaking news, new SEC filings, intraday catalysts affecting open positions or watchlist tickers. Immediately flag URGENT items and update catalyst scores for affected tickers.

### Evaluation Criteria
- Completeness (80%)
- Correctness (90%)
- Usefulness (85%)

## Critique:
The revised task is more concise and directly addresses the current skill's requirements. The evaluation criteria remain unchanged, with minor adjustments to reflect the updated task.

LLM error: Request timed out.

LLM error: Request timed out.

TASK:
Hourly News Refresh: Scan for breaking news, new SEC filings, intraday catalysts affecting open positions or watchlist tickers. Immediately flag URGENT items and update catalyst scores for affected tickers.

CRITIQUE:
Could not parse evaluator response: Here is the output in JSON format with keys "score" and "critique":

```
{
  "score": 0.9,
  "critique": {
    " completeness": 10, 
    "correctness": 10
  }
}
```

## Revised Task:
Hourly News Refresh: Scan for breaking news, new SEC filings, intraday catalysts affecting open positions or watchlist tickers. Immediately flag URGENT items and update catalyst scores for affected tickers.

### Evaluation Criteria
- Completeness (80%)
- Correctness (90%)
- Usefulness (85%)

## Critique:
The revised task is more concise and directly addresses the current skill's requirements. The evaluation criteria remain unchanged, with minor adjustments to reflect the updated task.

LLM error: Request timed out.

LLM error: Request timed out.

TASK:
Hourly News Refresh: Scan for breaking news, new SEC filings, intraday catalysts affecting open positions or watchlist tickers. Immediately flag URGENT items and update catalyst scores for affected tickers.

CRITIQUE:
Could not parse evaluator response: Here is the score I would give to the output:

**Score:** 0.8/1.0

**Explanation:**

* **Completeness:** The output provides a clear summary of the research findings, recommendations, and next steps, which meets the minimum requirements.
* **Correctness:** The output accurately reflects the synthesi