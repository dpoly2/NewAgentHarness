# Sprint 2 — Meets, Results, Travel, Payroll & Stripe (Weeks 7–10)

## Sprint Goal
Deliver full meet lifecycle management, athlete results tracking, travel/logistics booking, staff payroll system, and Stripe payment integration — all wired into the admin dashboard and parent portal.

---

## Tasks

### 1. Meet Management (Admin + Parent Portal)
- [x] `class-xftc-meets.php` — full CRUD for meets
- [x] Admin view: create/edit meets (name, date, time, location, type, categories)
- [x] Admin view: meet roster — list all registered athletes per event
- [x] Parent portal: browse upcoming meets, register athletes per event category
- [x] Waiver upload field per meet registration entry
- [x] Meet status workflow: upcoming → active → completed → cancelled

### 2. Meet Results Entry
- [x] `class-xftc-results.php` — results CRUD
- [x] Coach/Admin view: results entry form per meet (athlete, event, placement, result value)
- [x] Auto-detect personal best (compare against athlete's prior results)
- [x] Auto-detect club record (compare against all-time club bests)
- [x] Parent/Athlete portal: view personal results history with PR badges
- [x] Chart.js performance graph — progress over time per event category

### 3. Travel & Logistics
- [x] `class-xftc-travel.php` — travel booking CRUD
- [x] Admin view: manage bus seats + hotel rooms per meet
- [x] Parent portal: register athlete for travel (bus/hotel/both)
- [x] Travel fee calculation at checkout
- [x] Seat/room assignment display on admin roster
- [x] Travel manifest export (CSV) per meet

### 4. Payroll System
- [x] `class-xftc-payroll.php` — payroll CRUD
- [x] Admin view: staff list — add/edit staff (role, hourly wage, hire date, status)
- [x] Admin view: payroll entry — select staff, period dates, hours worked → auto-calculate gross/net
- [x] Staff portal view: logged-in staff can see their own pay history
- [x] Payroll status workflow: pending → paid → voided
- [x] Basic payroll summary report (exportable CSV)

### 5. Stripe Payment Integration
- [x] `class-xftc-payments.php` — Stripe Checkout + webhook handler (placeholder — awaiting API keys)
- [x] Stripe Checkout session creation stubbed with full implementation comments
- [x] Webhook handler (`/wp-json/xftc/v1/payments/webhook`) — registered and ready
- [x] Payment history table in admin dashboard
- [x] Receipt/confirmation email on successful payment (via `class-xftc-emails.php`) — wired, awaiting keys
- [x] Manual payment entry option (cash/check) for admin
- [ ] Stripe PHP SDK installation (requires Composer on staging server)
- [ ] Live Stripe API keys entered in WP Admin → Xtreme Force → Payments

### 6. REST API Endpoints (Sprint 2 set)
- [x] `GET /xftc/v1/meets` — list meets (public)
- [x] `POST /xftc/v1/meets` — create meet (Coach/Admin)
- [x] `POST /xftc/v1/meets/{id}/register` — register athlete for meet (Parent/Admin)
- [x] `POST /xftc/v1/results` — enter results (Coach/Admin)
- [x] `GET /xftc/v1/athletes/{id}/stats` — athlete stats + history
- [x] `POST /xftc/v1/payments/checkout` — initiate Stripe checkout
- [x] `POST /xftc/v1/payments/webhook` — Stripe webhook receiver

### 7. Admin Dashboard Updates
- [ ] Dashboard widgets: Upcoming meets, Recent payments, Payroll due, New registrations
- [ ] Sub-menu pages: Meets, Results, Travel, Payroll (wire up existing stubs)

### 8. Parent Portal Updates
- [ ] My Athletes → per athlete: stats tab, meet history tab, travel bookings tab
- [x] Checkout flow: select season/athlete → Stripe Checkout → confirmation page
- [x] Order history / receipts section

### 9. GitHub Push
- [x] All Sprint 2 source files pushed to `dpoly2/AgentHarness`
- [ ] Sprint 2 tagged: `v0.2.0`

---

## New Files Created ✅

| File | Status |
|------|--------|
| `includes/class-xftc-meets.php` | ✅ Complete |
| `includes/class-xftc-results.php` | ✅ Complete |
| `includes/class-xftc-travel.php` | ✅ Complete |
| `includes/class-xftc-payroll.php` | ✅ Complete |
| `includes/class-xftc-payments.php` | ✅ Placeholder (awaiting Stripe keys) |
| `api/class-xftc-rest-api.php` | ✅ Complete |
| `admin/views/meets.php` | ✅ Complete |
| `admin/views/results.php` | ✅ Complete |
| `admin/views/travel.php` | ✅ Complete |
| `admin/views/payroll.php` | ✅ Complete |
| `admin/views/payments.php` | ✅ Complete |
| `public/views/meets.php` | ✅ Complete |
| `public/views/results.php` | ✅ Complete |
| `public/views/checkout.php` | ✅ Complete |
| `public/views/receipts.php` | ✅ Complete |

---

## Remaining Before Full Definition of Done
1. Enter Stripe API keys in WP Admin → Xtreme Force → Payments
2. Install Stripe PHP SDK on staging server via Composer
3. Wire admin dashboard widgets (Sprint 2 extension or Sprint 3)
4. Wire athlete portal tabs (stats, meet history, travel bookings)

---

## Dependencies
- Stripe account + API keys (publishable + secret) required before payment testing
- Staging site (staging.s2tdesigns.com) must have Sprint 1 plugin active
- Composer or manual Stripe PHP SDK inclusion

---

## Assignee
wordpresspluginsagent

## Completed
2026-05-20

## Timeline
Weeks 7–10 ✅
