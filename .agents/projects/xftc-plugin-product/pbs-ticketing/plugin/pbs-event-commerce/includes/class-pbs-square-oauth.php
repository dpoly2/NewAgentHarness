<?php
/**
 * PBS Square OAuth Handler
 * Implements Square OAuth 2.0 Code Flow per:
 * https://developer.squareup.com/docs/oauth-api/overview
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Square_OAuth {

    /** Authorization URL base (production) */
    const AUTH_URL     = 'https://connect.squareup.com/oauth2/authorize';
    /** Token exchange endpoint */
    const TOKEN_URL    = 'https://connect.squareup.com/oauth2/token';
    /** Token revoke endpoint */
    const REVOKE_URL   = 'https://connect.squareup.com/oauth2/revoke';

    /** Scopes needed for PBS Event Commerce */
    const SCOPES = [
        'PAYMENTS_WRITE',
        'PAYMENTS_READ',
        'ORDERS_WRITE',
        'ORDERS_READ',
        'MERCHANT_PROFILE_READ',
    ];

    public static function init() {
        // Hook into admin_init to catch the OAuth callback on the settings page
        add_action( 'admin_init', [ __CLASS__, 'handle_callback' ] );
        // Hook to handle disconnect action
        add_action( 'admin_post_pbs_square_disconnect', [ __CLASS__, 'handle_disconnect' ] );
    }

    /**
     * Build the Square authorization URL.
     * Includes state nonce for CSRF protection.
     */
    public static function get_auth_url() {
        $app_id      = get_option( 'pbs_square_app_id', '' );
        $redirect    = self::get_redirect_uri();
        $state       = self::get_or_create_state();
        $environment = get_option( 'pbs_square_env', 'sandbox' );

        // Sandbox uses a different subdomain
        $base = ( $environment === 'sandbox' )
            ? 'https://connect.squareupsandbox.com/oauth2/authorize'
            : self::AUTH_URL;

        $params = [
            'client_id'     => $app_id,
            'response_type' => 'code',
            'scope'         => implode( ' ', self::SCOPES ),
            'redirect_uri'  => $redirect,
            'state'         => $state,
            'session'       => 'false',
        ];

        return $base . '?' . http_build_query( $params );
    }

    /**
     * The redirect URI Square will send the seller back to.
     * Must match exactly what's registered in the Square Developer Console.
     */
    public static function get_redirect_uri() {
        return admin_url( 'admin.php?page=pbs-commerce-settings&square_oauth_callback=1' );
    }

    /**
     * Create or retrieve the CSRF state token.
     */
    private static function get_or_create_state() {
        $state = get_transient( 'pbs_square_oauth_state' );
        if ( ! $state ) {
            $state = wp_generate_password( 32, false );
            set_transient( 'pbs_square_oauth_state', $state, 10 * MINUTE_IN_SECONDS );
            // Option fallback for object-cached hosts where transients may not persist across redirects
            update_option( 'pbs_square_oauth_state_fallback', $state );
        }
        return $state;
    }

    /**
     * Handle the OAuth callback from Square.
     * Square redirects back with ?code=... or ?error=...
     */
    public static function handle_callback() {
        // Only run on settings page with callback flag
        if ( ! isset( $_GET['square_oauth_callback'] ) ) return;
        if ( ! isset( $_GET['page'] ) || $_GET['page'] !== 'pbs-commerce-settings' ) return;
        if ( ! current_user_can( 'manage_options' ) ) return;

        // Record this attempt for diagnostics regardless of outcome
        $attempt = [
            'time'  => current_time( 'mysql' ),
            'has_code'  => isset( $_GET['code'] ),
            'has_state' => isset( $_GET['state'] ),
            'has_error' => isset( $_GET['error'] ),
        ];

        // Handle error response from Square
        if ( isset( $_GET['error'] ) ) {
            $error   = sanitize_text_field( $_GET['error'] );
            $message = sanitize_text_field( $_GET['error_description'] ?? 'Authorization denied.' );
            $attempt['result'] = 'square_error';
            update_option( 'pbs_square_last_oauth', $attempt );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&square_msg=error&square_err=' . rawurlencode( $message ) ) );
            exit;
        }

        // Validate state (CSRF check)
        $saved_state = get_transient( 'pbs_square_oauth_state' );
        // Also check option fallback (for object-cached hosts where transients are unreliable)
        if ( ! $saved_state ) {
            $saved_state = get_option( 'pbs_square_oauth_state_fallback', '' );
        }
        $given_state = sanitize_text_field( $_GET['state'] ?? '' );

        if ( empty( $saved_state ) || ! hash_equals( $saved_state, $given_state ) ) {
            $attempt['result'] = 'state_mismatch';
            $attempt['saved_state_empty'] = empty( $saved_state );
            update_option( 'pbs_square_last_oauth', $attempt );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&square_msg=state_mismatch' ) );
            exit;
        }
        delete_transient( 'pbs_square_oauth_state' );
        delete_option( 'pbs_square_oauth_state_fallback' );

        // Exchange authorization code for access token
        $code = sanitize_text_field( $_GET['code'] ?? '' );
        if ( empty( $code ) ) {
            $attempt['result'] = 'no_code';
            update_option( 'pbs_square_last_oauth', $attempt );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&square_msg=no_code' ) );
            exit;
        }

        $result = self::exchange_code_for_token( $code );

        if ( is_wp_error( $result ) ) {
            $attempt['result'] = 'exchange_failed';
            $attempt['error']  = $result->get_error_message();
            update_option( 'pbs_square_last_oauth', $attempt );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&square_msg=error&square_err=' . rawurlencode( 'Token exchange failed: ' . $result->get_error_message() ) ) );
            exit;
        }

        // Save tokens and merchant info
        update_option( 'pbs_square_access_token',  $result['access_token'] );
        update_option( 'pbs_square_refresh_token', $result['refresh_token'] ?? '' );
        update_option( 'pbs_square_token_expires', $result['expires_at'] ?? '' );
        update_option( 'pbs_square_merchant_id',   $result['merchant_id'] ?? '' );
        update_option( 'pbs_square_enabled', 1 );

        if ( empty( get_option( 'pbs_square_location_id' ) ) ) {
            PBS_Square::fetch_location( $result['access_token'] );
        }

        $attempt['result'] = 'success';
        update_option( 'pbs_square_last_oauth', $attempt );

        wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&square_msg=connected' ) );
        exit;
    }

    /**
     * Exchange authorization code for access + refresh token.
     */
    private static function exchange_code_for_token( $code ) {
        $app_id      = get_option( 'pbs_square_app_id', '' );
        $app_secret  = get_option( 'pbs_square_app_secret', '' );
        $environment = get_option( 'pbs_square_env', 'sandbox' );

        $token_url = ( $environment === 'sandbox' )
            ? 'https://connect.squareupsandbox.com/oauth2/token'
            : self::TOKEN_URL;

        $response = wp_remote_post( $token_url, [
            'headers' => [
                'Content-Type'  => 'application/json',
                'Square-Version' => '2024-10-17',
            ],
            'body' => wp_json_encode( [
                'client_id'     => $app_id,
                'client_secret' => $app_secret,
                'code'          => $code,
                'grant_type'    => 'authorization_code',
                'redirect_uri'  => self::get_redirect_uri(),
            ] ),
            'timeout' => 15,
        ] );

        if ( is_wp_error( $response ) ) return $response;

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( isset( $body['errors'] ) ) {
            $msg = $body['errors'][0]['detail'] ?? 'Unknown Square error.';
            return new WP_Error( 'square_oauth_error', $msg );
        }

        if ( empty( $body['access_token'] ) ) {
            return new WP_Error( 'no_token', 'No access token in Square response.' );
        }

        return $body;
    }

    /**
     * Refresh an expired access token using the saved refresh token.
     */
    public static function refresh_token() {
        $app_id       = get_option( 'pbs_square_app_id', '' );
        $app_secret   = get_option( 'pbs_square_app_secret', '' );
        $refresh_tok  = get_option( 'pbs_square_refresh_token', '' );
        $environment  = get_option( 'pbs_square_env', 'sandbox' );

        if ( empty( $refresh_tok ) ) return new WP_Error( 'no_refresh_token', 'No refresh token saved.' );

        $token_url = ( $environment === 'sandbox' )
            ? 'https://connect.squareupsandbox.com/oauth2/token'
            : self::TOKEN_URL;

        $response = wp_remote_post( $token_url, [
            'headers' => [
                'Content-Type'   => 'application/json',
                'Square-Version' => '2024-10-17',
            ],
            'body' => wp_json_encode( [
                'client_id'     => $app_id,
                'client_secret' => $app_secret,
                'refresh_token' => $refresh_tok,
                'grant_type'    => 'refresh_token',
            ] ),
            'timeout' => 15,
        ] );

        if ( is_wp_error( $response ) ) return $response;

        $body = json_decode( wp_remote_retrieve_body( $response ), true );

        if ( ! empty( $body['access_token'] ) ) {
            update_option( 'pbs_square_access_token',  $body['access_token'] );
            update_option( 'pbs_square_token_expires', $body['expires_at'] ?? '' );
            return $body['access_token'];
        }

        return new WP_Error( 'refresh_failed', $body['errors'][0]['detail'] ?? 'Refresh failed.' );
    }

    /**
     * Disconnect / revoke Square OAuth tokens.
     */
    public static function handle_disconnect() {
        if ( ! current_user_can( 'manage_options' ) ) wp_die( 'Unauthorized' );
        check_admin_referer( 'pbs_square_disconnect' );

        $access_token = get_option( 'pbs_square_access_token', '' );
        $app_id       = get_option( 'pbs_square_app_id', '' );
        $app_secret   = get_option( 'pbs_square_app_secret', '' );
        $environment  = get_option( 'pbs_square_env', 'sandbox' );

        // Revoke token with Square
        if ( $access_token && $app_secret ) {
            $revoke_url = ( $environment === 'sandbox' )
                ? 'https://connect.squareupsandbox.com/oauth2/revoke'
                : self::REVOKE_URL;

            wp_remote_post( $revoke_url, [
                'headers' => [
                    'Content-Type'        => 'application/json',
                    'Authorization'       => 'Client ' . $app_secret,
                    'Square-Version'      => '2024-10-17',
                ],
                'body'    => wp_json_encode( [ 'client_id' => $app_id, 'access_token' => $access_token ] ),
                'timeout' => 10,
            ] );
        }

        // Clear all Square tokens from DB
        delete_option( 'pbs_square_access_token' );
        delete_option( 'pbs_square_refresh_token' );
        delete_option( 'pbs_square_token_expires' );
        delete_option( 'pbs_square_merchant_id' );
        update_option( 'pbs_square_enabled', 0 );

        set_transient( 'pbs_square_oauth_notice', [ 'type' => 'info', 'message' => 'Square disconnected.' ], 60 );
        wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings' ) );
        exit;
    }

    /**
     * Return connection status details for display in settings.
     */
    public static function connection_status() {
        $token    = get_option( 'pbs_square_access_token', '' );
        $expires  = get_option( 'pbs_square_token_expires', '' );
        $merchant = get_option( 'pbs_square_merchant_id', '' );
        $location = get_option( 'pbs_square_location_id', '' );

        if ( empty( $token ) ) {
            return [ 'connected' => false, 'expired' => false, 'merchant_id' => '', 'location_id' => '', 'expires_at' => '', 'label' => 'Not connected', 'color' => '#e0e0e0' ];
        }

        $exp_ts  = $expires ? strtotime( $expires ) : 0;
        $expired = $exp_ts && $exp_ts < time();

        return [
            'connected'   => ! $expired,
            'expired'     => $expired,
            'label'       => $expired ? 'Token expired — reconnect' : 'Connected',
            'color'       => $expired ? '#f44336' : '#4caf50',
            'merchant_id' => $merchant,
            'location_id' => $location,
            'expires_at'  => $expires ? date( 'M j, Y', $exp_ts ) : 'Unknown',
        ];
    }
}
