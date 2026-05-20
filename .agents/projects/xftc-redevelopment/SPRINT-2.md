# Sprint 2 — Meets, Results, Travel, Payroll & Stripe (Weeks 7–10)

## Sprint Goal
Deliver full meet lifecycle management, athlete results tracking, travel/logistics booking, staff payroll system, and Stripe payment integration — all wired into the admin dashboard and parent portal.

---

## Tasks

### 1. Meet Management (Admin + Parent Portal)
- [ ] `class-xftc-meets.php` — full CRUD for meets
- [ ] Admin view: create/edit meets (name, date, time, location, type, categories)
- [ ] Admin view: meet roster — list all registered athletes per event
- [ ] Parent portal: browse upcoming meets, register athletes per event category
- [ ] Waiver upload field per meet registration entry
- [ ] Meet status workflow: upcoming → active → completed → cancelled

### 2. Meet Results Entry
- [ ] `class-xftc-results.php` — results CRUD
- [ ] Coach/Admin view: results entry form per meet (athlete, event, placement, result value)
- [ ] Auto-detect personal best (compare against athlete's prior results)
- [ ] Auto-detect club record (compare against all-time club bests)
- [ ] Parent/Athlete portal: view personal results history with PR badges
- [ ] Chart.js performance graph — progress over time per event category

### 3. Travel & Logistics
- [ ] `class-xftc-travel.php` — travel booking CRUD
- [ ] Admin view: manage bus seats + hotel rooms per meet
- [ ] Parent portal: register athlete for travel (bus/hotel/both)
- [ ] Travel fee calculation at checkout
- [ ] Seat/room assignment display on admin roster
- [ ] Travel manifest export (CSV) per meet

### 4. Payroll System
- [ ] `class-xftc-payroll.php` — payroll CRUD
- [ ] Admin view: staff list — add/edit staff (role, hourly wage, hire date, status)
- [ ] Admin view: payroll entry — select staff, period dates, hours worked → auto-calculate gross/net
- [ ] Staff portal view: logged-in staff can see their own pay history
- [ ] Payroll status workflow: pending → paid → voided
- [ ] Basic payroll summary report (exportable CSV)

### 5. Stripe Payment Integration
- [ ] `class-xftc-payments.php` — Stripe Checkout + webhook handler
- [ ] Install and configure Stripe PHP SDK (via Composer or manual include)
- [ ] Stripe Checkout session creation for:
  - Membership fees (per athlete, per season)
  - Travel fees (bus/hotel)
  - Meet entry fees (if applicable)
- [ ] Webhook handler (`/wp-json/xftc/v1/payments/webhook`) — listen for:
  - `checkout.session.completed` → mark payment completed, update membership/travel status
  - `payment_intent.payment_failed` → flag record, notify admin
- [ ] Payment history table in admin dashboard
- [ ] Receipt/confirmation email on successful payment (via `class-xftc-emails.php`)
- [ ] Manual payment entry option (cash/check) for admin

### 6. REST API Endpoints (Sprint 2 set)
- [ ] `GET /xftc/v1/meets` — list meets (public)
- [ ] `POST /xftc/v1/meets` — create meet (Coach/Admin)
- [ ] `POST /xftc/v1/meets/{id}/register` — register athlete for meet (Parent/Admin)
- [ ] `POST /xftc/v1/results` — enter results (Coach/Admin)
- [ ] `GET /xftc/v1/athletes/{id}/stats` — athlete stats + history
- [ ] `POST /xftc/v1/payments/checkout` — initiate Stripe checkout
- [ ] `POST /xftc/v1/payments/webhook` — Stripe webhook receiver

### 7. Admin Dashboard Updates
- [ ] Dashboard widgets:
  - Upcoming meets (next 30 days)
  - Recent payments (last 10 transactions)
  - Payroll due (staff with pending periods)
  - New meet registrations (count)
- [ ] Sub-menu pages: Meets, Results, Travel, Payroll (wire up existing stubs)

### 8. Parent Portal Updates
- [ ] My Athletes → per athlete: stats tab, meet history tab, travel bookings tab
- [ ] Checkout flow: select season/athlete → Stripe Checkout → confirmation page
- [ ] Order history / receipts section

### 9. GitHub Push
- [ ] All Sprint 2 source files pushed to `dpoly2/AgentHarness`
- [ ] Branch: `main` (or `sprint-2` feature branch if preferred)
- [ ] Sprint 2 tagged: `v0.2.0`

---

## New Files to Create

| File | Description |
|------|-------------|
| `includes/class-xftc-meets.php` | Meet CRUD, registration, status workflow |
| `includes/class-xftc-results.php` | Results entry, PR/record detection |
| `includes/class-xftc-travel.php` | Travel booking, seat/room management |
| `includes/class-xftc-payroll.php` | Staff payroll, period calc, CSV export |
| `includes/class-xftc-payments.php` | Stripe checkout + webhook handler |
| `api/class-xftc-rest-api.php` | All REST endpoint registrations |
| `admin/views/meets.php` | Admin meet management view |
| `admin/views/results.php` | Admin results entry view |
| `admin/views/travel.php` | Admin travel/logistics view |
| `admin/views/payroll.php` | Admin payroll view |
| `admin/views/payments.php` | Admin payment history view |
| `public/views/meets.php` | Parent portal: meet browser + registration |
| `public/views/results.php` | Parent/Athlete portal: results + chart |
| `public/views/checkout.php` | Stripe checkout flow |
| `public/views/receipts.php` | Order history + receipts |

---

## Definition of Done
- Coach/Admin can create meets and enter results in WP Admin
- Parents can browse meets and register athletes from the portal
- Travel booking (bus/hotel) available at checkout per meet
- Stripe Checkout processes membership and travel fees end-to-end
- Webhook correctly updates payment records on completion
- Staff payroll entries can be created and marked paid
- Admin dashboard shows live widgets for all Sprint 2 modules
- All code pushed to GitHub under `projects/xftc-redevelopment/plugin/`

---

## Dependencies
- Stripe account + API keys (publishable + secret) required before payment testing
- Staging site (staging.s2tdesigns.com) must have Sprint 1 plugin active
- Composer or manual Stripe PHP SDK inclusion

---

## Assignee
wordpresspluginsagent

## Timeline
Weeks 7–10 (target completion: end of week 10)
