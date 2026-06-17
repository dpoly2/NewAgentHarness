# INVOICE

**Invoice Date:** June 16, 2026  
**Invoice Number:** PBS-2026-06-001  

---

## Bill To

**Organization:** Psi Beta Sigma Fraternity, Inc.  
**Website:** newsite.psibetasigma1914.org  
**Project:** PBS Event Commerce WordPress Plugin Development

---

## From

**Developer:** Smith Capital Portfolio Development Team  
**Period:** May 27, 2026 – June 14, 2026  
**Total Hours:** 48 hours  

---

## Project Summary

Complete development, deployment, and integration of the **PBS Event Commerce** WordPress plugin (v2.0.0 → v2.4.0) for newsite.psibetasigma1914.org, including full payment gateway integration (Stripe, Square, PayPal), ProfilePress membership integration, donation system, admin UI, and comprehensive bug fixes.

---

## Detailed Work Breakdown

### Phase 1: Core Plugin Development & Payment Gateways (v2.0.0 – v2.1.0)
**Date Range:** May 27 – June 10, 2026  
**Hours:** 16 hours  

| Task | Description | Hours |
|------|-------------|-------|
| Plugin Architecture | Core plugin structure, database schema (orders, attendees, ticket types, promo codes, waitlist, custom questions), autoloader, admin menu registration | 4.0 |
| Payment Gateway Integration | Stripe payment processing with 3D Secure support, Square OAuth + payment processing, PayPal order capture | 6.0 |
| Frontend Widgets | Ticket widget shortcode, donation widget shortcode, order confirmation page, QR code generation | 3.0 |
| Admin UI Foundation | Settings page, orders page, attendees page with undefined variable fixes | 2.0 |
| Testing & Deployment | Initial v2.0.0 deployment, bug fixes, version 2.1.0 release | 1.0 |

**Deliverables:**
- ✅ Full payment processing for Stripe, Square, and PayPal
- ✅ Database schema with 6 tables
- ✅ OAuth flows for Stripe and Square
- ✅ Basic admin interface

---

### Phase 2: Square OAuth & Admin UI Enhancements (v2.1.1 – v2.2.0)
**Date Range:** June 10, 2026  
**Hours:** 12 hours  

| Task | Description | Hours |
|------|-------------|-------|
| Square OAuth Debugging | Fix connection_status() missing keys, enable OAuth button UX, robust callback handler, diagnostics panel, full token exchange exposure | 4.0 |
| Confirmation System | wp_hash() token security fix, order confirmation page auto-creation, resend confirmation email feature | 2.0 |
| Ticket Type CRUD | Full admin UI for creating, editing, deleting ticket types; donation ticket type support | 3.0 |
| Admin UI Polish | Orders page with printable receipt, attendees page full UI, ticket types page, undefined variable fixes (opcode cache compatibility) | 2.5 |
| URL Parameter Fix | Rename order_id/token to pbs_oid/pbs_tok to avoid conflicts with The Events Calendar plugin | 0.5 |

**Deliverables:**
- ✅ Square OAuth fully functional with diagnostics
- ✅ Complete ticket type management UI
- ✅ Email resend + printable receipts
- ✅ TEC compatibility fix

---

### Phase 3: Multi-Ticket Support & Donations (v2.2.1 – v2.2.5)
**Date Range:** June 11 – June 13, 2026  
**Hours:** 6 hours  

| Task | Description | Hours |
|------|-------------|-------|
| Multi-Ticket Cart | Support for purchasing multiple ticket types in a single order via qty_{id} POST fields | 2.0 |
| Donation Gateway Switch | Move donations from Square to Stripe (better UX, lower fees), add configurable donation gateway setting | 1.5 |
| Ticket Type Name Fix | Resolve ticket_type name mismatch causing invalid orders on confirmation page | 0.5 |
| Server-side Amount Validation | Enforce all amount calculations server-side per security spec; never trust client values | 1.5 |
| Testing & QA | End-to-end checkout testing for all payment methods and ticket configurations | 0.5 |

**Deliverables:**
- ✅ Multi-ticket checkout support
- ✅ Stripe donations with configurable gateway
- ✅ Server-side amount security
- ✅ Production-ready v2.2.5

---

### Phase 4: ProfilePress Integration (v2.3.0)
**Date Range:** June 13, 2026  
**Hours:** 8 hours  

| Task | Description | Hours |
|------|-------------|-------|
| PP Integration Class | Create `class-pbs-profilepress.php` with 5 integration points: gate tickets by plan, pre-fill checkout, grant membership on purchase, member discounts, "My Tickets" tab | 4.0 |
| Event Meta Fields | Add per-event PP settings: required plan, grant plan, discount plan, discount % | 1.0 |
| Settings UI | Global default grant plan setting, PP Integration admin card | 0.5 |
| API Compatibility | PlanFactory::get_plans() fallback to get_posts() for older PP versions | 1.0 |
| Checkout Integration | Wire pbs_order_complete action, pbs_order_amount filter, pbs_ticket_widget_data filter | 1.0 |
| Testing & Deployment | Manual testing of all 5 PP features, v2.3.0 deployment | 0.5 |

**Deliverables:**
- ✅ Full ProfilePress membership integration
- ✅ Member-only events
- ✅ Auto-enrollment on purchase
- ✅ Member discounts
- ✅ PP account "My Tickets" tab

---

### Phase 5: Emoji Charset Fix & Emergency Disable (v2.3.0 – v2.3.1)
**Date Range:** June 13, 2026  
**Hours:** 2 hours  

| Task | Description | Hours |
|------|-------------|-------|
| Charset Corruption Fix | Replace all 4-byte emoji literals with HTML entities across 6 PHP files; add `<meta charset="UTF-8">` to email wrapper | 1.0 |
| Emergency PP Disable | Donations stopped creating profiles due to PP user_register hooks firing inside AJAX response; emergency disable PP integration for production stability | 0.5 |
| Root Cause Analysis | Identified wp_create_user() inside active AJAX response as the root cause; ProfilePress hooks corrupt JSON output | 0.5 |

**Deliverables:**
- ✅ Emoji display fixed in email clients and admin UI
- ✅ Production stability restored
- ✅ PP integration disabled pending proper fix

---

### Phase 6: ProfilePress Re-Integration with Safety Fixes (v2.4.0)
**Date Range:** June 14, 2026  
**Hours:** 4 hours  

| Task | Description | Hours |
|------|-------------|-------|
| Database Schema Update | Add `order_type` column (ticket/donation) to pbs_orders with live ALTER TABLE migration | 0.5 |
| Donation Guards | Skip PP enrollment for donation orders; skip member discounts for donations | 0.5 |
| Deferred User Creation | Move wp_create_user() to wp_schedule_single_event() cron handler to run outside AJAX lifecycle | 1.0 |
| PP Hook Suspension | Implement suspend/restore_pp_registration_hooks() to prevent PP emails/redirects during programmatic account creation | 1.0 |
| API Version Guards | Wrap all \ProfilePress\ namespace calls in class_exists + method_exists + try/catch | 0.5 |
| Testing & Deployment | Manual verification of all 6 fix points, v2.4.0 deployment with PP re-enabled | 0.5 |

**Deliverables:**
- ✅ ProfilePress integration restored and fully functional
- ✅ Donation checkout works correctly (no user creation)
- ✅ Ticket checkout creates PP membership safely
- ✅ All PP version compatibility issues resolved
- ✅ Production-ready v2.4.0

---

## Files Created/Modified Summary

| Component | Files Modified | Lines Changed |
|-----------|----------------|---------------|
| Core Plugin | pbs-event-commerce.php | 50+ |
| Database Layer | class-pbs-db.php | 120+ |
| Checkout System | class-pbs-checkout.php | 180+ |
| Payment Gateways | class-pbs-stripe.php, class-pbs-square.php, class-pbs-paypal.php, class-pbs-square-oauth.php, class-pbs-stripe-oauth.php, class-pbs-paypal-connect.php | 450+ |
| ProfilePress Integration | class-pbs-profilepress.php | 450+ (new file) |
| Admin Interface | class-pbs-admin.php, admin/views/*.php | 600+ |
| Frontend Templates | templates/ticket-widget.php, templates/donate-widget.php, templates/confirmation.php | 250+ |
| Email System | class-pbs-email.php | 80+ |
| **Total** | **30+ PHP files** | **2,200+ lines** |

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| v2.0.0 | Jun 9, 2026 | Initial release with 3 payment gateways |
| v2.1.0 | Jun 10, 2026 | Square OAuth + confirmation system |
| v2.1.1–2.1.9 | Jun 10, 2026 | Square OAuth debugging + admin UI |
| v2.2.0–2.2.5 | Jun 10–13, 2026 | Multi-ticket + donation gateway switch |
| v2.3.0 | Jun 13, 2026 | ProfilePress integration (5 features) |
| v2.3.1 | Jun 14, 2026 | Emergency PP disable + emoji fix |
| v2.4.0 | Jun 14, 2026 | PP re-integration with safety fixes |

---

## Cost Breakdown

| Phase | Hours | Rate | Subtotal |
|-------|-------|------|----------|
| Phase 1: Core Development (v2.0.0–2.1.0) | 16.0 | $150/hr | $2,400.00 |
| Phase 2: Square OAuth & Admin UI (v2.1.1–2.2.0) | 12.0 | $150/hr | $1,800.00 |
| Phase 3: Multi-Ticket & Donations (v2.2.1–2.2.5) | 6.0 | $150/hr | $900.00 |
| Phase 4: ProfilePress Integration (v2.3.0) | 8.0 | $150/hr | $1,200.00 |
| Phase 5: Emergency Fixes (v2.3.1) | 2.0 | $150/hr | $300.00 |
| Phase 6: PP Safety Re-Integration (v2.4.0) | 4.0 | $150/hr | $600.00 |
| **Total Development** | **48.0** | **$150/hr** | **$7,200.00** |

---

## Payment Terms

**Total Amount Due:** $7,200.00  
**Payment Due:** Net 30 (July 16, 2026)  

**Accepted Payment Methods:**
- Wire Transfer
- ACH
- Check

**Bank Details:** Available upon request

---

## Deliverables Summary

✅ **PBS Event Commerce v2.4.0** — Production-ready WordPress plugin  
✅ **Payment Gateways** — Stripe, Square, PayPal fully integrated with OAuth  
✅ **ProfilePress Integration** — 5 features (member-only events, auto-enrollment, discounts, account tab, pre-fill)  
✅ **Admin Interface** — Complete CRUD for orders, attendees, ticket types, settings  
✅ **Frontend Widgets** — Ticket purchase, donations, order confirmation, QR codes  
✅ **Security** — Server-side amount validation, wp_hash() tokens, AJAX nonce protection  
✅ **Documentation** — Inline code documentation, version history, deployment zip  

---

## Support & Maintenance

**30-Day Bug Fix Warranty:** Any bugs discovered within 30 days of deployment will be fixed at no additional cost.

**Ongoing Maintenance:** Available at $125/hr for:
- Feature enhancements
- Version updates
- Security patches
- Performance optimization

---

## Notes

All source code and deployment packages have been committed to the project repository at:  
`/Users/polysqa/Documents/GitHub/NewAgentHarness/.agents/projects/xftc-plugin-product/pbs-ticketing/`

The production-ready deployment package is:  
`pbs-event-commerce.zip` (v2.4.0, 84KB)

---

**Authorized By:**  
Smith Capital Portfolio Development Team  
Date: June 16, 2026

---

*For questions regarding this invoice, please contact the development team.*
