<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_PayPal_Connect {
    public static function init() {
        add_action( 'wp_ajax_pbs_test_paypal', [ __CLASS__, 'ajax_test_connection' ] );
    }

    public static function ajax_test_connection() {
        check_ajax_referer( 'pbs_admin_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Unauthorized.' ], 403 );
        }

        $client_id = sanitize_text_field( wp_unslash( $_POST['client_id'] ?? '' ) );
        $secret    = sanitize_text_field( wp_unslash( $_POST['secret'] ?? '' ) );
        $mode      = sanitize_text_field( wp_unslash( $_POST['mode'] ?? get_option( 'pbs_paypal_mode', 'sandbox' ) ) );

        if ( empty( $client_id ) || empty( $secret ) ) {
            wp_send_json_error( [ 'message' => 'Enter both PayPal Client ID and Secret first.' ], 400 );
        }

        $token_response = wp_remote_post( self::base_url( $mode ) . '/v1/oauth2/token', [
            'headers' => [
                'Authorization' => 'Basic ' . base64_encode( $client_id . ':' . $secret ),
                'Content-Type'  => 'application/x-www-form-urlencoded',
                'Accept'        => 'application/json',
            ],
            'body'    => 'grant_type=client_credentials',
            'timeout' => 20,
        ] );

        if ( is_wp_error( $token_response ) ) {
            wp_send_json_error( [ 'message' => $token_response->get_error_message() ], 400 );
        }

        $token_body = json_decode( wp_remote_retrieve_body( $token_response ), true );
        if ( wp_remote_retrieve_response_code( $token_response ) >= 400 || empty( $token_body['access_token'] ) ) {
            $message = $token_body['error_description'] ?? $token_body['error'] ?? 'Unable to authenticate with PayPal.';
            wp_send_json_error( [ 'message' => $message ], 400 );
        }

        $userinfo_response = wp_remote_get( self::base_url( $mode ) . '/v1/identity/oauth2/userinfo?schema=paypalv1.1', [
            'headers' => [
                'Authorization' => 'Bearer ' . $token_body['access_token'],
                'Accept'        => 'application/json',
                'Content-Type'  => 'application/json',
            ],
            'timeout' => 20,
        ] );

        if ( is_wp_error( $userinfo_response ) ) {
            wp_send_json_error( [ 'message' => $userinfo_response->get_error_message() ], 400 );
        }

        $userinfo_body = json_decode( wp_remote_retrieve_body( $userinfo_response ), true );
        if ( wp_remote_retrieve_response_code( $userinfo_response ) >= 400 ) {
            $message = $userinfo_body['error_description'] ?? $userinfo_body['error'] ?? 'PayPal account verification failed.';
            wp_send_json_error( [ 'message' => $message ], 400 );
        }

        $email = $userinfo_body['emails'][0]['value'] ?? $userinfo_body['email'] ?? '';
        $name  = trim(
            ( $userinfo_body['name'] ?? '' )
            ?: implode( ' ', array_filter( [
                $userinfo_body['given_name'] ?? '',
                $userinfo_body['family_name'] ?? '',
            ] ) )
        );
        $payer_id = $userinfo_body['payer_id'] ?? $userinfo_body['user_id'] ?? '';

        update_option( 'pbs_paypal_merchant_email', $email );
        update_option( 'pbs_paypal_payer_id', $payer_id );

        wp_send_json_success( [
            'email'    => $email,
            'name'     => $name,
            'payer_id' => $payer_id,
            'message'  => 'PayPal credentials verified successfully.',
        ] );
    }

    private static function base_url( $mode ) {
        return 'live' === $mode ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com';
    }
}
