<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Shortcodes {

    public static function init() {
        add_shortcode( 'pbs_tickets',       [ __CLASS__, 'ticket_widget' ] );
        add_shortcode( 'pbs_donate',        [ __CLASS__, 'donate_widget' ] );
        add_shortcode( 'pbs_order_summary', [ __CLASS__, 'order_summary' ] );
        add_shortcode( 'pbs_attendee_list', [ __CLASS__, 'attendee_list' ] );
    }

    /** [pbs_tickets event_id="107" show_title="1"] */
    public static function ticket_widget( $atts ) {
        $atts = shortcode_atts( [
            'event_id'   => 0,
            'show_title' => 1,
        ], $atts, 'pbs_tickets' );

        $event_id = (int) $atts['event_id'];
        if ( ! $event_id ) return '';

        $tickets  = PBS_DB::get_ticket_types( $event_id );
        $event    = get_post( $event_id );
        $gateways = self::active_gateways();

        ob_start();
        include PBS_EC_PATH . 'templates/ticket-widget.php';
        return ob_get_clean();
    }

    /** [pbs_donate event_id="222" goal="5000" label="Supply Drive"] */
    public static function donate_widget( $atts ) {
        $atts = shortcode_atts( [
            'event_id' => 0,
            'goal'     => 0,
            'label'    => 'Donate',
            'amounts'  => '10,25,50,100',
        ], $atts, 'pbs_donate' );

        $event_id = (int) $atts['event_id'];
        $goal     = (float) $atts['goal'];
        $amounts  = array_map( 'trim', explode( ',', $atts['amounts'] ) );

        // Donations use a single configured gateway (default: stripe)
        $all_gateways      = self::active_gateways();
        $donation_gateway  = get_option( 'pbs_donation_gateway', 'stripe' );
        // Only show the configured donation gateway if it is active, else fall back to all active
        $gateways = in_array( $donation_gateway, $all_gateways, true )
            ? [ $donation_gateway ]
            : $all_gateways;

        // Calculate total donated so far
        global $wpdb;
        $total_donated = (float) $wpdb->get_var(
            $wpdb->prepare(
                "SELECT SUM(amount) FROM {$wpdb->prefix}pbs_orders WHERE event_id = %d AND status = 'complete'",
                $event_id
            )
        );

        ob_start();
        include PBS_EC_PATH . 'templates/donate-widget.php';
        return ob_get_clean();
    }

    /** [pbs_order_summary] — shown on confirmation page */
    public static function order_summary( $atts ) {
        // Use pbs_oid / pbs_tok to avoid conflicts with TEC's own order_id query var.
        $order_id = isset( $_GET['pbs_oid'] ) ? (int) $_GET['pbs_oid'] : 0;
        $token    = isset( $_GET['pbs_tok'] ) ? sanitize_text_field( $_GET['pbs_tok'] ) : '';

        if ( ! $order_id ) return '<p>No order found.</p>';

        $order = PBS_DB::get_order( $order_id );
        if ( ! $order ) return '<p>Order not found.</p>';

        // Verify token — wp_hash uses AUTH_KEY from wp-config, immune to HTTP/HTTPS URL differences
        $expected = substr( wp_hash( $order['order_number'] ), 0, 12 );
        if ( $token !== $expected ) return '<p>Invalid order link.</p>';

        ob_start();
        include PBS_EC_PATH . 'templates/confirmation.php';
        return ob_get_clean();
    }

    /** [pbs_attendee_list event_id="107"] — admin/password-gated */
    public static function attendee_list( $atts ) {
        if ( ! current_user_can( 'manage_options' ) ) {
            return '<p>You do not have permission to view this list.</p>';
        }
        $atts     = shortcode_atts( [ 'event_id' => 0 ], $atts );
        $event_id = (int) $atts['event_id'];
        $orders   = PBS_DB::get_orders( [ 'event_id' => $event_id, 'status' => 'complete' ] );

        ob_start();
        include PBS_EC_PATH . 'admin/views/attendees.php';
        return ob_get_clean();
    }

    private static function active_gateways() {
        $gateways = [];
        if ( get_option( 'pbs_stripe_publishable_key' ) && get_option( 'pbs_stripe_secret_key' ) ) {
            $gateways[] = 'stripe';
        }
        if ( get_option( 'pbs_square_app_id' ) && get_option( 'pbs_square_access_token' ) ) {
            $gateways[] = 'square';
        }
        if ( get_option( 'pbs_paypal_client_id' ) ) {
            $gateways[] = 'paypal';
        }
        return $gateways;
    }
}
