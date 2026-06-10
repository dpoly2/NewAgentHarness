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
     * Ensure we have a valid, non-expired access token.
     * Auto-refreshes if the saved token is expired.
     * Returns the usable token string, or empty string on failure.
     */
    public static function get_valid_token(): string {
        $access_token = get_option( 'pbs_square_access_token', '' );
        if ( ! $access_token ) return '';

        $expires = get_option( 'pbs_square_token_expires', '' );
        if ( $expires && strtotime( $expires ) < time() ) {
            // Token expired — attempt refresh
            $refreshed = PBS_Square_OAuth::refresh_token();
            if ( ! is_wp_error( $refreshed ) ) {
                $access_token = $refreshed;
            } else {
                // Refresh failed — token is dead
                return '';
            }
        }

        return $access_token;
    }

    /**
     * Fetch first active location from Square and persist it.
     * Returns location_id string, or empty string on failure.
     */
    public static function fetch_location( string $access_token ): string {
        $env      = get_option( 'pbs_square_env', 'sandbox' );
        $base_url = ( $env === 'sandbox' )
            ? 'https://connect.squareupsandbox.com'
            : 'https://connect.squareup.com';

        $response = wp_remote_get( $base_url . '/v2/locations', [
            'headers' => [
                'Authorization'  => 'Bearer ' . $access_token,
                'Square-Version' => '2024-10-17',
                'Content-Type'   => 'application/json',
            ],
            'timeout' => 10,
        ] );

        if ( is_wp_error( $response ) ) return '';

        $body = json_decode( wp_remote_retrieve_body( $response ), true );
        $id   = $body['locations'][0]['id'] ?? '';

        if ( $id ) {
            update_option( 'pbs_square_location_id', $id );
        }

        return $id;
    }

    /**
     * Charge via Square Payments API.
     * $data must include: amount, token (Square nonce from Web Payments SDK), name, email
     */
    public static function charge( $order_id, array $data ) {
        // Get a valid (possibly auto-refreshed) token
        $access_token = self::get_valid_token();
        if ( ! $access_token ) {
            return new WP_Error( 'config', 'Square is not configured: access token is missing or expired. Reconnect Square under PBS Commerce → Settings.' );
        }

        // Auto-fetch location_id if it was never saved
        $location_id = get_option( 'pbs_square_location_id', '' );
        if ( ! $location_id ) {
            $location_id = self::fetch_location( $access_token );
        }
        if ( ! $location_id ) {
            return new WP_Error( 'config', 'Square is not configured: Location ID is missing. Visit PBS Commerce → Settings → Square to reconnect.' );
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
