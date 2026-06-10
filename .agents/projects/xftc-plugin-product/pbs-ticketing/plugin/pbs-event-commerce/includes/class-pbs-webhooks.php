<?php
/**
 * PBS Webhooks — spec §8: Webhook Architecture
 *
 * Registers REST endpoints for Stripe, Square, and PayPal webhooks.
 * All endpoints verify payload signatures before processing.
 * Routes are registered at:
 *   POST /pbs-ec/v1/webhooks/stripe
 *   POST /pbs-ec/v1/webhooks/square
 *   POST /pbs-ec/v1/webhooks/paypal
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Webhooks {

    // ─────────────────────────────────────────────────────────────────────────
    // Registration
    // ─────────────────────────────────────────────────────────────────────────

    public static function register_routes(): void {
        register_rest_route( 'pbs-ec/v1', '/webhooks/stripe', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_stripe' ],
            'permission_callback' => '__return_true', // Auth via signature
        ] );

        register_rest_route( 'pbs-ec/v1', '/webhooks/square', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_square' ],
            'permission_callback' => '__return_true',
        ] );

        register_rest_route( 'pbs-ec/v1', '/webhooks/paypal', [
            'methods'             => WP_REST_Server::CREATABLE,
            'callback'            => [ __CLASS__, 'handle_paypal' ],
            'permission_callback' => '__return_true',
        ] );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Stripe webhook handler
    // Spec §8.2: verify X-Stripe-Signature header with HMAC-SHA256
    // ─────────────────────────────────────────────────────────────────────────

    public static function handle_stripe( WP_REST_Request $request ): WP_REST_Response {
        $signing_secret = get_option( 'pbs_stripe_webhook_secret', '' );
        $payload        = $request->get_body();
        $sig_header     = $request->get_header( 'x-stripe-signature' );

        // Fail closed: if no secret configured, reject all requests.
        if ( ! $signing_secret ) {
            return new WP_REST_Response( [ 'error' => 'Stripe webhook secret not configured.' ], 401 );
        }

        if ( ! self::verify_stripe_signature( $payload, $sig_header, $signing_secret ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid Stripe signature.' ], 401 );
        }

        $event = json_decode( $payload, true );
        if ( empty( $event['type'] ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid event payload.' ], 400 );
        }

        return self::process_stripe_event( $event );
    }

    /**
     * Verify Stripe webhook signature (Stripe's "v1" scheme).
     * Spec §8.2 / Stripe docs: https://stripe.com/docs/webhooks/signatures
     */
    private static function verify_stripe_signature( string $payload, ?string $header, string $secret ): bool {
        if ( empty( $header ) ) return false;

        // Header format: t=timestamp,v1=signature1,v1=signature2,...
        $parts = [];
        foreach ( explode( ',', $header ) as $part ) {
            [ $k, $v ] = explode( '=', $part, 2 ) + [ '', '' ];
            $parts[ $k ][] = $v;
        }

        $timestamp  = $parts['t'][0] ?? '';
        $signatures = $parts['v1'] ?? [];

        if ( ! $timestamp || ! $signatures ) return false;

        // Reject events older than 5 minutes (replay protection)
        if ( abs( time() - (int) $timestamp ) > 300 ) return false;

        $signed_payload = $timestamp . '.' . $payload;
        $expected       = hash_hmac( 'sha256', $signed_payload, $secret );

        foreach ( $signatures as $sig ) {
            if ( hash_equals( $expected, $sig ) ) return true;
        }

        return false;
    }

    private static function process_stripe_event( array $event ): WP_REST_Response {
        $type   = $event['type'];
        $object = $event['data']['object'] ?? [];

        switch ( $type ) {
            case 'payment_intent.succeeded':
                $order_id = self::find_order_by_payment_id( $object['id'] ?? '' );
                if ( $order_id ) {
                    $order = PBS_DB::get_order( $order_id );
                    // Idempotency: only advance to 'complete' from a non-terminal state
                    if ( $order && in_array( $order['status'], [ 'pending', 'processing' ], true ) ) {
                        PBS_DB::update_order_status( $order_id, 'complete', $object['id'] );
                        do_action( 'pbs_stripe_payment_succeeded', $order_id, $object );
                    }
                }
                break;

            case 'payment_intent.payment_failed':
                $order_id = self::find_order_by_payment_id( $object['id'] ?? '' );
                if ( $order_id ) {
                    $order = PBS_DB::get_order( $order_id );
                    if ( $order && $order['status'] === 'pending' ) {
                        PBS_DB::update_order_status( $order_id, 'failed' );
                        do_action( 'pbs_stripe_payment_failed', $order_id, $object );
                    }
                }
                break;

            case 'charge.refunded':
                $pi_id    = $object['payment_intent'] ?? '';
                $order_id = self::find_order_by_payment_id( $pi_id );
                if ( $order_id ) {
                    $order = PBS_DB::get_order( $order_id );
                    if ( $order && $order['status'] === 'complete' ) {
                        $new_status = $object['amount_refunded'] >= $object['amount'] ? 'refunded' : 'partial_refund';
                        PBS_DB::update_order_status( $order_id, $new_status );
                    }
                }
                break;

            default:
                return new WP_REST_Response( [ 'status' => 'ignored', 'type' => $type ], 200 );
        }

        return new WP_REST_Response( [ 'status' => 'ok', 'type' => $type ], 200 );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Square webhook handler
    // Spec §8.2: verify X-Square-Hmacsha256-Signature header
    // ─────────────────────────────────────────────────────────────────────────

    public static function handle_square( WP_REST_Request $request ): WP_REST_Response {
        $signing_key = get_option( 'pbs_square_webhook_signature_key', '' );
        $payload     = $request->get_body();
        $sig_header  = $request->get_header( 'x-square-hmacsha256-signature' );

        // Fail closed: if no key configured, reject all requests.
        if ( ! $signing_key ) {
            return new WP_REST_Response( [ 'error' => 'Square webhook signature key not configured.' ], 401 );
        }

        if ( ! self::verify_square_signature( $payload, $sig_header, $signing_key, $request->get_route() ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid Square signature.' ], 401 );
        }

        $event = json_decode( $payload, true );
        if ( empty( $event['type'] ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid event payload.' ], 400 );
        }

        return self::process_square_event( $event );
    }

    /**
     * Verify Square webhook HMAC-SHA256 signature.
     * Square signs: webhook_notification_url + request_body
     */
    private static function verify_square_signature( string $payload, ?string $header, string $key, string $route ): bool {
        if ( empty( $header ) ) return false;

        $notification_url = rest_url( 'pbs-ec/v1/webhooks/square' );
        $signed_payload   = $notification_url . $payload;
        $expected         = base64_encode( hash_hmac( 'sha256', $signed_payload, $key, true ) );

        return hash_equals( $expected, $header );
    }

    private static function process_square_event( array $event ): WP_REST_Response {
        $type   = $event['type'];
        $object = $event['data']['object']['payment'] ?? [];

        switch ( $type ) {
            case 'payment.completed':
                $ref_id   = $object['reference_id'] ?? '';
                $order_id = (int) $ref_id;
                if ( $order_id && PBS_DB::get_order( $order_id ) ) {
                    PBS_DB::update_order_status( $order_id, 'complete', $object['id'] ?? '' );
                    do_action( 'pbs_square_payment_completed', $order_id, $object );
                }
                break;

            case 'payment.failed':
                $ref_id   = $object['reference_id'] ?? '';
                $order_id = (int) $ref_id;
                if ( $order_id ) {
                    PBS_DB::update_order_status( $order_id, 'failed' );
                    do_action( 'pbs_square_payment_failed', $order_id, $object );
                }
                break;

            case 'refund.completed':
                $payment_obj = $event['data']['object']['refund']['payment_id'] ?? '';
                $order_id    = self::find_order_by_payment_id( $payment_obj );
                if ( $order_id ) {
                    PBS_DB::update_order_status( $order_id, 'refunded' );
                }
                break;

            default:
                return new WP_REST_Response( [ 'status' => 'ignored', 'type' => $type ], 200 );
        }

        return new WP_REST_Response( [ 'status' => 'ok', 'type' => $type ], 200 );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // PayPal webhook handler
    // Spec §8: verify via PayPal's webhook verification API
    // ─────────────────────────────────────────────────────────────────────────

    public static function handle_paypal( WP_REST_Request $request ): WP_REST_Response {
        $payload = $request->get_body();

        if ( ! self::verify_paypal_signature( $request ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid PayPal signature.' ], 401 );
        }

        $event = json_decode( $payload, true );
        if ( empty( $event['event_type'] ) ) {
            return new WP_REST_Response( [ 'error' => 'Invalid event payload.' ], 400 );
        }

        return self::process_paypal_event( $event );
    }

    /**
     * Verify PayPal webhook signature using PayPal's verification API.
     * See: https://developer.paypal.com/api/webhooks/#link-verifywebhooksignature
     */
    private static function verify_paypal_signature( WP_REST_Request $request ): bool {
        $webhook_id = get_option( 'pbs_paypal_webhook_id', '' );
        if ( ! $webhook_id ) {
            // Fail closed: webhook ID must be configured to verify signatures.
            error_log( 'PBS_Webhooks: pbs_paypal_webhook_id not configured — rejecting webhook.' );
            return false;
        }

        $client_id = get_option( 'pbs_paypal_client_id', '' );
        $secret    = get_option( 'pbs_paypal_secret', '' );
        if ( ! $client_id || ! $secret ) return false;

        // Get access token
        $mode         = get_option( 'pbs_paypal_mode', 'sandbox' );
        $base_url     = ( 'live' === $mode ) ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com';
        $token_res    = wp_remote_post( $base_url . '/v1/oauth2/token', [
            'headers' => [
                'Authorization' => 'Basic ' . base64_encode( $client_id . ':' . $secret ),
                'Content-Type'  => 'application/x-www-form-urlencoded',
            ],
            'body'    => 'grant_type=client_credentials',
            'timeout' => 10,
        ] );

        if ( is_wp_error( $token_res ) ) return false;
        $token_body   = json_decode( wp_remote_retrieve_body( $token_res ), true );
        $access_token = $token_body['access_token'] ?? '';
        if ( ! $access_token ) return false;

        $verify_body = [
            'auth_algo'         => $request->get_header( 'paypal-auth-algo' ),
            'cert_url'          => $request->get_header( 'paypal-cert-url' ),
            'transmission_id'   => $request->get_header( 'paypal-transmission-id' ),
            'transmission_sig'  => $request->get_header( 'paypal-transmission-sig' ),
            'transmission_time' => $request->get_header( 'paypal-transmission-time' ),
            'webhook_id'        => $webhook_id,
            'webhook_event'     => json_decode( $request->get_body(), true ),
        ];

        $verify_res = wp_remote_post( $base_url . '/v1/notifications/verify-webhook-signature', [
            'headers' => [
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type'  => 'application/json',
            ],
            'body'    => wp_json_encode( $verify_body ),
            'timeout' => 10,
        ] );

        if ( is_wp_error( $verify_res ) ) return false;

        $result = json_decode( wp_remote_retrieve_body( $verify_res ), true );
        return ( $result['verification_status'] ?? '' ) === 'SUCCESS';
    }

    private static function process_paypal_event( array $event ): WP_REST_Response {
        $type     = $event['event_type'];
        $resource = $event['resource'] ?? [];

        // Resolve PBS order ID: try custom_id first, then transient map by PayPal order ID.
        $paypal_order_id = $resource['supplementary_data']['related_ids']['order_id']
            ?? $resource['id']
            ?? '';
        $custom_id = $resource['custom_id'] ?? '';

        switch ( $type ) {
            case 'PAYMENT.CAPTURE.COMPLETED':
                $order_id = $custom_id
                    ? (int) $custom_id
                    : (int) get_transient( 'pbs_paypal_order_map_' . sanitize_key( $paypal_order_id ) );
                if ( $order_id && PBS_DB::get_order( $order_id ) ) {
                    PBS_DB::update_order_status( $order_id, 'complete', $resource['id'] ?? '' );
                    do_action( 'pbs_paypal_capture_completed', $order_id, $resource );
                }
                break;

            case 'PAYMENT.CAPTURE.DENIED':
            case 'PAYMENT.CAPTURE.DECLINED':
                $order_id = $custom_id
                    ? (int) $custom_id
                    : (int) get_transient( 'pbs_paypal_order_map_' . sanitize_key( $paypal_order_id ) );
                if ( $order_id ) {
                    PBS_DB::update_order_status( $order_id, 'failed' );
                    do_action( 'pbs_paypal_capture_failed', $order_id, $resource );
                }
                break;

            case 'PAYMENT.CAPTURE.REFUNDED':
                $order_id = $custom_id
                    ? (int) $custom_id
                    : (int) get_transient( 'pbs_paypal_order_map_' . sanitize_key( $paypal_order_id ) );
                if ( $order_id ) {
                    PBS_DB::update_order_status( $order_id, 'refunded' );
                }
                break;

            default:
                return new WP_REST_Response( [ 'status' => 'ignored', 'type' => $type ], 200 );
        }

        return new WP_REST_Response( [ 'status' => 'ok', 'type' => $type ], 200 );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Shared helper
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Look up an order by payment_id (transaction_id stored in pbs_orders.payment_id).
     */
    private static function find_order_by_payment_id( string $payment_id ): int {
        if ( ! $payment_id ) return 0;
        global $wpdb;
        $id = $wpdb->get_var( $wpdb->prepare(
            "SELECT id FROM {$wpdb->prefix}pbs_orders WHERE payment_id = %s LIMIT 1",
            $payment_id
        ) );
        return (int) $id;
    }
}
