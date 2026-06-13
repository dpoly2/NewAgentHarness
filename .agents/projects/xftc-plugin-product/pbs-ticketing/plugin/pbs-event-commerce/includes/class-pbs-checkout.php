<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Checkout {

    public static function init() {
        add_action( 'wp_ajax_pbs_process_order',        [ __CLASS__, 'ajax_process_order' ] );
        add_action( 'wp_ajax_nopriv_pbs_process_order', [ __CLASS__, 'ajax_process_order' ] );
        add_action( 'wp_ajax_pbs_stripe_3ds_complete',        [ __CLASS__, 'ajax_stripe_3ds_complete' ] );
        add_action( 'wp_ajax_nopriv_pbs_stripe_3ds_complete', [ __CLASS__, 'ajax_stripe_3ds_complete' ] );
        add_action( 'wp_ajax_pbs_get_tickets',          [ __CLASS__, 'ajax_get_tickets' ] );
        add_action( 'wp_ajax_nopriv_pbs_get_tickets',   [ __CLASS__, 'ajax_get_tickets' ] );
    }

    /** AJAX: process_order */
    public static function ajax_process_order() {
        // Accept nonce from either JS-injected 'nonce' field OR form's 'pbs_nonce' field
        $nonce = $_POST['nonce'] ?? $_POST['pbs_nonce'] ?? '';
        if ( ! wp_verify_nonce( $nonce, 'pbs_ec_nonce' ) ) {
            wp_send_json_error( [ 'message' => 'Security check failed.' ] );
        }

        $data = self::sanitize_order_input( $_POST );
        if ( is_wp_error( $data ) ) {
            wp_send_json_error( [ 'message' => $data->get_error_message() ] );
        }

        // Insert pending order
        $order_id = PBS_DB::insert_order( [
            'event_id'       => $data['event_id'],
            'ticket_type'    => $data['ticket_type'],
            'quantity'       => $data['quantity'],
            'amount'         => $data['amount'],
            'attendee_name'  => $data['name'],
            'attendee_email' => $data['email'],
            'attendee_phone' => $data['phone'],
            'payment_method' => $data['gateway'],
            'status'         => 'pending',
        ] );

        if ( ! $order_id ) {
            wp_send_json_error( [ 'message' => 'Could not create order. Please try again.' ] );
        }

        // Route to gateway
        $result = false;
        switch ( $data['gateway'] ) {
            case 'stripe':
                $result = PBS_Stripe::charge( $order_id, $data );
                break;
            case 'square':
                $result = PBS_Square::charge( $order_id, $data );
                break;
            case 'paypal':
                // Store PBS order ID → PayPal order ID mapping before capture,
                // so the webhook handler can look up the PBS order by PayPal order ID.
                if ( ! empty( $data['paypal_order_id'] ) ) {
                    set_transient(
                        'pbs_paypal_order_map_' . sanitize_key( $data['paypal_order_id'] ),
                        $order_id,
                        DAY_IN_SECONDS
                    );
                }
                $result = PBS_PayPal::capture( $order_id, $data );
                break;
        }

        if ( is_wp_error( $result ) ) {
            // Bug 5 fix: Stripe 3DS — keep order pending, return client_secret to browser
            if ( $result->get_error_code() === 'stripe_3ds' ) {
                $parts         = explode( ':', $result->get_error_message(), 2 );
                $client_secret = $parts[1] ?? '';
                wp_send_json_success( [
                    'requires_action' => true,
                    'client_secret'   => $client_secret,
                    'order_id'        => $order_id,
                ] );
                return;
            }
            PBS_DB::update_order_status( $order_id, 'failed' );
            wp_send_json_error( [ 'message' => $result->get_error_message() ] );
        }

        // Mark complete
        PBS_DB::update_order_status( $order_id, 'complete', $result['transaction_id'] ?? '' );

        // Send confirmation email
        $order = PBS_DB::get_order( $order_id );
        PBS_Email::send_confirmation( $order );

        // Build confirmation URL — use pbs_oid/pbs_tok to avoid TEC order_id query var conflict.
        $token       = substr( wp_hash( $order['order_number'] ), 0, 12 );
        $confirm_url = add_query_arg( [
            'pbs_oid' => $order_id,
            'pbs_tok' => $token,
        ], get_permalink( get_option( 'pbs_confirmation_page_id', 0 ) ) ?: home_url( '/order-confirmation/' ) );

        wp_send_json_success( [
            'message'      => 'Payment successful!',
            'order_id'     => $order_id,
            'order_number' => $order['order_number'],
            'redirect'     => $confirm_url,
        ] );
    }

    /** AJAX: Stripe 3DS completion — confirm the PaymentIntent after browser auth */
    public static function ajax_stripe_3ds_complete() {
        $nonce = $_POST['nonce'] ?? '';
        if ( ! wp_verify_nonce( $nonce, 'pbs_ec_nonce' ) ) {
            wp_send_json_error( [ 'message' => 'Security check failed.' ] );
        }

        $order_id          = (int) ( $_POST['order_id'] ?? 0 );
        $payment_intent_id = sanitize_text_field( $_POST['payment_intent_id'] ?? '' );

        if ( ! $order_id || ! $payment_intent_id ) {
            wp_send_json_error( [ 'message' => 'Missing order or payment intent.' ] );
        }

        $order = PBS_DB::get_order( $order_id );
        if ( ! $order ) {
            wp_send_json_error( [ 'message' => 'Order not found.' ] );
        }

        // Verify the PaymentIntent status with Stripe
        $secret   = get_option( 'pbs_stripe_secret_key', '' );
        $response = wp_remote_get(
            'https://api.stripe.com/v1/payment_intents/' . $payment_intent_id,
            [ 'headers' => [ 'Authorization' => 'Bearer ' . $secret ], 'timeout' => 20 ]
        );

        if ( is_wp_error( $response ) ) {
            wp_send_json_error( [ 'message' => 'Could not verify payment. ' . $response->get_error_message() ] );
        }

        $pi = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ( $pi['status'] ?? '' ) !== 'succeeded' ) {
            PBS_DB::update_order_status( $order_id, 'failed' );
            wp_send_json_error( [ 'message' => '3D Secure authentication did not complete.' ] );
        }

        PBS_DB::update_order_status( $order_id, 'complete', $payment_intent_id );
        PBS_Email::send_confirmation( PBS_DB::get_order( $order_id ) );

        $token       = substr( wp_hash( $order['order_number'] ), 0, 12 );
        $confirm_url = add_query_arg( [
            'pbs_oid' => $order_id,
            'pbs_tok' => $token,
        ], get_permalink( get_option( 'pbs_confirmation_page_id', 0 ) ) ?: home_url( '/order-confirmation/' ) );

        wp_send_json_success( [
            'message'  => 'Payment successful!',
            'redirect' => $confirm_url,
        ] );
    }

    /** REST: get_event_tickets */
    public static function get_event_tickets( WP_REST_Request $request ) {
        $event_id = (int) $request['event_id'];
        $tickets  = PBS_DB::get_ticket_types( $event_id );
        return rest_ensure_response( $tickets );
    }

    /** REST wrapper for orders (admin) */
    public static function process_order( WP_REST_Request $request ) {
        return rest_ensure_response( [ 'status' => 'use ajax endpoint' ] );
    }

    private static function sanitize_order_input( $post ) {
        $event_id    = (int) ( $post['event_id'] ?? 0 );
        $ticket_type = sanitize_text_field( $post['ticket_type'] ?? '' );
        $quantity    = max( 1, (int) ( $post['quantity'] ?? 1 ) );
        $name        = sanitize_text_field( $post['name'] ?? '' );
        $email       = sanitize_email( $post['email'] ?? '' );
        $phone       = sanitize_text_field( $post['phone'] ?? '' );
        $gateway     = sanitize_key( $post['gateway'] ?? '' );
        $token           = sanitize_text_field( $post['payment_token'] ?? '' );
        $paypal_order_id = sanitize_text_field( $post['paypal_order_id'] ?? '' );

        if ( ! $event_id )             return new WP_Error( 'missing', 'Event not specified.' );
        if ( ! $name )                 return new WP_Error( 'missing', 'Name is required.' );
        if ( ! is_email( $email ) )    return new WP_Error( 'missing', 'Valid email required.' );
        if ( ! in_array( $gateway, [ 'stripe', 'square', 'paypal' ] ) ) {
            return new WP_Error( 'missing', 'Invalid payment method.' );
        }

        // Server-side amount calculation — spec §19: order total never trusted from client.
        $is_donation = ! empty( $post['is_donation'] );

        if ( $is_donation ) {
            // Donation widget — amount is user-chosen, enforce minimum $1.00
            $amount = round( (float) ( $post['amount'] ?? 0 ), 2 );
            if ( $amount < 1.00 ) {
                return new WP_Error( 'amount', 'Minimum donation is $1.00.' );
            }
            $ticket_type = 'Donation';
        } else {
            $ticket = $ticket_type ? PBS_DB::get_ticket_type_by_name( $event_id, $ticket_type ) : null;

            if ( $ticket ) {
                if ( (int) $ticket['is_donation'] ) {
                    // Donation ticket type from the ticket widget
                    $amount = (float) ( $post['amount'] ?? 0 );
                    if ( $amount < 1.00 ) {
                        return new WP_Error( 'amount', 'Minimum donation is $1.00.' );
                    }
                } else {
                    // Fixed-price ticket: calculate from DB price, ignore client value
                    $amount = round( (float) $ticket['price'] * $quantity, 2 );
                }
            } elseif ( $ticket_type !== '' ) {
                // Multi-ticket order: resolve via individual qty_{id} POST fields.
                $multi_amount = 0.0;
                $multi_names  = [];
                $multi_qty    = 0;
                foreach ( $post as $key => $val ) {
                    if ( 0 !== strpos( $key, 'qty_' ) ) continue;
                    $tid = (int) substr( $key, 4 );
                    $qty = max( 0, (int) $val );
                    if ( ! $tid || ! $qty ) continue;
                    $tt = PBS_DB::get_ticket_type( $tid );
                    if ( ! $tt || (int) $tt['event_id'] !== $event_id || ! (int) $tt['active'] ) continue;
                    $multi_names[] = $tt['name'];
                    $multi_qty    += $qty;
                    if ( (int) $tt['is_donation'] ) {
                        $multi_amount += max( 1.0, (float) ( $post['amount'] ?? 0 ) );
                    } else {
                        $multi_amount += round( (float) $tt['price'] * $qty, 2 );
                    }
                }
                if ( empty( $multi_names ) ) {
                    return new WP_Error( 'amount', 'Ticket type not found or not available.' );
                }
                $ticket_type = implode( ', ', $multi_names );
                $quantity    = $multi_qty ?: $quantity;
                $amount      = round( $multi_amount, 2 );
            } else {
                // No ticket_type sent — only allow $0 free orders
                $client_amount = (float) ( $post['amount'] ?? 0 );
                if ( $client_amount > 0 ) {
                    return new WP_Error( 'amount', 'Cannot process a paid order without a valid ticket type.' );
                }
                $amount = 0.00;
            }
        }

        return compact( 'event_id', 'ticket_type', 'quantity', 'amount', 'name', 'email', 'phone', 'gateway', 'token', 'paypal_order_id' );
    }
}
