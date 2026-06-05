<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Stripe {

    private static function secret_key() {
        return get_option( 'pbs_stripe_secret_key', '' );
    }

    /**
     * Create a PaymentIntent and confirm it with the client-side token.
     * $data must include: amount (dollars), token (Stripe PaymentMethod ID), name, email
     */
    public static function charge( $order_id, array $data ) {
        $secret = self::secret_key();
        if ( ! $secret ) return new WP_Error( 'config', 'Stripe is not configured.' );

        $amount_cents = (int) round( $data['amount'] * 100 );
        $order        = PBS_DB::get_order( $order_id );

        // Create PaymentIntent
        $response = wp_remote_post( 'https://api.stripe.com/v1/payment_intents', [
            'headers' => [
                'Authorization' => 'Bearer ' . $secret,
                'Content-Type'  => 'application/x-www-form-urlencoded',
            ],
            'body' => http_build_query( [
                'amount'               => $amount_cents,
                'currency'             => 'usd',
                'payment_method'       => $data['token'],
                'confirm'              => 'true',
                'description'          => sprintf( 'PBS Order %s — %s', $order['order_number'], $data['ticket_type'] ),
                'receipt_email'        => $data['email'],
                'return_url'           => home_url( '/order-confirmation/' ),
                'metadata[order_id]'   => $order_id,
                'metadata[order_num]'  => $order['order_number'],
                'metadata[event_id]'   => $data['event_id'],
            ] ),
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) return $response;

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ! empty( $body['error'] ) ) {
            return new WP_Error( 'stripe', $body['error']['message'] ?? 'Stripe payment failed.' );
        }

        if ( in_array( $body['status'] ?? '', [ 'succeeded', 'requires_capture' ] ) ) {
            return [ 'transaction_id' => $body['id'] ];
        }

        // Needs further action (3DS) — return client secret for frontend to handle
        if ( ( $body['status'] ?? '' ) === 'requires_action' ) {
            return new WP_Error( 'stripe_3ds', 'requires_action:' . $body['client_secret'] );
        }

        return new WP_Error( 'stripe', 'Payment could not be processed. Status: ' . ( $body['status'] ?? 'unknown' ) );
    }
}
