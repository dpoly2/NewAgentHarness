<?php
/**
 * Plugin Name: PBS Event Commerce
 * Plugin URI:  https://psibetasigma1914.org
 * Description: Native ticketing and donation system for Psi Beta Sigma 1914 - Square, Stripe, and PayPal checkout.
 * Version:     2.1.0
 * Author:      S2T Designs
 * Author URI:  https://s2tdesigns.com
 * License:     GPL-2.0+
 * Text Domain: pbs-event-commerce
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'PBS_EC_VERSION',  '2.1.0' );
define( 'PBS_EC_PATH',     plugin_dir_path( __FILE__ ) );
define( 'PBS_EC_URL',      plugin_dir_url( __FILE__ ) );
define( 'PBS_EC_BASENAME', plugin_basename( __FILE__ ) );

// Autoload all classes
$pbs_classes = array(
    'PBS_DB', 'PBS_Shortcodes', 'PBS_Checkout', 'PBS_Email',
    'PBS_Square', 'PBS_Stripe', 'PBS_PayPal', 'PBS_Admin',
    'PBS_QR', 'PBS_Discount', 'PBS_Waitlist', 'PBS_Custom_Questions',
    'PBS_Refund', 'PBS_Reports', 'PBS_Square_OAuth', 'PBS_Stripe_OAuth',
    'PBS_PayPal_Connect', 'PBS_Webhooks',
);
foreach ( $pbs_classes as $pbs_class ) {
    $pbs_file = PBS_EC_PATH . 'includes/class-' . strtolower( str_replace( '_', '-', $pbs_class ) ) . '.php';
    if ( file_exists( $pbs_file ) ) require_once $pbs_file;
}

// Activation — install all DB tables
register_activation_hook( __FILE__, array( 'PBS_DB', 'install' ) );

// Boot
add_action( 'plugins_loaded', function() {
    PBS_Shortcodes::init();
    PBS_Checkout::init();
    PBS_Admin::init();
    PBS_Square_OAuth::init();
    PBS_Stripe_OAuth::init();
    PBS_PayPal_Connect::init();

    add_action( 'pbs_square_token_refresh', function() {
        $expires = get_option( 'pbs_square_token_expires', '' );
        if ( ! $expires ) {
            return;
        }

        $exp_ts = strtotime( $expires );
        if ( $exp_ts && ( $exp_ts - time() ) < 7 * DAY_IN_SECONDS ) {
            PBS_Square_OAuth::refresh_token();
        }
    } );

    if ( ! wp_next_scheduled( 'pbs_square_token_refresh' ) ) {
        wp_schedule_event( time(), 'daily', 'pbs_square_token_refresh' );
    }
} );

// Frontend assets
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style( 'pbs-tickets', PBS_EC_URL . 'assets/css/pbs-tickets.css', array(), PBS_EC_VERSION );
    wp_enqueue_script( 'pbs-checkout', PBS_EC_URL . 'assets/js/pbs-checkout.js', array( 'jquery' ), PBS_EC_VERSION, true );
    wp_localize_script( 'pbs-checkout', 'PBS_EC', array(
        'ajax_url'                  => admin_url( 'admin-ajax.php' ),
        'rest_url'                  => rest_url( 'pbs-ec/v1/' ),
        'nonce'                     => wp_create_nonce( 'pbs_ec_nonce' ),
        'rest_nonce'                => wp_create_nonce( 'wp_rest' ),
        'currency'                  => 'USD',
        'square_app_id'             => get_option( 'pbs_square_app_id', '' ),
        'square_location_id'        => get_option( 'pbs_square_location_id', '' ),
        'square_env'                => get_option( 'pbs_square_env', 'sandbox' ),
        'stripe_pub_key'            => get_option( 'pbs_stripe_publishable_key', '' ),
        'paypal_client_id'          => get_option( 'pbs_paypal_client_id', '' ),
        'paypal_create_order_url'   => rest_url( 'pbs-ec/v1/paypal/create-order' ),
    ) );
} );

// REST API routes — all v2 additions
add_action( 'rest_api_init', function() {

    // Webhook endpoints — spec §8: all gateways
    PBS_Webhooks::register_routes();

    // PayPal server-side order creation — spec §13 Three-Party SDK Flow
    register_rest_route( 'pbs-ec/v1', '/paypal/create-order', [
        'methods'             => 'POST',
        'callback'            => function( WP_REST_Request $req ) {
            $nonce = $req->get_header( 'x-wp-nonce' ) ?: $req->get_param( 'nonce' );
            if ( ! wp_verify_nonce( $nonce, 'wp_rest' ) ) {
                return new WP_REST_Response( [ 'success' => false, 'message' => 'Security check failed.' ], 403 );
            }

            $event_id    = (int) $req->get_param( 'event_id' );
            $ticket_type = sanitize_text_field( $req->get_param( 'ticket_type' ) ?? '' );
            $quantity    = max( 1, (int) ( $req->get_param( 'quantity' ) ?? 1 ) );

            if ( ! $event_id ) {
                return new WP_REST_Response( [ 'success' => false, 'message' => 'Event not specified.' ], 400 );
            }

            // Server-side amount calculation — never trust client amount
            $ticket = $ticket_type ? PBS_DB::get_ticket_type_by_name( $event_id, $ticket_type ) : null;
            if ( $ticket ) {
                $amount = (int) $ticket['is_donation']
                    ? max( 1.0, (float) $req->get_param( 'amount' ) )
                    : round( (float) $ticket['price'] * $quantity, 2 );
            } else {
                $amount = max( 0.0, (float) $req->get_param( 'amount' ) );
            }

            $result = PBS_PayPal::create_order( $event_id, [
                'ticket_type' => $ticket_type,
                'quantity'    => $quantity,
                'amount'      => $amount,
            ] );

            if ( is_wp_error( $result ) ) {
                return new WP_REST_Response( [ 'success' => false, 'message' => $result->get_error_message() ], 400 );
            }

            return new WP_REST_Response( [ 'success' => true, 'paypal_order_id' => $result['paypal_order_id'] ] );
        },
        'permission_callback' => '__return_true',
    ] );

    // Core ticket/order endpoints
    register_rest_route( 'pbs-ec/v1', '/order', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_Checkout', 'process_order' ),
        'permission_callback' => '__return_true',
    ) );
    register_rest_route( 'pbs-ec/v1', '/tickets/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_Checkout', 'get_event_tickets' ),
        'permission_callback' => '__return_true',
    ) );
    register_rest_route( 'pbs-ec/v1', '/orders', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_Admin', 'get_orders' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );

    // Ticket types CRUD
    register_rest_route( 'pbs-ec/v1', '/ticket-types/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => function( WP_REST_Request $req ) {
            global $wpdb;
            return $wpdb->get_results( $wpdb->prepare(
                "SELECT * FROM {$wpdb->prefix}pbs_ticket_types WHERE event_id = %d ORDER BY sort_order ASC",
                (int) $req['event_id']
            ), ARRAY_A );
        },
        'permission_callback' => '__return_true',
    ) );

    // Seed ticket types (admin)
    register_rest_route( 'pbs-ec/v1', '/seed-tickets', array(
        'methods'             => 'POST',
        'callback'            => function( WP_REST_Request $req ) {
            global $wpdb;
            $table = $wpdb->prefix . 'pbs_ticket_types';
            if ( class_exists('PBS_DB') ) PBS_DB::install();
            $wpdb->query( "DELETE FROM $table WHERE 1=1" );

            $tickets = array(
                // EVENT 107: Golf Tournament (Oct 3, 2026)
                array('event_id'=>107,'name'=>'Individual Player','description'=>'One player entry. Includes green fees, cart, breakfast buffet, and range balls.','price'=>150.00,'capacity'=>72,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-09-26 23:59:59','is_donation'=>0,'sort_order'=>1,'active'=>1),
                array('event_id'=>107,'name'=>'Foursome Package','description'=>'4 player entries at a group rate. Best value for teams.','price'=>550.00,'capacity'=>18,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-09-26 23:59:59','is_donation'=>0,'sort_order'=>2,'active'=>1),
                array('event_id'=>107,'name'=>'Hole Sponsorship','description'=>'Sponsor a hole with signage at the tee box. Includes 1 player entry.','price'=>250.00,'capacity'=>18,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-09-26 23:59:59','is_donation'=>0,'sort_order'=>3,'active'=>1),
                array('event_id'=>107,'name'=>'Donation - Scholarship Fund','description'=>'Support the scholarship fund without playing. Tax-deductible.','price'=>0.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-10-03 23:59:59','is_donation'=>1,'sort_order'=>4,'active'=>1),
                // EVENT 222: Back to School Supply Drive (Aug 8, 2026)
                array('event_id'=>222,'name'=>'Custom Donation','description'=>'Your donation provides school supplies for students in need in the Austin/Pflugerville area. 100% of funds go to supplies.','price'=>0.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-08-08 23:59:59','is_donation'=>1,'sort_order'=>1,'active'=>1),
                array('event_id'=>222,'name'=>'Student Bundle Sponsor','description'=>'Sponsor one student complete supply bundle - backpack, notebooks, pencils, and essentials.','price'=>50.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-08-08 23:59:59','is_donation'=>1,'sort_order'=>2,'active'=>1),
                array('event_id'=>222,'name'=>'Classroom Sponsor','description'=>'Fully supply an entire classroom of 25 students.','price'=>250.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-08-08 23:59:59','is_donation'=>1,'sort_order'=>3,'active'=>1),
                // EVENT 224: Scholarship Banquet (Nov 14, 2026)
                array('event_id'=>224,'name'=>'General Admission','description'=>'One ticket. Includes dinner and awards program.','price'=>75.00,'capacity'=>200,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-11-07 23:59:59','is_donation'=>0,'sort_order'=>1,'active'=>1),
                array('event_id'=>224,'name'=>'Table of 8','description'=>'Reserve a full table of 8 guests at a discounted group rate.','price'=>550.00,'capacity'=>25,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-11-07 23:59:59','is_donation'=>0,'sort_order'=>2,'active'=>1),
                array('event_id'=>224,'name'=>'VIP Table of 8','description'=>'Premium front-section table with program recognition and on-stage acknowledgment.','price'=>750.00,'capacity'=>5,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-11-07 23:59:59','is_donation'=>0,'sort_order'=>3,'active'=>1),
                array('event_id'=>224,'name'=>'Donation - Scholarship Fund','description'=>'Support a student scholarship without attending. Tax-deductible.','price'=>0.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-06-05 00:00:00','ticket_end'=>'2026-11-14 23:59:59','is_donation'=>1,'sort_order'=>4,'active'=>1),
                // EVENT 223: Founder's Day (Jan 9, 2027)
                array('event_id'=>223,'name'=>'Free RSVP','description'=>"Free admission. Reserve your spot for Founder's Day celebration.'",'price'=>0.00,'capacity'=>150,'sold'=>0,'ticket_start'=>'2026-10-01 00:00:00','ticket_end'=>'2027-01-08 23:59:59','is_donation'=>0,'sort_order'=>1,'active'=>1),
                array('event_id'=>223,'name'=>'Donation - Chapter Fund','description'=>"Celebrate Founder's Day by supporting the chapter general fund.",'price'=>0.00,'capacity'=>0,'sold'=>0,'ticket_start'=>'2026-10-01 00:00:00','ticket_end'=>'2027-01-09 23:59:59','is_donation'=>1,'sort_order'=>2,'active'=>1),
            );

            $inserted = 0;
            foreach ( $tickets as $t ) {
                if ( $wpdb->insert( $table, $t ) ) $inserted++;
            }
            return array( 'success' => true, 'inserted' => $inserted, 'total' => count($tickets) );
        },
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );

    // QR check-in
    register_rest_route( 'pbs-ec/v1', '/checkin', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_QR', 'checkin' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );
    register_rest_route( 'pbs-ec/v1', '/checkin-list/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_QR', 'checkin_list' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );

    // Promo codes
    register_rest_route( 'pbs-ec/v1', '/validate-promo', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_Discount', 'rest_validate' ),
        'permission_callback' => '__return_true',
    ) );

    // Waitlist
    register_rest_route( 'pbs-ec/v1', '/waitlist', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_Waitlist', 'rest_join' ),
        'permission_callback' => '__return_true',
    ) );

    // Custom questions
    register_rest_route( 'pbs-ec/v1', '/questions/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_Custom_Questions', 'rest_get' ),
        'permission_callback' => '__return_true',
    ) );

    // Refunds & transfers
    register_rest_route( 'pbs-ec/v1', '/refund', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_Refund', 'rest_refund' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );
    register_rest_route( 'pbs-ec/v1', '/transfer', array(
        'methods'             => 'POST',
        'callback'            => array( 'PBS_Refund', 'rest_transfer' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );

    // Reports
    register_rest_route( 'pbs-ec/v1', '/reports/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_Reports', 'rest_summary' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );
    register_rest_route( 'pbs-ec/v1', '/export/(?P<event_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => array( 'PBS_Reports', 'rest_export' ),
        'permission_callback' => function() { return current_user_can( 'manage_options' ); },
    ) );
} );
