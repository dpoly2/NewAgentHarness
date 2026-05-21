<?php
/**
 * Class TS_Dashboard_Widgets
 * Registers admin dashboard widgets: Upcoming meets, Recent payments, Payroll due, New registrations
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class TS_Dashboard_Widgets {
    public static function init() {
        add_action( 'wp_dashboard_setup', [ __CLASS__, 'register_widgets' ] );
    }

    public static function register_widgets() {
        wp_add_dashboard_widget( 'ts_upcoming_meets', 'Upcoming Meets', [ __CLASS__, 'widget_upcoming_meets' ] );
        wp_add_dashboard_widget( 'ts_recent_payments', 'Recent Payments', [ __CLASS__, 'widget_recent_payments' ] );
        wp_add_dashboard_widget( 'ts_payroll_due', 'Payroll Due', [ __CLASS__, 'widget_payroll_due' ] );
        wp_add_dashboard_widget( 'ts_new_registrations', 'New Registrations', [ __CLASS__, 'widget_new_registrations' ] );
    }

    public static function widget_upcoming_meets() {
        echo '<p>Placeholder: upcoming meets list (implement DB queries).</p>';
    }

    public static function widget_recent_payments() {
        echo '<p>Placeholder: recent payments list (implement DB queries).</p>';
    }

    public static function widget_payroll_due() {
        echo '<p>Placeholder: payroll due (implement payroll query).</p>';
    }

    public static function widget_new_registrations() {
        echo '<p>Placeholder: new registrations (recent signups).</p>';
    }
}

TS_Dashboard_Widgets::init();
