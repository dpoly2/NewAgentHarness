<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Stripe_OAuth {
    const TOKEN_URL   = 'https://connect.stripe.com/oauth/token';
    const AUTH_URL    = 'https://connect.stripe.com/oauth/authorize';
    const DEAUTH_URL  = 'https://connect.stripe.com/oauth/deauthorize';
    const ACCOUNT_URL = 'https://api.stripe.com/v1/account';

    public static function init() {
        add_action( 'admin_init', [ __CLASS__, 'handle_callback' ] );
        add_action( 'admin_post_pbs_stripe_disconnect', [ __CLASS__, 'handle_disconnect' ] );
        add_action( 'wp_ajax_pbs_validate_stripe_keys', [ __CLASS__, 'ajax_validate_keys' ] );
    }

    public static function get_auth_url() {
        $client_id = get_option( 'pbs_stripe_connect_client_id', '' );
        $state     = self::get_or_create_state();

        return add_query_arg( [
            'response_type' => 'code',
            'client_id'     => $client_id,
            'scope'         => 'read_write',
            'redirect_uri'  => self::get_redirect_uri(),
            'state'         => $state,
        ], self::AUTH_URL );
    }

    public static function get_redirect_uri() {
        return admin_url( 'admin.php?page=pbs-commerce-settings&stripe_oauth_callback=1' );
    }

    private static function get_or_create_state() {
        $state = get_transient( 'pbs_stripe_oauth_state' );

        if ( ! $state ) {
            $state = wp_generate_password( 32, false );
            set_transient( 'pbs_stripe_oauth_state', $state, 10 * MINUTE_IN_SECONDS );
        }

        return $state;
    }

    public static function handle_callback() {
        if ( ! isset( $_GET['stripe_oauth_callback'] ) ) {
            return;
        }

        if ( ! isset( $_GET['page'] ) || 'pbs-commerce-settings' !== $_GET['page'] ) {
            return;
        }

        if ( ! current_user_can( 'manage_options' ) ) {
            return;
        }

        if ( isset( $_GET['error'] ) ) {
            $message = sanitize_text_field( wp_unslash( $_GET['error_description'] ?? 'Authorization denied.' ) );
            set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'error', 'message' => 'Stripe OAuth error: ' . $message ], 60 );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
            exit;
        }

        $saved_state = get_transient( 'pbs_stripe_oauth_state' );
        $given_state = sanitize_text_field( wp_unslash( $_GET['state'] ?? '' ) );

        if ( empty( $saved_state ) || ! hash_equals( $saved_state, $given_state ) ) {
            set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'error', 'message' => 'OAuth state mismatch. Please try connecting Stripe again.' ], 60 );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
            exit;
        }

        delete_transient( 'pbs_stripe_oauth_state' );

        $code = sanitize_text_field( wp_unslash( $_GET['code'] ?? '' ) );
        if ( empty( $code ) ) {
            set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'error', 'message' => 'No authorization code received from Stripe.' ], 60 );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
            exit;
        }

        $result = self::exchange_code_for_token( $code );

        if ( is_wp_error( $result ) ) {
            set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'error', 'message' => 'Stripe connection failed: ' . $result->get_error_message() ], 60 );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
            exit;
        }

        update_option( 'pbs_stripe_secret_key', $result['access_token'] );
        update_option( 'pbs_stripe_publishable_key', $result['stripe_publishable_key'] ?? '' );
        update_option( 'pbs_stripe_user_id', $result['stripe_user_id'] ?? '' );
        update_option( 'pbs_stripe_enabled', 1 );

        $mode = 'test';
        if ( 0 === strpos( $result['access_token'], 'sk_live_' ) ) {
            $mode = 'live';
        } elseif ( 0 === strpos( $result['access_token'], 'sk_test_' ) ) {
            $mode = 'test';
        }
        update_option( 'pbs_stripe_mode', $mode );

        delete_transient( 'pbs_stripe_connection_status' );
        set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'success', 'message' => 'Stripe connected successfully. Keys were saved and Stripe was enabled.' ], 60 );

        wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
        exit;
    }

    private static function exchange_code_for_token( $code ) {
        $response = wp_remote_post( self::TOKEN_URL, [
            'headers' => [
                'Content-Type' => 'application/x-www-form-urlencoded',
            ],
            'body'    => [
                'code'         => $code,
                'grant_type'   => 'authorization_code',
                'client_id'    => get_option( 'pbs_stripe_connect_client_id', '' ),
                'redirect_uri' => self::get_redirect_uri(),
            ],
            'timeout' => 20,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( wp_remote_retrieve_response_code( $response ) >= 400 ) {
            $message = $body['error_description'] ?? $body['error'] ?? 'Stripe token exchange failed.';
            return new WP_Error( 'stripe_oauth_error', $message );
        }

        if ( empty( $body['access_token'] ) ) {
            return new WP_Error( 'stripe_oauth_error', 'No access token returned from Stripe.' );
        }

        return $body;
    }

    public static function handle_disconnect() {
        if ( ! current_user_can( 'manage_options' ) ) {
            wp_die( esc_html__( 'Unauthorized', 'pbs-event-commerce' ) );
        }

        check_admin_referer( 'pbs_stripe_disconnect' );

        $client_id      = get_option( 'pbs_stripe_connect_client_id', '' );
        $stripe_user_id = get_option( 'pbs_stripe_user_id', '' );

        if ( $client_id && $stripe_user_id ) {
            wp_remote_post( self::DEAUTH_URL, [
                'headers' => [
                    'Content-Type' => 'application/x-www-form-urlencoded',
                ],
                'body'    => [
                    'client_id'      => $client_id,
                    'stripe_user_id' => $stripe_user_id,
                ],
                'timeout' => 20,
            ] );
        }

        delete_option( 'pbs_stripe_secret_key' );
        delete_option( 'pbs_stripe_publishable_key' );
        delete_option( 'pbs_stripe_user_id' );
        update_option( 'pbs_stripe_enabled', 0 );
        delete_transient( 'pbs_stripe_connection_status' );

        set_transient( 'pbs_stripe_oauth_notice', [ 'type' => 'info', 'message' => 'Stripe disconnected.' ], 60 );
        wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
        exit;
    }

    public static function connection_status() {
        $secret_key     = get_option( 'pbs_stripe_secret_key', '' );
        $publishable_key = get_option( 'pbs_stripe_publishable_key', '' );
        $stripe_user_id = get_option( 'pbs_stripe_user_id', '' );

        if ( empty( $secret_key ) ) {
            return [
                'connected'    => false,
                'account_name' => '',
                'email'        => '',
                'stripe_user_id' => $stripe_user_id,
                'mode'         => self::detect_mode( $secret_key, $publishable_key ),
            ];
        }

        $cached = get_transient( 'pbs_stripe_connection_status' );
        if ( is_array( $cached ) ) {
            return $cached;
        }

        $account = self::fetch_account( $secret_key );

        $status = [
            'connected'      => ! is_wp_error( $account ),
            'account_name'   => '',
            'email'          => '',
            'stripe_user_id' => $stripe_user_id,
            'mode'           => self::detect_mode( $secret_key, $publishable_key ),
        ];

        if ( ! is_wp_error( $account ) ) {
            $status['account_name'] = $account['name'];
            $status['email']        = $account['email'];
        }

        set_transient( 'pbs_stripe_connection_status', $status, 5 * MINUTE_IN_SECONDS );

        return $status;
    }

    public static function ajax_validate_keys() {
        check_ajax_referer( 'pbs_admin_nonce', 'nonce' );

        if ( ! current_user_can( 'manage_options' ) ) {
            wp_send_json_error( [ 'message' => 'Unauthorized.' ], 403 );
        }

        $secret_key      = sanitize_text_field( wp_unslash( $_POST['secret_key'] ?? '' ) );
        $publishable_key = sanitize_text_field( wp_unslash( $_POST['publishable_key'] ?? '' ) );

        if ( empty( $secret_key ) ) {
            wp_send_json_error( [ 'message' => 'Enter a Stripe secret key first.' ], 400 );
        }

        $account = self::fetch_account( $secret_key );
        if ( is_wp_error( $account ) ) {
            wp_send_json_error( [ 'message' => $account->get_error_message() ], 400 );
        }

        wp_send_json_success( [
            'account_name' => $account['name'],
            'email'        => $account['email'],
            'mode'         => self::detect_mode( $secret_key, $publishable_key ),
            'message'      => 'Stripe keys are valid.',
        ] );
    }

    private static function fetch_account( $secret_key ) {
        $response = wp_remote_get( self::ACCOUNT_URL, [
            'headers' => [
                'Authorization' => 'Bearer ' . $secret_key,
            ],
            'timeout' => 20,
        ] );

        if ( is_wp_error( $response ) ) {
            return $response;
        }

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( wp_remote_retrieve_response_code( $response ) >= 400 || ! empty( $body['error'] ) ) {
            $message = $body['error']['message'] ?? 'Stripe rejected the provided key.';
            return new WP_Error( 'stripe_account_error', $message );
        }

        $name  = $body['business_profile']['name'] ?? $body['settings']['dashboard']['display_name'] ?? $body['display_name'] ?? '';
        $email = $body['email'] ?? '';

        return [
            'name'  => $name,
            'email' => $email,
        ];
    }

    private static function detect_mode( $secret_key, $publishable_key = '' ) {
        if ( 0 === strpos( (string) $secret_key, 'sk_live_' ) || 0 === strpos( (string) $publishable_key, 'pk_live_' ) ) {
            return 'live';
        }

        if ( 0 === strpos( (string) $secret_key, 'sk_test_' ) || 0 === strpos( (string) $publishable_key, 'pk_test_' ) ) {
            return 'test';
        }

        return '';
    }
}
