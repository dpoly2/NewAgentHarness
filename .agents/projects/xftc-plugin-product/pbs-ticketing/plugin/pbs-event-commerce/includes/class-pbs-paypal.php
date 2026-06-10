<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_PayPal {

    private static function base_url() {
        $mode = get_option( 'pbs_paypal_mode', 'sandbox' );
        return $mode === 'live'
            ? 'https://api-m.paypal.com'
            : 'https://api-m.sandbox.paypal.com';
    }

    private static function get_access_token() {
        $client_id = get_option( 'pbs_paypal_client_id', '' );
        $secret    = get_option( 'pbs_paypal_secret', '' );
        if ( ! $client_id || ! $secret ) return false;

        $response = wp_remote_post( self::base_url() . '/v1/oauth2/token', [
            'headers' => [
                'Authorization' => 'Basic ' . base64_encode( "$client_id:$secret" ),
                'Content-Type'  => 'application/x-www-form-urlencoded',
            ],
            'body'    => 'grant_type=client_credentials',
            'timeout' => 20,
        ] );

        $body = json_decode( wp_remote_retrieve_body( $response ), true );
        return $body['access_token'] ?? false;
    }

    /**
     * Create a PayPal order server-side (spec §13 Three-Party SDK Flow).
     * Returns the PayPal order ID to be passed to the JS SDK.
     *
     * @param int   $event_id
     * @param array $data  Keys: ticket_type, quantity, amount, currency (optional)
     * @return array|WP_Error  ['paypal_order_id' => '...'] on success.
     */
    public static function create_order( int $event_id, array $data ) {
        $access_token = self::get_access_token();
        if ( ! $access_token ) {
            return new WP_Error( 'config', 'PayPal is not configured.' );
        }

        $amount   = round( (float) ( $data['amount'] ?? 0 ), 2 );
        $currency = strtoupper( $data['currency'] ?? 'USD' );

        if ( $amount <= 0 ) {
            return new WP_Error( 'amount', 'Invalid order amount.' );
        }

        // The PBS order is created later (at checkout submit) so we cannot embed
        // the PBS order ID in custom_id yet. We use a short-lived transient keyed
        // by the PayPal order ID — the checkout AJAX sets it once the PBS order
        // is created, and the webhook reads it.
        $response = wp_remote_post( self::base_url() . '/v2/checkout/orders', [
            'headers' => [
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type'  => 'application/json',
            ],
            'body'    => wp_json_encode( [
                'intent'         => 'CAPTURE',
                'purchase_units' => [
                    [
                        'amount'      => [
                            'currency_code' => $currency,
                            'value'         => number_format( $amount, 2, '.', '' ),
                        ],
                        'description' => sprintf(
                            'Event %d — %s x%d',
                            $event_id,
                            sanitize_text_field( $data['ticket_type'] ?? 'Ticket' ),
                            max( 1, (int) ( $data['quantity'] ?? 1 ) )
                        ),
                    ],
                ],
            ] ),
            'timeout' => 20,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( wp_remote_retrieve_response_code( $response ) >= 400 ) {
            $msg = $body['message'] ?? ( $body['details'][0]['description'] ?? 'PayPal order creation failed.' );
            return new WP_Error( 'paypal_create', $msg );
        }

        return [ 'paypal_order_id' => $body['id'] ];
    }

    /**
     * Issue a refund against a captured PayPal payment.
     *
     * @param string     $capture_id  PayPal capture ID (from purchase_units.payments.captures[0].id).
     * @param float|null $amount      Dollars to refund. Null = full refund.
     * @return array|WP_Error  ['refund_id' => '...'] on success.
     */
    public static function refund( string $capture_id, float $amount = null ) {
        $access_token = self::get_access_token();
        if ( ! $access_token ) {
            return new WP_Error( 'config', 'PayPal is not configured.' );
        }

        if ( empty( $capture_id ) ) {
            return new WP_Error( 'missing', 'Capture ID is required for PayPal refund.' );
        }

        $body = new stdClass();
        if ( null !== $amount ) {
            $body->amount = [
                'value'         => number_format( $amount, 2, '.', '' ),
                'currency_code' => 'USD',
            ];
        }

        $response = wp_remote_post(
            self::base_url() . "/v2/payments/captures/{$capture_id}/refund",
            [
                'headers' => [
                    'Authorization' => 'Bearer ' . $access_token,
                    'Content-Type'  => 'application/json',
                ],
                'body'    => wp_json_encode( $body ),
                'timeout' => 30,
            ]
        );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $data = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( wp_remote_retrieve_response_code( $response ) >= 400 ) {
            $msg = $data['message'] ?? ( $data['details'][0]['description'] ?? 'PayPal refund failed.' );
            return new WP_Error( 'paypal_refund', $msg );
        }

        if ( in_array( $data['status'] ?? '', [ 'COMPLETED', 'PENDING' ] ) ) {
            return [ 'refund_id' => $data['id'] ];
        }

        return new WP_Error( 'paypal_refund', 'Unexpected PayPal refund status: ' . ( $data['status'] ?? 'unknown' ) );
    }

    /**
     * Capture a PayPal order that was approved client-side.
     * $data must include: paypal_order_id (from JS SDK onApprove callback)
     */
    public static function capture( $order_id, array $data ) {
        $access_token = self::get_access_token();
        if ( ! $access_token ) return new WP_Error( 'config', 'PayPal is not configured.' );

        $paypal_order_id = sanitize_text_field( $data['paypal_order_id'] ?? '' );
        if ( ! $paypal_order_id ) return new WP_Error( 'missing', 'PayPal order ID missing.' );

        $response = wp_remote_post(
            self::base_url() . "/v2/checkout/orders/{$paypal_order_id}/capture",
            [
                'headers' => [
                    'Authorization' => 'Bearer ' . $access_token,
                    'Content-Type'  => 'application/json',
                ],
                'body'    => '{}',
                'timeout' => 30,
            ]
        );

        if ( is_wp_error( $response ) ) return $response;

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ( $body['status'] ?? '' ) === 'COMPLETED' ) {
            $capture_id = $body['purchase_units'][0]['payments']['captures'][0]['id'] ?? $paypal_order_id;
            return [ 'transaction_id' => $capture_id ];
        }

        return new WP_Error( 'paypal', 'PayPal capture failed. Status: ' . ( $body['status'] ?? 'unknown' ) );
    }
}
