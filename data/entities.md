# Data Entities — Xtreme Force Track Club

## XtremeForceAthlete
Tracks athlete signups for each season.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Athlete full name |
| email | string | Contact email |
| phone | string | Contact phone |
| signup_date | string | Date of registration |
| status | string | Active / Inactive / Pending |
| notes | string | Additional notes |

## XtremeForcePayment
Tracks payments received from athletes/families.

| Field | Type | Description |
|-------|------|-------------|
| payer_name | string | Name of payer |
| email | string | Payer email |
| amount | number | Payment amount ($) |
| payment_date | string | Date of payment |
| payment_type | string | Registration / Uniform / Other |
| status | string | Confirmed / Pending / Refunded |
| notes | string | Additional notes |
