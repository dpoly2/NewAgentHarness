# SmithCap FMO — Bookkeeping Setup Guide
**Created:** 2026-05-24
**Managed By:** finance-bookkeeper
**Platform Recommendation:** Wave (free) — upgrade to QuickBooks when revenue >$5K/mo per entity

---

## Recommended Bookkeeping Stack

| Tool | Purpose | Cost | Priority |
|------|---------|------|----------|
| **Wave** | Core bookkeeping — income, expenses, invoicing | Free | 🔴 Set up now |
| **Expensify** or **Dext** | Receipt capture on mobile | Free tier / $10/mo | 🟡 Q3 2026 |
| **Google Sheets** | Cross-entity dashboard (until QuickBooks) | Free | 🟡 Build now |
| **Gusto** | Payroll (when employees hired) | $40+/mo | ⬜ Future |
| **QuickBooks Online** | Upgrade when complex | $30–$90/mo | ⬜ 2027 |

---

## Entity Bank Account Structure

> **Rule:** One dedicated bank account per LLC. Never co-mingle personal and business funds.

| Entity | Account Type | Recommended Bank | Status |
|--------|-------------|-----------------|--------|
| David Smith (Personal) | Checking + HYSA | Any + Marcus/Ally | ⬜ Confirm |
| S2T Designs | Business Checking | Mercury or Chase Business | 🔴 Open ASAP |
| The Elevation LLC | Business Checking | Mercury | ⬜ After LLC filed |
| Smith Capital LLC | Business Checking | Mercury or Frost Bank | ⬜ After LLC filed |
| Nutrue Apparel LLC | Business Checking | Mercury | ⬜ After LLC filed |
| XFTC | Nonprofit Checking | Local credit union or Chase | ✅ Should exist |
| PBS Foundation | Nonprofit Checking | Local credit union | ⬜ After IRS approval |

> **Mercury Bank** is highly recommended for LLCs — no monthly fees, no minimums, instant account opening online, built for startups.

---

## Chart of Accounts — All Entities

### INCOME ACCOUNTS
| Code | Account | Entity |
|------|---------|--------|
| 4000 | Web Design Revenue | S2T Designs |
| 4010 | Plugin / Dev Revenue | S2T Designs |
| 4020 | Monthly Retainer Revenue | S2T Designs |
| 4100 | Membership Fees | XFTC |
| 4110 | Registration Fees | XFTC |
| 4120 | Donations — Unrestricted | XFTC |
| 4130 | Donations — Restricted | XFTC |
| 4140 | Grant Income | XFTC / PBS |
| 4200 | Event Ticket Sales | The Elevation |
| 4210 | Table / VIP Revenue | The Elevation |
| 4220 | Sponsorship Revenue | The Elevation |
| 4300 | Product Sales — Apparel | Nutrue Apparel |
| 4310 | Wholesale Revenue | Nutrue Apparel |
| 4400 | Consulting Revenue | Smith Capital |
| 4410 | Rental Income | Smith Capital (future) |
| 4900 | Miscellaneous Income | All |

### EXPENSE ACCOUNTS
| Code | Account | Notes |
|------|---------|-------|
| 5000 | Payroll — Salaries | When employees added |
| 5010 | Contract Labor / 1099 | Freelancers, subcontractors |
| 5100 | Software & Subscriptions | Base44, GitHub, hosting, Canva, etc. |
| 5110 | Website / Hosting | WP hosting, domain fees |
| 5200 | Marketing & Advertising | Meta ads, TikTok, print |
| 5210 | Promotional Materials | XFTC promo, uniforms |
| 5300 | Professional Services | CPA, legal, consultants |
| 5310 | Filing & Licensing Fees | TX SOS, EIN, permits |
| 5400 | Equipment & Technology | Computers, cameras, hardware |
| 5410 | Office Supplies | Paper, ink, etc. |
| 5500 | Travel | Mileage, flights, lodging |
| 5510 | Meals & Entertainment | 50% deductible |
| 5600 | Facilities / Rent | Office, event venue rental |
| 5700 | Insurance | E&O, GL, life, disability |
| 5800 | Cost of Goods Sold | Nutrue — Printful fulfillment cost |
| 5810 | Event Production Costs | The Elevation — venue, talent, F&B |
| 5900 | Bank Fees | Monthly fees, transfer fees |
| 5910 | Merchant Processing | Stripe, PayPal fees |
| 6000 | Depreciation | Assets over time |
| 6100 | Interest Expense | Loan interest |
| 6900 | Miscellaneous Expense | Catch-all |

---

## Monthly Close Checklist

### Week 1 of Every Month (for Prior Month)
- [ ] Import all bank transactions into Wave
- [ ] Categorize every transaction to correct account
- [ ] Match receipts to expenses (use Expensify or photo uploads)
- [ ] Record any invoices issued (S2T client invoices)
- [ ] Record any payments received

### Week 2
- [ ] Reconcile all bank accounts (Wave reconciliation tool)
- [ ] Review AR — flag any overdue invoices (S2T clients)
- [ ] Review AP — confirm all vendors paid
- [ ] Verify payroll or contractor payments are recorded

### Week 3
- [ ] Produce monthly P&L per entity
- [ ] Produce cash position summary
- [ ] Send monthly report to finance-cfo
- [ ] Flag any anomalies or unresolved transactions

### Week 4
- [ ] Prepare for next month — outstanding invoices, upcoming expenses
- [ ] Confirm estimated tax tracking is current
- [ ] Update DASHBOARD.md with latest revenue/expense figures

---

## Mileage & Home Office Tracking

### Vehicle Mileage (IRS Rate: $0.67/mile for 2026)
Track every business trip. Use a simple Google Sheet or MileIQ app.

| Date | From | To | Purpose | Miles | Entity |
|------|------|----|---------|-------|--------|
| Example | Home | XFTC practice | Coaching supervision | 12 | XFTC |
| Example | Home | Client meeting | S2T client kickoff | 25 | S2T |

**Annual target:** Track every business mile. At $0.67/mile, 3,000 miles = $2,010 deduction.

### Home Office Deduction
Requires a dedicated, regularly used space for business.

| Method | Calculation | Est. Deduction |
|--------|-------------|---------------|
| Simplified | $5/sq ft × sq ft (max 300 sq ft) | Up to $1,500/yr |
| Actual | % of home used for business × home expenses | $2K–$5K/yr typical |

> **Recommended:** Actual method if home expenses are high. Set up once, track consistently.

---

## Annual 1099 Process

Every January, issue 1099-NEC to any individual or unincorporated business paid $600+ in the prior year.

### 1099 Checklist
- [ ] Collect W-9 from every contractor BEFORE first payment (not after)
- [ ] Track all contractor payments in Wave throughout the year
- [ ] Pull 1099-eligible payments list by January 10
- [ ] File 1099-NEC with IRS by January 31
- [ ] Mail or email copies to contractors by January 31
- [ ] Use IRS FIRE system or a platform like Track1099 or Tax1099 for e-filing

### Entities That Will Issue 1099s
| Entity | Likely Contractors |
|--------|-------------------|
| S2T Designs | Freelance designers, developers, copywriters |
| XFTC | Coaches, admin staff (if paid $600+) |
| The Elevation | DJs, event staff, photographers, venue staff |
