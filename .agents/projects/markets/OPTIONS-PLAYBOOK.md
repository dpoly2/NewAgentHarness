# SmithCap FMO — Options Trading Playbook
**Author:** markets-options-strategist
**Owner:** David Smith / SmithCap FMO
**Created:** 2026-06-04
**Version:** 1.0

---

## ⚠️ Important Disclaimer

This playbook is for educational and personal trading reference only. It is NOT financial advice. Options trading involves substantial risk of loss. Never trade with money you cannot afford to lose. Always consult a licensed financial professional before making investment decisions.

---

## Part 1 — Options Fundamentals

### What Is an Option?

An option is a **contract** that gives the buyer the **right, but not the obligation**, to buy or sell 100 shares of a stock at a specified price (the **strike**) before or on a specific date (the **expiration**).

Every option has:
- **Ticker** — the underlying stock
- **Type** — Call (right to BUY) or Put (right to SELL)
- **Strike Price** — the price at which you can buy/sell the stock
- **Expiration Date** — when the contract expires
- **Premium** — the price paid/received for the contract (x100 shares)

One contract = 100 shares. A $2.00 premium = $200 actual cost.

---

### Calls vs Puts

| | Call Option | Put Option |
|---|---|---|
| **Right to...** | BUY 100 shares at strike | SELL 100 shares at strike |
| **Buyer profits when...** | Stock goes UP | Stock goes DOWN |
| **Seller profits when...** | Stock stays FLAT or goes down | Stock stays FLAT or goes up |
| **Use case (buyer)** | Bullish speculation or leverage | Bearish speculation or hedge |
| **Use case (seller)** | Income on stock you own | Income or buy stocks at a discount |

---

### Moneyness

| Term | Meaning | Example (Stock @ $100) |
|------|---------|----------------------|
| **In the Money (ITM)** | Has intrinsic value | Call with $95 strike / Put with $105 strike |
| **At the Money (ATM)** | Strike = current price | Call or Put with $100 strike |
| **Out of the Money (OTM)** | No intrinsic value yet | Call with $110 strike / Put with $90 strike |

**Rule of thumb:** Sell OTM options (premium sellers). Buy OTM options only with a strong directional thesis.

---

### The Greeks — Your Dashboard

Greeks tell you HOW an option's price will change. Understanding these is non-negotiable.

#### Delta (Δ) — Direction
- Range: 0 to 1.0 for calls / -1.0 to 0 for puts
- **Meaning:** How much the option price moves per $1 move in the stock
- Example: Delta 0.30 = option gains $0.30 if stock rises $1.00
- **Key targets:**
  - Selling premium: target 0.20–0.35 delta (OTM, high probability of expiring worthless)
  - Buying options for directional play: 0.40–0.70 delta (more responsive)
  - Deep ITM: Delta > 0.80 (acts almost like stock)

#### Theta (Θ) — Time Decay
- Always negative for option buyers / positive for option sellers
- **Meaning:** How much the option loses in value per day (time decay)
- Example: Theta = -$0.05 means the option loses $5/day per contract
- **Key insight:** Time decay accelerates in the final 30 days before expiration
- **Strategy:** When SELLING options, theta works FOR you. When BUYING, it works AGAINST you.

#### Vega (ν) — Volatility Sensitivity
- **Meaning:** How much the option price changes per 1% change in Implied Volatility (IV)
- High Vega = option price moves a lot when IV changes
- **Key insight:** IV spikes before earnings, then CRUSHES after. Option sellers want to sell high IV; option buyers want to buy low IV.
- **IV Rank (IVR):** Compares current IV to its 52-week range. IVR > 50 = elevated IV, good for selling. IVR < 30 = low IV, bad for selling.

#### Gamma (Γ) — Delta Acceleration
- **Meaning:** How fast delta changes as the stock moves
- **Danger zone:** Gamma spikes dramatically within 7–14 days of expiration (gamma risk)
- **Rule:** Close or roll short options before they get within 7 DTE unless intentional

#### Rho (ρ) — Interest Rate Sensitivity
- Least impactful for short-term trades. Matters more for long-dated LEAPS.
- Rising rates = slightly higher call prices, slightly lower put prices.

---

### Implied Volatility (IV) — The Engine

**IV = the market's expectation of future price movement**, expressed as an annualized percentage.

| IV Level | What It Means | Action |
|----------|-------------|--------|
| High IV (IVR > 50) | Market expects big moves. Premiums are EXPENSIVE. | SELL premium (covered calls, CSPs, spreads) |
| Low IV (IVR < 30) | Market is calm. Premiums are CHEAP. | BUY options (directional plays, LEAPS) |
| Medium IV (IVR 30–50) | Normal. Use judgment. | Either — depends on setup |

**IV Crush:** IV drops sharply AFTER a binary event (earnings, FDA decision). Option buyers lose even if the stock moves the "right" way. This is why buying options into earnings is risky.

---

### Bid-Ask Spread — The Hidden Cost

Every option has a bid (what buyers pay) and ask (what sellers receive). The spread between them is a transaction cost.

- **Liquid options** (NVDA, AAPL, SPY): tight spreads, $0.01–$0.10. Trade these.
- **Illiquid options** (small caps): wide spreads, $0.50–$2.00+. Avoid these.
- **Rule:** Always use limit orders. Never use market orders on options. Place your limit between the bid and ask.

---

## Part 2 — The Strategy Playbook

### Strategy Selection Matrix

| Market Outlook | IV Environment | Best Strategy |
|---------------|----------------|--------------|
| Bullish | High IV | Cash-Secured Put OR Bull Put Spread |
| Bullish | Low IV | Long Call OR LEAP Call |
| Bullish (own stock) | High IV | Covered Call |
| Neutral / Slight Bullish | High IV | Iron Condor OR Covered Call |
| Neutral / Slight Bearish | High IV | Bear Call Spread |
| Strong move expected (either direction) | Low IV | Long Straddle / Strangle |
| Bearish (own stock) | Any | Protective Put OR Collar |
| Very Bullish, long term | Low IV | LEAP Call |

---

### Strategy 1 — Covered Call (Wheel Entry — Income)

**Situation:** You OWN 100 shares of a stock. You want to generate income monthly.

**Structure:** Sell 1 OTM call for every 100 shares owned.

**Profit/Loss:**
- Max Profit = Premium received + (Strike - Stock purchase price) if called away
- Max Loss = Stock falls to zero (same risk as holding stock, reduced by premium)
- Breakeven = Stock price - Premium received

**Example:**
```
Stock: NVDA @ $210
Sell: July $225 Call @ $3.50 premium
Premium received: $350 (per contract)
Max Profit: $350 (if NVDA stays below $225 at expiration)
Called away profit: $350 + ($225-$210) x 100 = $1,850
Breakeven: $210 - $3.50 = $206.50
```

**Rules:**
- Target 0.25–0.35 delta (15–25% OTM)
- Use 30–45 DTE (days to expiration)
- Exit: buy back at 50% profit OR roll at 21 DTE
- Don't sell calls if you're not willing to sell the shares at the strike

**When to use:** Monthly income on core holdings. Great on NVDA, MSFT, AMD, SPY.

---

### Strategy 2 — Cash-Secured Put (Wheel Entry — Acquire at Discount)

**Situation:** You WANT to own a stock at a price lower than current. You have cash sitting idle.

**Structure:** Sell 1 OTM put. Keep enough cash to buy 100 shares at the strike price.

**Profit/Loss:**
- Max Profit = Premium received (if stock stays above strike)
- Max Loss = (Strike x 100) - Premium received (if stock goes to zero)
- Breakeven = Strike - Premium received

**Example:**
```
Stock: AMD @ $542
Sell: July $510 Put @ $8.00 premium
Premium received: $800
Capital required: $51,000 (cash to buy 100 shares at $510)
Max Profit: $800 (AMD stays above $510)
Breakeven: $510 - $8.00 = $502.00
If assigned: own 100 AMD at effective cost $502/share
```

**Rules:**
- Only sell at a strike where you're HAPPY to own the stock
- Keep the full cash in your account — this is not a margin play
- Target 0.25–0.35 delta, 30–45 DTE
- Exit: buy back at 50% profit OR roll if stock approaching strike

**When to use:** Earning income while waiting for a pullback. Also the entry leg of the Wheel Strategy.

---

### Strategy 3 — The Wheel Strategy (Full Cycle Income)

**Situation:** You have cash. You want to generate consistent income on stocks you'd be happy to own.

**Structure:** Repeat cycle — CSP → Own Stock → Covered Call → Repeat.

```
STEP 1: Sell Cash-Secured Put
   ↓ Stock stays above strike → Collect premium. Repeat Step 1.
   ↓ Stock drops below strike → GET ASSIGNED (own 100 shares)

STEP 2: Sell Covered Call
   ↓ Stock stays below strike → Collect premium. Repeat Step 2.
   ↓ Stock rises above strike → GET CALLED AWAY (shares sold)

STEP 3: Back to Step 1 with cash received.
```

**Best stocks for the Wheel:** High IV, liquid options, stocks you fundamentally believe in.
Good candidates: NVDA, AMD, LLY, MSFT, TSLA (for experienced traders)

**Wheel math example (Monthly):**
- $50K account, NVDA CSP at $200 strike, collect $6.50/contract/month
- Monthly income: $650 / $50K = 1.3% per month = ~15.6% annualized (not counting appreciation)

---

### Strategy 4 — Bull Put Spread (Defined Risk — Bullish)

**Situation:** Bullish on a stock but want to cap your maximum loss. Great for high-priced stocks or when you don't want to tie up a lot of cash.

**Structure:** Sell a put at a higher strike + Buy a put at a lower strike (same expiration). Net credit received.

**Profit/Loss:**
- Max Profit = Net credit received
- Max Loss = Spread width - Net credit
- Breakeven = Short strike - Net credit

**Example:**
```
Stock: SPY @ $590
Sell: July $575 Put @ $4.00
Buy:  July $560 Put @ $1.50
Net credit: $2.50 ($250 per spread)
Max Profit: $250 (SPY stays above $575)
Max Loss: ($575-$560) x 100 - $250 = $1,250
Breakeven: $575 - $2.50 = $572.50
Capital required: $1,500 (spread width x 100) - $250 (credit) = $1,250
R:R = $250 profit / $1,250 max loss = 1:5 (make 20% on margin)
```

**Rules:**
- Set the short strike below a strong support level
- Target 0.25–0.30 delta on short strike
- Close at 50% profit. Close if loss exceeds 2x credit received.
- Never risk more than 2% of account on a single spread.

---

### Strategy 5 — Bear Call Spread (Defined Risk — Neutral to Bearish)

**Situation:** Neutral or mildly bearish. Want to sell a call spread for credit above a resistance level.

**Structure:** Sell a call at lower strike + Buy a call at higher strike. Net credit received.

**Profit/Loss:**
- Max Profit = Net credit
- Max Loss = Spread width - Net credit
- Breakeven = Short call strike + Net credit

**Example:**
```
Stock: NVDA @ $210 (at resistance)
Sell: July $230 Call @ $3.00
Buy:  July $245 Call @ $1.00
Net credit: $2.00 ($200 per spread)
Max Profit: $200 (NVDA stays below $230)
Max Loss: $1,300
Breakeven: $232.00
```

**Use when:** Stock is at resistance and you expect it to stall or pull back. 

---

### Strategy 6 — Iron Condor (Neutral — Range-Bound)

**Situation:** You believe the stock will stay within a range. Collect premium from both sides.

**Structure:** Bull Put Spread + Bear Call Spread on the same stock, same expiration.

**Profit/Loss:**
- Max Profit = Total net credit (both spreads)
- Max Loss = Wider spread width - Total credit
- Two breakevens: Short put strike - credit AND Short call strike + credit

**Example:**
```
Stock: SPY @ $590
Sell $575 Put / Buy $560 Put (Bull Put Spread) → $2.50 credit
Sell $605 Call / Buy $620 Call (Bear Call Spread) → $2.00 credit
Total credit: $4.50 ($450 per iron condor)
Profit zone: SPY stays between $572.50 and $607.50 at expiration
Max loss: $1,050 (one side goes full loss)
```

**Best use:** High IV environments on broad indexes (SPY, QQQ, IWM). Monthly income play.

**Rules:**
- Manage the untested side if the stock trends strongly in one direction
- Take profit at 50% of max profit
- Never hold to expiration

---

### Strategy 7 — Long Call (Directional — Bullish Speculation)

**Situation:** High conviction bullish thesis. Want leveraged upside with defined risk.

**Structure:** Buy 1 OTM or ATM call. Pay premium upfront.

**Profit/Loss:**
- Max Profit = Unlimited (theoretically)
- Max Loss = Premium paid (fully defined)
- Breakeven = Strike + Premium paid

**Example:**
```
Stock: NVDA @ $210
Buy: August $220 Call @ $8.00 premium
Cost: $800 per contract
Breakeven: $228.00
If NVDA → $250: Call worth ~$30.00 = $3,000 profit (275% return)
If NVDA → $210: Call expires worthless = $800 loss (100% of premium)
```

**Rules:**
- Only buy when IV is LOW (IVR < 30) — cheap options
- Use at least 45–60 DTE to give the thesis time to work
- Never buy calls into earnings (IV crush)
- Size to risk no more than 1–2% of account per trade

---

### Strategy 8 — Long Put (Directional — Bearish or Hedge)

**Situation:** Bearish on a stock, or need to hedge an existing long position.

**Structure:** Buy 1 OTM or ATM put. Pay premium upfront.

**Example:**
```
Stock: Overextended stock @ $100
Buy: 45 DTE $90 Put @ $3.00
Cost: $300 per contract
Breakeven: $87.00
If stock → $75: Put worth ~$15 = $1,200 profit
If stock stays above $90: $300 loss
```

**As a hedge:** Buy a put on a large existing position when market looks extended. Treat it like insurance — pay the cost, accept it, move on.

---

### Strategy 9 — LEAP Call (Long-Term Bullish)

**Situation:** High conviction on a stock over 1–2 years but don't want to tie up capital buying shares.

**Structure:** Buy a deep ITM call with 12–24 months until expiration. Delta 0.70–0.85.

**Why LEAPS work:**
- Acts similar to owning the stock (high delta)
- Costs a fraction of buying 100 shares outright
- Defined risk (max loss = premium paid)
- Theta decay is slow on long-dated options (not the enemy here)

**Example:**
```
Stock: LLY @ $1,080
Buy: Jan 2028 $900 Call (deep ITM) @ $210 premium
Cost: $21,000 per contract vs. $108,000 to buy 100 shares
Delta: ~0.80 (moves $0.80 for every $1 LLY moves)
If LLY → $1,300 in 12 months: Call worth ~$410 = +$19,000 profit (90% return)
```

**Best for:** NVDA, LLY, MSFT — stocks with strong 2-year thesis. Buy on dips, not rips.

---

### Strategy 10 — Long Straddle (Earnings Play)

**Situation:** Earnings coming up. You expect a big move but don't know which direction.

**Structure:** Buy 1 ATM call + 1 ATM put, same strike, same expiration. Enter 1–2 days before earnings.

**Profit/Loss:**
- Profit if stock moves enough in EITHER direction to exceed premium paid
- Loss if stock barely moves (IV crush erodes value even if stock moves a little)
- Breakeven = Strike ± Total premium paid

**Example:**
```
Stock: NVDA @ $210 (earnings tomorrow)
Buy: $210 Call @ $8.00
Buy: $210 Put @ $7.50
Total cost: $15.50 ($1,550 per straddle)
Upper breakeven: $225.50
Lower breakeven: $194.50
If NVDA gaps to $235 after earnings: profit ~$900
If NVDA barely moves to $213: loss ~$1,250 (IV crush)
```

**Rules:**
- Only use if IV Rank is BELOW 50 before earnings (cheap straddle)
- EXIT on the day of earnings or the morning after — don't hold
- Position size to max 2% of account
- Skip if the stock is already pricing in a huge move (high IV = expensive straddle)

---

### Strategy 11 — Collar (Hedge an Existing Position)

**Situation:** You own stock and are nervous about downside, but don't want to sell.

**Structure:** Buy a protective put + Sell a covered call. The call premium offsets the put cost.

**Example:**
```
Own: 100 shares NVDA @ $210
Buy: $190 Put (downside protection) @ $3.50
Sell: $230 Call (cap upside) @ $3.50
Net cost: $0.00 (zero-cost collar)
Protected range: $190–$230
```

**Use when:** Sitting on a big gain and worried about a pullback but don't want to sell (taxes, conviction, etc.)

---

## Part 3 — Risk Management Rules

### The 2% Rule
**Never risk more than 2% of your total trading account on a single options trade.**

| Account Size | Max Risk Per Trade |
|-------------|-------------------|
| $10,000 | $200 |
| $25,000 | $500 |
| $50,000 | $1,000 |
| $100,000 | $2,000 |

For defined-risk trades (spreads, long options): max loss = 2% of account.
For cash-secured puts: count the full cash requirement against your account.

---

### The 21 DTE Rule
When selling premium (covered calls, CSPs, spreads), close or roll the position when it hits **21 days to expiration**. Why?

- Gamma risk spikes inside 21 DTE — small stock moves create big option price swings
- Theta accelerates, but so does the risk of things going wrong fast
- Take the remaining profit and redeploy into the next cycle

---

### The 50% Profit Rule
When a short option position has gained 50% of max profit, close it. Don't get greedy.

- You've captured most of the profit for that trade
- Holding for the last 50% exposes you to gamma risk for much smaller reward
- Close it, bank the gain, open the next trade

---

### Stop-Loss Rules

| Strategy | Stop-Loss Trigger |
|----------|-----------------|
| Short puts/calls/spreads | 2x credit received (e.g., collected $2.00 → close if position goes to -$4.00 loss) |
| Long calls/puts | 50% of premium paid (e.g., paid $8.00 → close at $4.00) |
| Long straddle | Exit day of earnings, no exceptions |
| Covered call | If stock drops significantly, evaluate the stock thesis, not the option |

---

### Position Sizing

| Strategy | Capital Requirement | Max # Open Positions |
|----------|-------------------|---------------------|
| Cash-Secured Put | Full strike x 100 | Based on cash available |
| Covered Call | None extra (own the shares) | One per 100 shares |
| Bull/Bear Spread | Max loss amount | 5–8 simultaneous |
| Long Call/Put | Premium paid | 3–5 simultaneous |
| Iron Condor | Max loss amount | 3–5 simultaneous |

**Never have more than 25% of your account in options premium risk at one time.**

---

## Part 4 — Trade Execution Checklist

Before entering ANY options trade, answer these:

```
PRE-TRADE CHECKLIST
□ What is my maximum loss on this trade?
□ Is max loss within 2% of my account?
□ What is my profit target (50% for short premium, specific target for long)?
□ What is my stop-loss trigger?
□ What is the IV Rank? (High = sell, Low = buy)
□ Is there an earnings event within the trade's lifespan? If yes — intentional?
□ Is the option liquid? (Bid-ask spread tight, open interest > 500)
□ Am I using a limit order? (Always yes)
□ Does this trade fit the current macro regime?
□ Have I logged this trade (or will I log upon entry)?
```

---

## Part 5 — Earnings Calendar Protocol

Earnings events are the highest-risk periods for options. Follow this protocol:

**7 days before earnings:**
- Check all open positions for earnings exposure
- Decide: close before earnings OR hold through (and why)

**3 days before earnings:**
- If holding through for an earnings play — structure it as a straddle or spread
- Never hold a naked long call or put into earnings (IV crush risk)

**Day of earnings (after market close):**
- If using straddle: be ready to close the next morning
- Review the move vs. your breakeven — exit if breakeven isn't achievable

**Day after earnings:**
- Close all earnings plays. Don't hope for a delayed move.

---

## Part 6 — Broker & Account Setup

### Recommended Platforms

| Broker | Best For | Options Level Needed |
|--------|---------|---------------------|
| **Tastytrade** | Options-first platform, best for premium sellers | Level 2+ |
| **TD Ameritrade (thinkorswim)** | Advanced charts + paper trading | Level 2+ |
| **Fidelity** | Long-term investing + covered calls | Level 2 |
| **Interactive Brokers** | Lowest commissions, professional grade | Level 2–3 |
| **Robinhood** | Basic options, simple interface | Level 2 |

### Options Approval Levels

| Level | What You Can Trade |
|-------|-------------------|
| **Level 1** | Covered calls only |
| **Level 2** | Long calls/puts + cash-secured puts |
| **Level 3** | Spreads (defined risk) |
| **Level 4** | Naked calls/puts (NOT recommended) |

**SmithCap FMO targets Level 3.** All strategies in this playbook require Level 2 or 3.

---

## Part 7 — SmithCap Options Risk Framework Summary

| Rule | Limit |
|------|-------|
| Max risk per trade | 2% of trading account |
| Max total options exposure | 25% of trading account |
| 21 DTE rule on short positions | Close or roll |
| 50% profit rule | Take profit and redeploy |
| Stop-loss on spreads | 2x credit received |
| Stop-loss on long options | 50% of premium paid |
| IV Rank threshold for selling | IVR > 30 preferred, >50 ideal |
| IV Rank threshold for buying | IVR < 30 preferred |
| Earnings rule | Define the trade structure before entering |
| Max single position | 10% of liquid trading capital |
| No naked options | Never. Defined risk only. |

---

## Part 8 — Quick Reference Cheat Sheet

```
BULLISH   + HIGH IV  → Sell Cash-Secured Put or Bull Put Spread
BULLISH   + LOW IV   → Buy Call or LEAP
NEUTRAL   + HIGH IV  → Iron Condor or Covered Call
BEARISH   + HIGH IV  → Bear Call Spread or Buy Put Spread
BIG MOVE? + LOW IV   → Long Straddle (earnings play)
OWN STOCK + WORRIED  → Collar or Protective Put
OWN STOCK + INCOME   → Covered Call

ALWAYS:
✅ Define max loss FIRST
✅ Use limit orders
✅ Check IV Rank before choosing buy vs. sell
✅ Check earnings calendar
✅ Close at 50% profit on short positions
✅ Close at 21 DTE on short positions
✅ Never risk more than 2% per trade

NEVER:
❌ Naked calls or puts
❌ Market orders on options
❌ Hold long straddles past earnings day
❌ Trade illiquid options (wide bid-ask)
❌ Let a losing spread go to max loss without evaluating exit
❌ Trade with emergency fund or retirement money
```

---

*SmithCap FMO — Options Playbook v1.0 | June 2026*
*markets-options-strategist | Managed by AgentHarness*
