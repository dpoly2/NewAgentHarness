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
    /**
     * Issue a partial or full refund for a Stripe PaymentIntent or Charge.
     *
     * @param string $payment_id  Stripe payment_intent ID or charge ID.
     * @param float  $amount      Amount to refund in dollars. Null = full refund.
     * @return array|WP_Error  ['refund_id' => '...'] on success.
     */
    public static function refund( string $payment_id, float $amount = null ) {
        $secret = self::secret_key();
        if ( ! $secret ) {
            return new WP_Error( 'config', 'Stripe is not configured.' );
        }

        if ( empty( $payment_id ) ) {
            return new WP_Error( 'missing', 'Payment ID is required for refund.' );
        }

        $body = [];

        // Stripe refunds accept either a charge or payment_intent ID.
        // Use strpos for PHP 7.4 compatibility (str_starts_with requires PHP 8.0+).
        if ( 0 === strpos( $payment_id, 'pi_' ) ) {
            $body['payment_intent'] = $payment_id;
        } else {
            $body['charge'] = $payment_id;
        }

        if ( null !== $amount ) {
            $body['amount'] = (int) round( $amount * 100 );
        }

        $response = wp_remote_post( 'https://api.stripe.com/v1/refunds', [
            'headers' => [
                'Authorization' => 'Bearer ' . $secret,
                'Content-Type'  => 'application/x-www-form-urlencoded',
            ],
            'body'    => http_build_query( $body ),
            'timeout' => 30,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $data = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ! empty( $data['error'] ) ) {
            return new WP_Error( 'stripe_refund', $data['error']['message'] ?? 'Stripe refund failed.' );
        }

        if ( in_array( $data['status'] ?? '', [ 'succeeded', 'pending' ] ) ) {
            return [ 'refund_id' => $data['id'] ];
        }

        return new WP_Error( 'stripe_refund', 'Unexpected Stripe refund status: ' . ( $data['status'] ?? 'unknown' ) );
    }

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
                'return_url'           => add_query_arg( [
                    'pbs_oid' => $order_id,
                    'pbs_tok' => substr( wp_hash( $order['order_number'] ), 0, 12 ),
                ], get_permalink( get_option( 'pbs_confirmation_page_id', 0 ) ) ?: home_url( '/order-confirmation/' ) ),
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
