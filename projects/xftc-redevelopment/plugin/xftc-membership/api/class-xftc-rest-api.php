<?php
/**
 * Class TRACKSUITE_REST_API
 *
 * Registers all custom REST API endpoints for the XFTC Membership plugin.
 * Namespace: /wp-json/xftc/v1/
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

class TRACKSUITE_REST_API {

    private string $namespace = 'xftc/v1';

    public function __construct() {
        add_action( 'rest_api_init', [ $this, 'register_routes' ] );
    }

    public function register_routes(): void {

        /** ── ATHLETES ──────────────────────────────────────── */
        register_rest_route( $this->namespace, '/athletes', [
            [ 'methods' => 'GET',  'callback' => [ $this, 'get_athletes' ],    'permission_callback' => [ $this, 'require_coach_or_admin' ] ],
            [ 'methods' => 'POST', 'callback' => [ $this, 'create_athlete' ],  'permission_callback' => [ $this, 'require_parent_or_admin' ] ],
        ] );
        register_rest_route( $this->namespace, '/athletes/(?P<id>\d+)', [
            [ 'methods' => 'GET', 'callback' => [ $this, 'get_athlete' ],      'permission_callback' => [ $this, 'require_authenticated' ] ],
            [ 'methods' => 'PUT', 'callback' => [ $this, 'update_athlete' ],   'permission_callback' => [ $this, 'require_parent_or_admin' ] ],
        ] );
        register_rest_route( $this->namespace, '/athletes/(?P<id>\d+)/stats', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'get_athlete_stats' ],
            'permission_callback' => [ $this, 'require_authenticated' ],
        ] );

        /** ── SEASONS ───────────────────────────────────────── */
        register_rest_route( $this->namespace, '/seasons', [
            [ 'methods' => 'GET',  'callback' => [ $this, 'get_seasons' ],    'permission_callback' => '__return_true' ],
            [ 'methods' => 'POST', 'callback' => [ $this, 'create_season' ],  'permission_callback' => [ $this, 'require_admin' ] ],
        ] );

        /** ── MEETS ─────────────────────────────────────────── */
        register_rest_route( $this->namespace, '/meets', [
            [ 'methods' => 'GET',  'callback' => [ $this, 'get_meets' ],    'permission_callback' => '__return_true' ],
            [ 'methods' => 'POST', 'callback' => [ $this, 'create_meet' ],  'permission_callback' => [ $this, 'require_coach_or_admin' ] ],
        ] );
        register_rest_route( $this->namespace, '/meets/(?P<id>\d+)', [
            [ 'methods' => 'GET',  'callback' => [ $this, 'get_meet' ],    'permission_callback' => '__return_true' ],
            [ 'methods' => 'PUT',  'callback' => [ $this, 'update_meet' ], 'permission_callback' => [ $this, 'require_coach_or_admin' ] ],
        ] );
        register_rest_route( $this->namespace, '/meets/(?P<id>\d+)/register', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'register_for_meet' ],
            'permission_callback' => [ $this, 'require_parent_or_admin' ],
        ] );
        register_rest_route( $this->namespace, '/meets/(?P<id>\d+)/roster', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'get_meet_roster' ],
            'permission_callback' => [ $this, 'require_coach_or_admin' ],
        ] );

        /** ── RESULTS ───────────────────────────────────────── */
        register_rest_route( $this->namespace, '/results', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'add_result' ],
            'permission_callback' => [ $this, 'require_coach_or_admin' ],
        ] );
        register_rest_route( $this->namespace, '/results/(?P<id>\d+)', [
            [ 'methods' => 'PUT',    'callback' => [ $this, 'update_result' ], 'permission_callback' => [ $this, 'require_coach_or_admin' ] ],
            [ 'methods' => 'DELETE', 'callback' => [ $this, 'delete_result' ], 'permission_callback' => [ $this, 'require_admin' ] ],
        ] );

        /** ── TRAVEL ────────────────────────────────────────── */
        register_rest_route( $this->namespace, '/travel', [
            [ 'methods' => 'GET',  'callback' => [ $this, 'get_travel' ],     'permission_callback' => [ $this, 'require_authenticated' ] ],
            [ 'methods' => 'POST', 'callback' => [ $this, 'book_travel' ],    'permission_callback' => [ $this, 'require_parent_or_admin' ] ],
        ] );
        register_rest_route( $this->namespace, '/travel/(?P<id>\d+)', [
            [ 'methods' => 'PUT',    'callback' => [ $this, 'update_travel' ],  'permission_callback' => [ $this, 'require_admin' ] ],
            [ 'methods' => 'DELETE', 'callback' => [ $this, 'cancel_travel' ],  'permission_callback' => [ $this, 'require_admin' ] ],
        ] );

        /** ── PAYMENTS ──────────────────────────────────────── */
        register_rest_route( $this->namespace, '/payments/checkout', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'create_checkout' ],
            'permission_callback' => [ $this, 'require_parent_or_admin' ],
        ] );
        register_rest_route( $this->namespace, '/payments/webhook', [
            'methods'             => 'POST',
            'callback'            => [ $this, 'handle_webhook' ],
            'permission_callback' => '__return_true', // Verified via Stripe signature
        ] );

        /** ── REPORTS ───────────────────────────────────────── */
        register_rest_route( $this->namespace, '/reports/(?P<type>[a-z_]+)', [
            'methods'             => 'GET',
            'callback'            => [ $this, 'get_report' ],
            'permission_callback' => [ $this, 'require_admin' ],
        ] );
    }

    /** ─── ATHLETE HANDLERS ──────────────────────────────────── */

    public function get_athletes( \WP_REST_Request $req ): \WP_REST_Response {
        $members = new TRACKSUITE_Members();
        return new \WP_REST_Response( $members->get_all_members(), 200 );
    }

    public function create_athlete( \WP_REST_Request $req ): \WP_REST_Response {
        $members = new TRACKSUITE_Members();
        $id = $members->create_member( $req->get_json_params() );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Could not create athlete.' ], 400 );
        return new \WP_REST_Response( [ 'id' => $id ], 201 );
    }

    public function get_athlete( \WP_REST_Request $req ): \WP_REST_Response {
        $members = new TRACKSUITE_Members();
        $athlete = $members->get_member( (int) $req['id'] );
        if ( ! $athlete ) return new \WP_REST_Response( [ 'error' => 'Not found.' ], 404 );
        return new \WP_REST_Response( $athlete, 200 );
    }

    public function update_athlete( \WP_REST_Request $req ): \WP_REST_Response {
        $members = new TRACKSUITE_Members();
        $updated = $members->update_member( (int) $req['id'], $req->get_json_params() );
        return new \WP_REST_Response( [ 'updated' => $updated ], $updated ? 200 : 400 );
    }

    public function get_athlete_stats( \WP_REST_Request $req ): \WP_REST_Response {
        $results = new TRACKSUITE_Results();
        $id      = (int) $req['id'];
        return new \WP_REST_Response( [
            'athlete_id'    => $id,
            'all_results'   => $results->get_athlete_results( $id ),
            'personal_bests'=> $results->get_personal_bests( $id ),
            'events'        => $results->get_athlete_events( $id ),
        ], 200 );
    }

    /** ─── SEASON HANDLERS ───────────────────────────────────── */

    public function get_seasons( \WP_REST_Request $req ): \WP_REST_Response {
        $seasons = new TRACKSUITE_Seasons();
        return new \WP_REST_Response( $seasons->get_all_seasons(), 200 );
    }

    public function create_season( \WP_REST_Request $req ): \WP_REST_Response {
        $seasons = new TRACKSUITE_Seasons();
        $id = $seasons->create_season( $req->get_json_params() );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Could not create season.' ], 400 );
        return new \WP_REST_Response( [ 'id' => $id ], 201 );
    }

    /** ─── MEET HANDLERS ─────────────────────────────────────── */

    public function get_meets( \WP_REST_Request $req ): \WP_REST_Response {
        $meets  = new TRACKSUITE_Meets();
        $status = sanitize_text_field( $req->get_param( 'status' ) ?? '' );
        return new \WP_REST_Response( $meets->get_all_meets( $status ), 200 );
    }

    public function create_meet( \WP_REST_Request $req ): \WP_REST_Response {
        $meets = new TRACKSUITE_Meets();
        $id    = $meets->create_meet( $req->get_json_params() );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Could not create meet.' ], 400 );
        return new \WP_REST_Response( [ 'id' => $id ], 201 );
    }

    public function get_meet( \WP_REST_Request $req ): \WP_REST_Response {
        $meets = new TRACKSUITE_Meets();
        $meet  = $meets->get_meet( (int) $req['id'] );
        if ( ! $meet ) return new \WP_REST_Response( [ 'error' => 'Not found.' ], 404 );
        return new \WP_REST_Response( $meet, 200 );
    }

    public function update_meet( \WP_REST_Request $req ): \WP_REST_Response {
        $meets   = new TRACKSUITE_Meets();
        $updated = $meets->update_meet( (int) $req['id'], $req->get_json_params() );
        return new \WP_REST_Response( [ 'updated' => $updated ], $updated ? 200 : 400 );
    }

    public function register_for_meet( \WP_REST_Request $req ): \WP_REST_Response {
        $meets  = new TRACKSUITE_Meets();
        $params = $req->get_json_params();
        $id     = $meets->register_athlete( (int) $req['id'], (int) $params['athlete_id'], $params );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Registration failed.' ], 400 );
        return new \WP_REST_Response( [ 'entry_id' => $id ], 201 );
    }

    public function get_meet_roster( \WP_REST_Request $req ): \WP_REST_Response {
        $meets = new TRACKSUITE_Meets();
        return new \WP_REST_Response( $meets->get_meet_roster( (int) $req['id'] ), 200 );
    }

    /** ─── RESULT HANDLERS ───────────────────────────────────── */

    public function add_result( \WP_REST_Request $req ): \WP_REST_Response {
        $results = new TRACKSUITE_Results();
        $id      = $results->add_result( $req->get_json_params() );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Could not save result.' ], 400 );
        return new \WP_REST_Response( [ 'id' => $id ], 201 );
    }

    public function update_result( \WP_REST_Request $req ): \WP_REST_Response {
        $results = new TRACKSUITE_Results();
        $updated = $results->update_result( (int) $req['id'], $req->get_json_params() );
        return new \WP_REST_Response( [ 'updated' => $updated ], $updated ? 200 : 400 );
    }

    public function delete_result( \WP_REST_Request $req ): \WP_REST_Response {
        $results = new TRACKSUITE_Results();
        $deleted = $results->delete_result( (int) $req['id'] );
        return new \WP_REST_Response( [ 'deleted' => $deleted ], $deleted ? 200 : 400 );
    }

    /** ─── TRAVEL HANDLERS ───────────────────────────────────── */

    public function get_travel( \WP_REST_Request $req ): \WP_REST_Response {
        $travel  = new TRACKSUITE_Travel();
        $meet_id = (int) $req->get_param( 'meet_id' );
        $data    = $meet_id
            ? $travel->get_meet_travel( $meet_id )
            : $travel->get_athlete_travel( get_current_user_id() );
        return new \WP_REST_Response( $data, 200 );
    }

    public function book_travel( \WP_REST_Request $req ): \WP_REST_Response {
        $travel = new TRACKSUITE_Travel();
        $id     = $travel->create_booking( $req->get_json_params() );
        if ( ! $id ) return new \WP_REST_Response( [ 'error' => 'Booking failed.' ], 400 );
        return new \WP_REST_Response( [ 'booking_id' => $id ], 201 );
    }

    public function update_travel( \WP_REST_Request $req ): \WP_REST_Response {
        $travel  = new TRACKSUITE_Travel();
        $updated = $travel->update_booking( (int) $req['id'], $req->get_json_params() );
        return new \WP_REST_Response( [ 'updated' => $updated ], $updated ? 200 : 400 );
    }

    public function cancel_travel( \WP_REST_Request $req ): \WP_REST_Response {
        $travel  = new TRACKSUITE_Travel();
        $deleted = $travel->delete_booking( (int) $req['id'] );
        return new \WP_REST_Response( [ 'cancelled' => $deleted ], $deleted ? 200 : 400 );
    }

    /** ─── PAYMENT HANDLERS ──────────────────────────────────── */

    public function create_checkout( \WP_REST_Request $req ): \WP_REST_Response {
        $payments = new TRACKSUITE_Payments();
        $params   = $req->get_json_params();
        $params['user_id']     = get_current_user_id();
        $params['success_url'] = home_url( '/portal/?payment=success' );
        $params['cancel_url']  = home_url( '/portal/?payment=cancelled' );
        $result = $payments->create_checkout_session( $params );
        if ( is_wp_error( $result ) ) {
            return new \WP_REST_Response( [ 'error' => $result->get_error_message() ], 400 );
        }
        return new \WP_REST_Response( $result, 200 );
    }

    public function handle_webhook( \WP_REST_Request $req ): \WP_REST_Response {
        $payments = new TRACKSUITE_Payments();
        return $payments->handle_webhook( $req );
    }

    /** ─── REPORT HANDLER ────────────────────────────────────── */

    public function get_report( \WP_REST_Request $req ): \WP_REST_Response {
        $type = sanitize_key( $req['type'] );
        // TODO: Wire to class-ts-reports.php (Sprint 3)
        return new \WP_REST_Response( [ 'report' => $type, 'status' => 'coming in Sprint 3' ], 200 );
    }

    /** ─── PERMISSION CALLBACKS ──────────────────────────────── */

    public function require_authenticated(): bool {
        return is_user_logged_in();
    }

    public function require_parent_or_admin(): bool {
        return current_user_can( 'TRACKSUITE_parent' )
            || current_user_can( 'TRACKSUITE_admin' )
            || current_user_can( 'administrator' );
    }

    public function require_coach_or_admin(): bool {
        return current_user_can( 'TRACKSUITE_coach' )
            || current_user_can( 'TRACKSUITE_admin' )
            || current_user_can( 'administrator' );
    }

    public function require_admin(): bool {
        return current_user_can( 'TRACKSUITE_admin' ) || current_user_can( 'administrator' );
    }
}

