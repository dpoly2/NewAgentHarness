<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Admin {

    public static function init() {
        add_action( 'admin_menu', [ __CLASS__, 'register_menu' ] );
        add_action( 'admin_init', [ __CLASS__, 'register_settings' ] );
        add_action( 'admin_enqueue_scripts', [ __CLASS__, 'enqueue_admin_assets' ] );
    }

    public static function register_menu() {
        add_menu_page(
            'PBS Commerce',
            'PBS Commerce',
            'manage_options',
            'pbs-commerce',
            [ __CLASS__, 'orders_page' ],
            'dashicons-tickets-alt',
            30
        );
        add_submenu_page( 'pbs-commerce', 'Orders',     'Orders',     'manage_options', 'pbs-commerce',          [ __CLASS__, 'orders_page' ] );
        add_submenu_page( 'pbs-commerce', 'Ticket Types','Ticket Types','manage_options','pbs-ticket-types',     [ __CLASS__, 'ticket_types_page' ] );
        add_submenu_page( 'pbs-commerce', 'Settings',   'Settings',   'manage_options', 'pbs-commerce-settings', [ __CLASS__, 'settings_page' ] );
    }

    public static function register_settings() {
        $options = [
            'pbs_stripe_publishable_key', 'pbs_stripe_secret_key',
            'pbs_square_app_id', 'pbs_square_location_id', 'pbs_square_access_token', 'pbs_square_env',
            'pbs_paypal_client_id', 'pbs_paypal_secret', 'pbs_paypal_mode',
            'pbs_email_from', 'pbs_email_from_name', 'pbs_email_bcc',
            'pbs_treasurer_email', 'pbs_confirmation_page_id',
        ];
        foreach ( $options as $opt ) {
            register_setting( 'pbs_commerce_settings', $opt );
        }
    }

    public static function enqueue_admin_assets( $hook ) {
        if ( strpos( $hook, 'pbs-commerce' ) === false && strpos( $hook, 'pbs-ticket' ) === false ) return;
        wp_enqueue_style( 'pbs-admin', PBS_EC_URL . 'assets/css/pbs-tickets.css', [], PBS_EC_VERSION );
    }

    public static function orders_page() {
        $event_filter = isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0;
        $status_filter = sanitize_text_field( $_GET['status'] ?? '' );
        $orders = PBS_DB::get_orders( array_filter( [ 'event_id' => $event_filter, 'status' => $status_filter ] ) );
        include PBS_EC_PATH . 'admin/views/orders.php';
    }

    public static function ticket_types_page() {
        include PBS_EC_PATH . 'admin/views/ticket-types.php';
    }

    public static function settings_page() {
        include PBS_EC_PATH . 'admin/views/settings.php';
    }

    /** REST endpoint: get orders */
    public static function get_orders( WP_REST_Request $request ) {
        $args = [
            'event_id' => (int) $request->get_param( 'event_id' ),
            'status'   => sanitize_text_field( $request->get_param( 'status' ) ),
            'limit'    => (int) $request->get_param( 'limit' ) ?: 200,
        ];
        return rest_ensure_response( PBS_DB::get_orders( array_filter( $args ) ) );
    }
}
