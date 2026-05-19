# Requirements — Custom WordPress Membership Plugin

## 1. Member Registration
- Custom registration form (integrates with or replaces Gravity Forms)
- Fields: Name, Email, Phone, DOB, Guardian name (if minor), Season/Year
- Duplicate detection by email
- Auto-create WordPress user account (subscriber role)
- Welcome email on successful registration

## 2. Membership Types
- Youth Athlete (primary)
- Staff / Coach
- Sponsor / Donor
- Each type has its own fields, fees, and permissions

## 3. Payment Integration
- Stripe (one-time season fee)
- Payment status tracked per member record
- Receipt email on payment
- Unpaid members flagged in admin

## 4. Member Portal (Front-end)
- Login-protected page
- View own profile, payment status, season info
- Download waivers/releases
- View schedule

## 5. Admin Dashboard (WP Admin)
- List all members with filter by status, type, season
- Edit member records
- Export to CSV
- Send bulk email to segment (e.g. all unpaid members)
- Mark payments as received (manual entry)

## 6. Notifications / Emails
- Welcome email (on registration)
- Payment confirmation
- Renewal reminder (seasonal)
- Custom admin alerts (new signup, payment received)

## 7. Season Management
- Members tied to a season (e.g. 2026 Outdoor)
- Roll over / re-register each season
- Historical records preserved

## 8. Shortcodes / Blocks
- [xftc_register] — Registration form
- [xftc_portal] — Member portal
- [xftc_members] — Public member directory (optional, admin-controlled)

## 9. REST API Endpoints
- GET /wp-json/xftc/v1/members — list members (authenticated)
- POST /wp-json/xftc/v1/members — create member
- GET /wp-json/xftc/v1/members/{id} — get member
- PUT /wp-json/xftc/v1/members/{id} — update member

## 10. Security
- All endpoints require authentication
- Nonce verification for form submissions
- Data sanitization and validation on all inputs
- GDPR-friendly data handling
