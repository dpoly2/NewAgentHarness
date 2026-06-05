<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Square {

    private static function endpoint() {
        $env = get_option( 'pbs_square_env', 'sandbox' );
        return $env === 'production'
            ? 'https://connect.squareup.com/v2/payments'
            : 'https://connect.squareupsandbox.com/v2/payments';
    }

    /**
     * Charge via Square Payments API.
     * $data must include: amount, token (Square nonce from Web Payments SDK), name, email
     */
    public static function charge( $order_id, array $data ) {
        $access_token  = get_option( 'pbs_square_access_token', '' );
        $location_id   = get_option( 'pbs_square_location_id', '' );

        if ( ! $access_token || ! $location_id ) {
            return new WP_Error( 'config', 'Square is not configured.' );
        }

        $amount_cents = (int) round( $data['amount'] * 100 );
        $order        = PBS_DB::get_order( $order_id );
        $idempotency  = wp_generate_uuid4();

        $response = wp_remote_post( self::endpoint(), [
            'headers' => [
                'Authorization' => 'Bearer ' . $access_token,
                'Content-Type'  => 'application/json',
                'Square-Version' => '2024-01-18',
            ],
            'body' => json_encode( [
                'idempotency_key'  => $idempotency,
                'source_id'        => $data['token'],  // nonce from Web Payments SDK
                'amount_money'     => [
                    'amount'   => $amount_cents,
                    'currency' => 'USD',
                ],
                'location_id'      => $location_id,
                'note'             => sprintf( 'PBS Order %s — %s', $order['order_number'], $data['ticket_type'] ),
                'buyer_email_address' => $data['email'],
                'reference_id'     => (string) $order_id,
            ] ),
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) return $response;

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ! empty( $body['errors'] ) ) {
            $msg = $body['errors'][0]['detail'] ?? 'Square payment failed.';
            return new WP_Error( 'square', $msg );
        }

        $payment = $body['payment'] ?? [];
        if ( ( $payment['status'] ?? '' ) === 'COMPLETED' ) {
            return [ 'transaction_id' => $payment['id'] ];
        }

        return new WP_Error( 'square', 'Square payment status: ' . ( $payment['status'] ?? 'unknown' ) );
    }
}
