<?php
/**
 * Plugin Name: PBS Event Commerce
 * Plugin URI:  https://psibetasigma1914.org
 * Description: Native ticketing and donation system for Psi Beta Sigma 1914 — Square, Stripe, and PayPal checkout, styled to match The Events Calendar.
 * Version:     1.0.0
 * Author:      S2T Designs
 * Author URI:  https://s2tdesigns.com
 * License:     GPL-2.0+
 * Text Domain: pbs-event-commerce
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'PBS_EC_VERSION',  '1.0.0' );
define( 'PBS_EC_PATH',     plugin_dir_path( __FILE__ ) );
define( 'PBS_EC_URL',      plugin_dir_url( __FILE__ ) );
define( 'PBS_EC_BASENAME', plugin_basename( __FILE__ ) );

// Autoload classes
$classes = [
    'PBS_DB',
    'PBS_Shortcodes',
    'PBS_Checkout',
    'PBS_Email',
    'PBS_Square',
    'PBS_Stripe',
    'PBS_PayPal',
    'PBS_Admin',
];
foreach ( $classes as $class ) {
    $file = PBS_EC_PATH . 'includes/class-' . strtolower( str_replace( '_', '-', $class ) ) . '.php';
    if ( file_exists( $file ) ) require_once $file;
}

// Activation hook — create DB tables
register_activation_hook( __FILE__, [ 'PBS_DB', 'install' ] );

// Deactivation hook
register_deactivation_hook( __FILE__, function() {
    // Keep data on deactivation; only remove on uninstall
} );

// Boot
add_action( 'plugins_loaded', function() {
    PBS_Shortcodes::init();
    PBS_Checkout::init();
    PBS_Admin::init();
} );

// Enqueue frontend assets
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style(
        'pbs-tickets',
        PBS_EC_URL . 'assets/css/pbs-tickets.css',
        [],
        PBS_EC_VERSION
    );
    wp_enqueue_script(
        'pbs-checkout',
        PBS_EC_URL . 'assets/js/pbs-checkout.js',
        [ 'jquery' ],
        PBS_EC_VERSION,
        true
    );
    wp_localize_script( 'pbs-checkout', 'PBS_EC', [
        'ajax_url'    => admin_url( 'admin-ajax.php' ),
        'nonce'       => wp_create_nonce( 'pbs_ec_nonce' ),
        'currency'    => 'USD',
        'square_app_id'      => get_option( 'pbs_square_app_id', '' ),
        'square_location_id' => get_option( 'pbs_square_location_id', '' ),
        'square_env'         => get_option( 'pbs_square_env', 'sandbox' ),
        'stripe_pub_key'     => get_option( 'pbs_stripe_publishable_key', '' ),
        'paypal_client_id'   => get_option( 'pbs_paypal_client_id', '' ),
    ] );
} );

// REST API routes
add_action( 'rest_api_init', function() {
    // Process order endpoint
    register_rest_route( 'pbs-ec/v1', '/order', [
        'methods'             => 'POST',
        'callback'            => [ 'PBS_Checkout', 'process_order' ],
        'permission_callback' => '__return_true',
    ] );
    // Get event tickets endpoint
    register_rest_route( 'pbs-ec/v1', '/tickets/(?P<event_id>\d+)', [
        'methods'             => 'GET',
        'callback'            => [ 'PBS_Checkout', 'get_event_tickets' ],
        'permission_callback' => '__return_true',
    ] );
    // Admin: get orders
    register_rest_route( 'pbs-ec/v1', '/orders', [
        'methods'             => 'GET',
        'callback'            => [ 'PBS_Admin', 'get_orders' ],
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ] );
} );
