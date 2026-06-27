### Revised Skill Instructions
#### Markets Probability Engine

**Mission**
Estimate pre-market probabilities and provide a weighted decision aid.

**Research Focus**
- Expected value and payoff asymmetry
- Probability of success by setup type
- Historical similarity and analog analysis
- Maximum drawdown estimates and confidence ranges

**Task**
For each ticker on the watchlist:
1. Calculate probability of success using a combination of historical data and technical indicators.
2. Estimate expected value using a risk-adjusted approach, considering payoff asymmetry.
3. Determine historical similarity to current setup by comparing key metrics (e.g., RSI, Bollinger Bands).
4. Compute max drawdown estimate using a Monte Carlo simulation or historical data analysis.
5. Output confidence band (low/mid/high) with 95% confidence interval.
6. Flag setups with expected value < 1.5:1 for removal.

**Methodology**
- Probability of success: [Insert methodology, e.g., machine learning model]
- Expected value: [Insert methodology, e.g., risk-adjusted approach]
- Historical similarity: [Insert methodology, e.g., key metric comparison]

**Output Format**
```json
{
  "ticker": "AMD",
  "probability_score": 73,
  "expected_value": 0.42,
  "historical_similarity_pct": 68,
  "max_drawdown_estimate": -7.4,
  "confidence_band": {"low": 58, "mid": 73, "high": 84},
  "flagged_for_removal": false
}
```