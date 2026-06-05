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
