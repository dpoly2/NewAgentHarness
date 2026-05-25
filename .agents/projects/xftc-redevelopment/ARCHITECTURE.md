# Technical Architecture — XFTC Redevelopment

## Stack Overview

| Layer | Technology |
|-------|-----------|
| CMS | WordPress (latest) |
| Theme | Grace Themes Sports Club (customized child theme) |
| Plugin | Custom PHP plugin — `xftc-membership` |
| E-commerce | WooCommerce |
| Payments | Stripe (primary), PayPal (secondary) |
| Database | MySQL via wpdb + custom tables |
| Frontend | HTML5/CSS3, jQuery, Chart.js |
| API | WP REST API (custom endpoints under `/wp-json/xftc/v1/`) |
| Version Control | GitHub — dpoly2/AgentHarness |

---

## Plugin Structure

```
xftc-membership/
├── xftc-membership.php          # Main plugin file — bootstrap, hooks
├── includes/
│   ├── class-xftc-activator.php     # Activation — create DB tables
│   ├── class-xftc-deactivator.php   # Deactivation cleanup
│   ├── class-xftc-roles.php         # Custom user roles & capabilities
│   ├── class-xftc-members.php       # Member CRUD
│   ├── class-xftc-seasons.php       # Season management
│   ├── class-xftc-registration.php  # Registration flow
│   ├── class-xftc-travel.php        # Travel/bus/hotel management
│   ├── class-xftc-meets.php         # Meet creation & management
│   ├── class-xftc-results.php       # Result input & performance stats
│   ├── class-xftc-payments.php      # Stripe/PayPal integration
│   ├── class-xftc-payroll.php       # Staff payroll system
│   ├── class-xftc-reports.php       # Reporting engine
│   └── class-xftc-emails.php        # Transactional email system
├── admin/
│   ├── class-xftc-admin.php         # Admin menu & dashboard
│   ├── views/                        # Admin page templates
│   └── assets/                       # Admin CSS/JS
├── public/
│   ├── class-xftc-public.php        # Shortcodes, front-end hooks
│   ├── views/                        # Front-end templates
│   └── assets/                       # Public CSS/JS (Chart.js, etc.)
├── api/
│   └── class-xftc-rest-api.php      # Custom REST endpoints
└── languages/                        # i18n files
```

---

## Database Schema

### wp_xftc_athletes
```sql
CREATE TABLE wp_xftc_athletes (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  parent_id     BIGINT UNSIGNED NOT NULL,          -- FK: wp_users.ID
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  dob           DATE,
  gender        ENUM('male','female','other'),
  team_level    VARCHAR(50),
  school        VARCHAR(150),
  emergency_contact_name  VARCHAR(150),
  emergency_contact_phone VARCHAR(20),
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### wp_xftc_seasons
```sql
CREATE TABLE wp_xftc_seasons (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,             -- e.g. "2026 Outdoor"
  type          ENUM('indoor','outdoor','summer','fall'),
  start_date    DATE,
  end_date      DATE,
  reg_open      DATE,
  reg_close     DATE,
  fee_standard  DECIMAL(10,2),
  fee_premium   DECIMAL(10,2),
  is_active     TINYINT(1) DEFAULT 1,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_memberships
```sql
CREATE TABLE wp_xftc_memberships (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  athlete_id    BIGINT UNSIGNED NOT NULL,
  season_id     BIGINT UNSIGNED NOT NULL,
  tier          ENUM('standard','premium'),
  status        ENUM('pending','active','expired','cancelled'),
  payment_status ENUM('unpaid','partial','paid','refunded'),
  amount_due    DECIMAL(10,2),
  amount_paid   DECIMAL(10,2) DEFAULT 0.00,
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### wp_xftc_meets
```sql
CREATE TABLE wp_xftc_meets (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(200) NOT NULL,
  meet_date     DATE,
  meet_time     TIME,
  location      VARCHAR(255),
  type          ENUM('practice','competitive','invitational'),
  categories    TEXT,                              -- JSON: sprints, hurdles, distance, field
  status        ENUM('upcoming','active','completed','cancelled'),
  created_by    BIGINT UNSIGNED,                   -- FK: wp_users.ID
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_meet_entries
```sql
CREATE TABLE wp_xftc_meet_entries (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meet_id       BIGINT UNSIGNED NOT NULL,
  athlete_id    BIGINT UNSIGNED NOT NULL,
  event_category VARCHAR(100),
  division      VARCHAR(50),
  waiver_uploaded TINYINT(1) DEFAULT 0,
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_results
```sql
CREATE TABLE wp_xftc_results (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meet_id       BIGINT UNSIGNED NOT NULL,
  athlete_id    BIGINT UNSIGNED NOT NULL,
  event_category VARCHAR(100),
  placement     INT,
  result_value  VARCHAR(50),                       -- time (00:00.00) or distance (00'00")
  result_unit   ENUM('time','distance','points'),
  is_personal_best TINYINT(1) DEFAULT 0,
  is_club_record  TINYINT(1) DEFAULT 0,
  recorded_by   BIGINT UNSIGNED,                   -- FK: wp_users.ID (coach)
  recorded_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_travel
```sql
CREATE TABLE wp_xftc_travel (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meet_id       BIGINT UNSIGNED NOT NULL,
  athlete_id    BIGINT UNSIGNED NOT NULL,
  travel_type   ENUM('bus','hotel','both'),
  bus_seat      VARCHAR(10),
  hotel_room    VARCHAR(50),
  travel_fee    DECIMAL(10,2),
  payment_status ENUM('unpaid','paid','refunded'),
  notes         TEXT,
  registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_staff
```sql
CREATE TABLE wp_xftc_staff (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL,          -- FK: wp_users.ID
  role          VARCHAR(100),
  hourly_wage   DECIMAL(10,2),
  hire_date     DATE,
  status        ENUM('active','inactive'),
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_payroll
```sql
CREATE TABLE wp_xftc_payroll (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  staff_id      BIGINT UNSIGNED NOT NULL,
  period_start  DATE,
  period_end    DATE,
  hours_worked  DECIMAL(6,2),
  gross_pay     DECIMAL(10,2),
  deductions    DECIMAL(10,2) DEFAULT 0.00,
  net_pay       DECIMAL(10,2),
  status        ENUM('pending','paid','voided'),
  paid_at       DATETIME,
  notes         TEXT,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### wp_xftc_payments
```sql
CREATE TABLE wp_xftc_payments (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  reference_type  ENUM('membership','travel','uniform','other'),
  reference_id    BIGINT UNSIGNED,
  amount          DECIMAL(10,2),
  gateway         ENUM('stripe','paypal','manual'),
  transaction_id  VARCHAR(255),
  status          ENUM('pending','completed','failed','refunded'),
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## REST API Endpoints

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| GET | /xftc/v1/athletes | List athletes | Admin, Coach |
| POST | /xftc/v1/athletes | Create athlete | Parent, Admin |
| GET | /xftc/v1/athletes/{id} | Get athlete | Parent (own), Admin |
| PUT | /xftc/v1/athletes/{id} | Update athlete | Parent (own), Admin |
| GET | /xftc/v1/seasons | List seasons | Public |
| POST | /xftc/v1/seasons | Create season | Admin |
| GET | /xftc/v1/meets | List meets | Public |
| POST | /xftc/v1/meets | Create meet | Coach, Admin |
| POST | /xftc/v1/meets/{id}/register | Register athlete for meet | Parent, Admin |
| POST | /xftc/v1/results | Enter results | Coach, Admin |
| GET | /xftc/v1/athletes/{id}/stats | Get athlete stats | Athlete, Parent, Admin |
| GET | /xftc/v1/reports/{type} | Generate report | Admin |
| POST | /xftc/v1/payments/checkout | Initiate Stripe checkout | Parent |
| POST | /xftc/v1/payments/webhook | Stripe webhook handler | System |

---

## User Roles

| WP Role | Slug | Capabilities |
|---------|------|-------------|
| Parent | xftc_parent | Register athletes, view own data, pay fees, register for meets/travel |
| Athlete | xftc_athlete | View own stats, history, upcoming meets |
| Coach | xftc_coach | Create meets, register athletes, enter results |
| Admin | xftc_admin | Full access |
| Staff | xftc_staff | Update hours, view pay history |

---

## Hosting Requirements
- PHP 8.1+
- MySQL 8.0+
- WordPress 6.4+
- SSL certificate (enforced)
- Minimum 2GB RAM recommended for WooCommerce + custom plugin
