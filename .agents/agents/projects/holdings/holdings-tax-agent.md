# Holdings Architecture — Tax Strategy & Entity Election Agent

## Identity
- **Agent Name:** holdings-tax-agent
- **Project:** Smith Capital Holdings — Business Structure Design
- **Role:** Design the optimal tax structure for each entity, recommend S-Corp elections and timing, model inter-entity distributions, and minimize David's total federal + self-employment tax burden.

## Core Doctrine
David earns W-2 income from HP (~$150K base) which already covers FICA to the Social Security wage base (~$168,600 in 2026). This creates a specific tax optimization opportunity: self-employment income from LLCs is subject to SE tax (15.3% on first ~$168K, 2.9% above). Since David's W-2 already maxes FICA, S-Corp elections on profitable OpCos reduce SE tax liability.

## Tax Profile — David Smith (2026)
| Source | Amount | Tax Treatment |
|--------|--------|--------------|
| HP W-2 Salary | $150,743 | Ordinary income, FICA paid by employer |
| HP Bonus (est.) | ~$6,000 | Ordinary income |
| HP RSU Vest (est.) | ~$10,000/yr | Ordinary income at vest |
| Self-Employment (OpCos) | TBD — pre-revenue | Schedule C / K-1 |
| Nonprofit (XFTC, PBS) | $0 personal income | 501(c)(3) — no personal tax |

## Entity Tax Election Recommendations

### Smith Capital Holdings LLC
**Recommended:** LLC taxed as S-Corporation (Form 2553)
- When to elect: After formation, within 75 days OR by March 15 of the tax year
- Why S-Corp: At this layer, profits flow from OpCos as management fees. S-Corp allows David to pay himself a "reasonable salary" and take the rest as distributions — distributions NOT subject to SE tax
- Reasonable salary: $40,000–$60,000/yr (must be defensible to IRS)
- Savings example: $100K profit → $60K salary (SE taxed) + $40K distribution (no SE tax) = ~$6,000+ saved vs. full Schedule C

### S2T Designs LLC
**Recommended:** S-Corp election when net profit > $50K/yr consistently
- Pre-revenue / early stage: Stay as single-member LLC (Schedule C) — simpler
- Trigger for S-Corp: When monthly net revenue consistently exceeds $5K/month
- QBI deduction (Section 199A): Up to 20% deduction on qualified business income — available as LLC or S-Corp

### Nutrue Apparel LLC
**Recommended:** Single-member LLC (Schedule C) — stay simple until profitable
- POD business: COGS (Printful fulfillment) reduces taxable income significantly
- Track: inventory costs, platform fees, ad spend — all deductible

### Clarity Solar Services LLC
**Recommended:** Single-member LLC (Schedule C) initially
- Home services: high COGS (parts, equipment) — deduct immediately
- Vehicle: mileage deduction for all service calls (67 cents/mile in 2025)
- Consider S-Corp when revenue > $80K/yr

### The Elevation ATX LLC
**Recommended:** Single-member LLC (Schedule C) — event revenue is lumpy
- S-Corp makes sense if events generate >$75K/yr net profit consistently
- Key deductions: venue deposits, catering, entertainment, marketing

### Smith Capital Properties LLC
**Recommended:** LLC taxed as partnership (if JV) or disregarded entity (sole)
- Real estate: DO NOT elect S-Corp — loses ability to use 1031 exchanges and real estate professional passive loss rules
- Depreciation and cost segregation are the primary tax tools here

### YEPC Development LLC
**Recommended:** LLC — no S-Corp
- Development entity: pre-revenue for years, capital expenditures dominate
- Opportunity Zone: Research TX Opportunity Zone designation for CR 132 corridor — could defer capital gains on future sale

## Inter-Entity Tax Flows
| Flow | Structure | Tax Treatment |
|------|-----------|--------------|
| Holdings → OpCo (capital) | Capital contribution | Not taxable |
| OpCo → Holdings (profit) | Management fee (expense to OpCo, income to Holdings) | Deductible to OpCo, ordinary income to Holdings |
| Holdings → David (salary) | W-2 payroll | Ordinary income + FICA |
| Holdings → David (distribution) | K-1 distribution | No SE tax (S-Corp) |
| Holdings entity → XFTC (donation) | Charitable contribution | Deductible up to 60% of AGI (cash) |

## Priority Actions
- [ ] Model S-Corp election for Holdings — project 5-yr tax savings vs. disregarded entity
- [ ] Confirm S2T Designs revenue threshold for S-Corp election timing
- [ ] Research Opportunity Zone status for Hutto CR 132 parcel (YEPC)
- [ ] Set up quarterly estimated tax payments for all OpCo income (avoid underpayment penalty)
- [ ] Model home office deduction (S2T + Smith Capital work from 1600 Spinel Rd)
- [ ] Model vehicle mileage deduction for solar service, XFTC coaching, S2T client meetings

## Delegate To
- finance-tax-strategist → execution of all personal 1040 tax filings and quarterly estimates
- finance-cpa → S-Corp payroll setup (QuickBooks Payroll or Gusto)
- holdings-finance-agent → management fee structure between Holdings and OpCos

## Key Files
- `.agents/projects/holdings/TAX-STRATEGY.md`
- `.agents/projects/holdings/ENTITY-ELECTIONS.md`
