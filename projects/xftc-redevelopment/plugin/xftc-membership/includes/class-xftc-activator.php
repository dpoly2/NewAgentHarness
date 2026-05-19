<?php
/**
 * Fired during plugin activation.
 * Creates all custom database tables using dbDelta.
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Activator {

    /**
     * Run on plugin activation.
     * Creates DB tables and sets default options.
     */
    public static function activate() {
        self::create_tables();
        self::set_default_options();
        flush_rewrite_rules();
    }

    /**
     * Create all custom plugin tables.
     */
    private static function create_tables() {
        global $wpdb;
        $charset = $wpdb->get_charset_collate();
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';

        $tables = [];

        // ── Athletes ──────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_athletes (
            id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            parent_id               BIGINT UNSIGNED NOT NULL,
            first_name              VARCHAR(100) NOT NULL,
            last_name               VARCHAR(100) NOT NULL,
            dob                     DATE DEFAULT NULL,
            gender                  ENUM('male','female','other') DEFAULT NULL,
            team_level              VARCHAR(50) DEFAULT NULL,
            school                  VARCHAR(150) DEFAULT NULL,
            emergency_contact_name  VARCHAR(150) DEFAULT NULL,
            emergency_contact_phone VARCHAR(20) DEFAULT NULL,
            created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY parent_id (parent_id)
        ) $charset;";

        // ── Seasons ───────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_seasons (
            id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            name         VARCHAR(100) NOT NULL,
            type         ENUM('indoor','outdoor','summer','fall') NOT NULL,
            start_date   DATE DEFAULT NULL,
            end_date     DATE DEFAULT NULL,
            reg_open     DATE DEFAULT NULL,
            reg_close    DATE DEFAULT NULL,
            fee_standard DECIMAL(10,2) DEFAULT 0.00,
            fee_premium  DECIMAL(10,2) DEFAULT 0.00,
            is_active    TINYINT(1) NOT NULL DEFAULT 1,
            created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) $charset;";

        // ── Memberships ───────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_memberships (
            id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            athlete_id     BIGINT UNSIGNED NOT NULL,
            season_id      BIGINT UNSIGNED NOT NULL,
            tier           ENUM('standard','premium') NOT NULL DEFAULT 'standard',
            status         ENUM('pending','active','expired','cancelled') NOT NULL DEFAULT 'pending',
            payment_status ENUM('unpaid','partial','paid','refunded') NOT NULL DEFAULT 'unpaid',
            amount_due     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            amount_paid    DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            registered_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY athlete_id (athlete_id),
            KEY season_id (season_id)
        ) $charset;";

        // ── Meets ─────────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_meets (
            id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            name       VARCHAR(200) NOT NULL,
            meet_date  DATE DEFAULT NULL,
            meet_time  TIME DEFAULT NULL,
            location   VARCHAR(255) DEFAULT NULL,
            type       ENUM('practice','competitive','invitational') NOT NULL DEFAULT 'competitive',
            categories LONGTEXT DEFAULT NULL,
            status     ENUM('upcoming','active','completed','cancelled') NOT NULL DEFAULT 'upcoming',
            created_by BIGINT UNSIGNED DEFAULT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) $charset;";

        // ── Meet Entries ──────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_meet_entries (
            id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            meet_id          BIGINT UNSIGNED NOT NULL,
            athlete_id       BIGINT UNSIGNED NOT NULL,
            event_category   VARCHAR(100) DEFAULT NULL,
            division         VARCHAR(50) DEFAULT NULL,
            waiver_uploaded  TINYINT(1) NOT NULL DEFAULT 0,
            registered_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY meet_id (meet_id),
            KEY athlete_id (athlete_id)
        ) $charset;";

        // ── Results ───────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_results (
            id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            meet_id          BIGINT UNSIGNED NOT NULL,
            athlete_id       BIGINT UNSIGNED NOT NULL,
            event_category   VARCHAR(100) DEFAULT NULL,
            placement        INT DEFAULT NULL,
            result_value     VARCHAR(50) DEFAULT NULL,
            result_unit      ENUM('time','distance','points') DEFAULT NULL,
            is_personal_best TINYINT(1) NOT NULL DEFAULT 0,
            is_club_record   TINYINT(1) NOT NULL DEFAULT 0,
            recorded_by      BIGINT UNSIGNED DEFAULT NULL,
            recorded_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY meet_id (meet_id),
            KEY athlete_id (athlete_id)
        ) $charset;";

        // ── Travel ────────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_travel (
            id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            meet_id        BIGINT UNSIGNED NOT NULL,
            athlete_id     BIGINT UNSIGNED NOT NULL,
            travel_type    ENUM('bus','hotel','both') NOT NULL DEFAULT 'bus',
            bus_seat       VARCHAR(10) DEFAULT NULL,
            hotel_room     VARCHAR(50) DEFAULT NULL,
            travel_fee     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            payment_status ENUM('unpaid','paid','refunded') NOT NULL DEFAULT 'unpaid',
            notes          TEXT DEFAULT NULL,
            registered_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY meet_id (meet_id),
            KEY athlete_id (athlete_id)
        ) $charset;";

        // ── Staff ─────────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_staff (
            id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            user_id     BIGINT UNSIGNED NOT NULL,
            role        VARCHAR(100) DEFAULT NULL,
            hourly_wage DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            hire_date   DATE DEFAULT NULL,
            status      ENUM('active','inactive') NOT NULL DEFAULT 'active',
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id)
        ) $charset;";

        // ── Payroll ───────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_payroll (
            id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            staff_id     BIGINT UNSIGNED NOT NULL,
            period_start DATE NOT NULL,
            period_end   DATE NOT NULL,
            hours_worked DECIMAL(6,2) NOT NULL DEFAULT 0.00,
            gross_pay    DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            deductions   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            net_pay      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            status       ENUM('pending','paid','voided') NOT NULL DEFAULT 'pending',
            paid_at      DATETIME DEFAULT NULL,
            notes        TEXT DEFAULT NULL,
            created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY staff_id (staff_id)
        ) $charset;";

        // ── Payments ──────────────────────────────────────────────────────────
        $tables[] = "CREATE TABLE {$wpdb->prefix}xftc_payments (
            id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            user_id        BIGINT UNSIGNED NOT NULL,
            reference_type ENUM('membership','travel','uniform','other') NOT NULL DEFAULT 'membership',
            reference_id   BIGINT UNSIGNED DEFAULT NULL,
            amount         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            gateway        ENUM('stripe','paypal','manual') NOT NULL DEFAULT 'manual',
            transaction_id VARCHAR(255) DEFAULT NULL,
            status         ENUM('pending','completed','failed','refunded') NOT NULL DEFAULT 'pending',
            created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id)
        ) $charset;";

        foreach ( $tables as $sql ) {
            dbDelta( $sql );
        }

        update_option( 'xftc_db_version', XFTC_VERSION );
    }

    /**
     * Set default plugin options on first activation.
     */
    private static function set_default_options() {
        add_option( 'xftc_stripe_mode',       'test' );
        add_option( 'xftc_stripe_public_key', '' );
        add_option( 'xftc_stripe_secret_key', '' );
        add_option( 'xftc_admin_email',       get_option( 'admin_email' ) );
        add_option( 'xftc_club_name',         'Xtreme Force Track Club' );
    }
}
