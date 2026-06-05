# PBS Ticketing Plugin — Spec
**Plugin Name:** PBS Event Commerce
**Slug:** pbs-event-commerce
**Version:** 1.0.0
**Author:** S2T Designs / AgentJames
**Status:** In Development

---

## Goal
Replace the placeholder payment links on all PBS events with a native WordPress ticketing 
system that:
- Matches the look and feel of The Events Calendar + Event Tickets (same CSS variables, 
  same card/button styles, same tribe- class structure)
- Supports Square, Stripe, and PayPal checkout natively
- Works like Zeffy/Eventbrite — ticket selection → attendee info → payment → confirmation
- Handles both TICKETS (Golf, Banquet) and DONATIONS (Back to School Drive)

---

## Pages / Flows

### Flow 1: Ticket Purchase (Golf Tournament, Scholarship Banquet)
1. Event page shows ticket widget (qty selector + ticket type + price) — SAME as TEC widget
2. "Get Tickets" → PBS checkout page (custom, styled like /tickets-checkout/)
3. Attendee info form (name, email, phone, dietary/special needs)
4. Payment selection: Square | Stripe | PayPal
5. Payment completes → confirmation email + redirect to Order Confirmation page

### Flow 2: Donation (Back to School Drive, general)
1. Page shows donation widget (preset amounts: $10, $25, $50, $100 + custom)
2. Donor info (name, email, optional message)
3. Payment selection: Square | Stripe | PayPal
4. Confirmation email + tax receipt (as 501c3 donation)

---

## Payment Gateways

### Square
- REST API v2 — Web Payments SDK (card + Apple Pay + Google Pay)
- Endpoint: POST /v2/payments
- Requires: Square App ID + Location ID + Access Token

### Stripe
- Stripe.js v3 — Card Element
- Endpoint: PaymentIntents API
- Requires: Stripe Publishable Key + Secret Key

### PayPal
- PayPal JS SDK — Smart Payment Buttons
- Handles: PayPal + Venmo + Pay Later
- Requires: PayPal Client ID

---

## Database Tables (custom)

### pbs_orders
| Column | Type | Notes |
|--------|------|-------|
| id | INT AUTO_INCREMENT | PK |
| order_number | VARCHAR(20) | PBS-YYYYMMDD-XXXX |
| event_id | INT | WP post ID of tribe_event |
| ticket_type | VARCHAR(100) | Golf Ticket, Banquet Ticket, Donation |
| quantity | INT | 1 for donations |
| amount | DECIMAL(10,2) | Total charged |
| attendee_name | VARCHAR(200) | |
| attendee_email | VARCHAR(200) | |
| attendee_phone | VARCHAR(20) | |
| payment_method | ENUM('square','stripe','paypal') | |
| payment_id | VARCHAR(200) | Gateway transaction ID |
| status | ENUM('pending','complete','failed','refunded') | |
| created_at | DATETIME | |

### pbs_attendees (for multi-attendee orders)
| Column | Type | Notes |
|--------|------|-------|
| id | INT AUTO_INCREMENT | PK |
| order_id | INT | FK → pbs_orders |
| name | VARCHAR(200) | |
| email | VARCHAR(200) | |
| phone | VARCHAR(20) | |
| ticket_type | VARCHAR(100) | |

---

## Shortcodes

| Shortcode | Usage |
|-----------|-------|
| [pbs_tickets event_id="107"] | Ticket widget for an event (on event page or standalone page) |
| [pbs_donate event_id="222" goal="5000"] | Donation widget with progress bar |
| [pbs_order_summary] | Post-checkout confirmation summary |
| [pbs_attendee_list event_id="107"] | Admin: list of registered attendees (password-gated) |

---

## Styling Strategy
- Import tribe-common CSS variables (`--tec-color-*`) so widget inherits TEC color scheme
- Use `.tribe-tickets` wrapper class on all widgets to inherit existing CSS
- Button class: `.tribe-tickets__buy` (matches TEC "Get Tickets" button)
- Card container: `.tribe-tickets__ticket-item` (matches TEC ticket card style)
- PBS Royal Blue override: `#164f90` for primary CTA buttons

---

## Files Structure
```
pbs-event-commerce/
├── pbs-event-commerce.php          ← Main plugin file, hooks, activation
├── includes/
│   ├── class-pbs-db.php            ← DB table creation + CRUD
│   ├── class-pbs-shortcodes.php    ← All shortcode registrations
│   ├── class-pbs-checkout.php      ← Order processing logic
│   ├── class-pbs-email.php         ← Confirmation + receipt emails
│   ├── class-pbs-square.php        ← Square payment gateway
│   ├── class-pbs-stripe.php        ← Stripe payment gateway
│   ├── class-pbs-paypal.php        ← PayPal gateway
│   └── class-pbs-admin.php         ← WP Admin order/attendee dashboard
├── assets/
│   ├── css/
│   │   └── pbs-tickets.css         ← Widget styles (TEC-compatible)
│   └── js/
│       ├── pbs-checkout.js         ← Checkout flow JS
│       ├── pbs-square.js           ← Square Web Payments SDK handler
│       ├── pbs-stripe.js           ← Stripe.js handler
│       └── pbs-paypal.js           ← PayPal SDK handler
├── templates/
│   ├── ticket-widget.php           ← [pbs_tickets] frontend template
│   ├── donate-widget.php           ← [pbs_donate] frontend template
│   ├── checkout.php                ← Full checkout page template
│   └── confirmation.php            ← Order confirmation template
└── admin/
    └── views/
        ├── orders.php              ← Orders list table
        └── attendees.php           ← Attendees list by event
```

---

## Credentials Needed (stored in wp_options, set via WP Admin settings page)
- `pbs_square_app_id` — Square App ID
- `pbs_square_location_id` — Square Location ID  
- `pbs_square_access_token` — Square secret token
- `pbs_stripe_publishable_key`
- `pbs_stripe_secret_key`
- `pbs_paypal_client_id`
- `pbs_paypal_mode` — sandbox | live

---

## Admin Settings Page
WP Admin → PBS Commerce → Settings
- Payment gateway toggles (enable/disable each)
- Credential fields per gateway
- Email settings (from name, from email, BCC)
- Test mode toggle

