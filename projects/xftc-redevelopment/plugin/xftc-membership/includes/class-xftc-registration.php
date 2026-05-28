<?php
/**
 * Handles the parent registration flow and membership creation.
 *
 * @package TRACKSUITE_Membership
 */

defined( 'ABSPATH' ) || exit;

class TRACKSUITE_Registration {

    public function init() {
        add_action( 'wp_ajax_nopriv_TRACKSUITE_register_parent', [ $this, 'handle_parent_registration' ] );
        add_action( 'wp_ajax_TRACKSUITE_register_parent',        [ $this, 'handle_parent_registration' ] );
        add_action( 'wp_ajax_TRACKSUITE_add_athlete',            [ $this, 'handle_add_athlete' ] );
        add_action( 'wp_ajax_TRACKSUITE_register_membership',    [ $this, 'handle_register_membership' ] );
    }

    /**
     * AJAX: Register a new parent account.
     * Creates a WP user with the TRACKSUITE_parent role.
     */
    public function handle_parent_registration() {
        check_ajax_referer( 'TRACKSUITE_register_nonce', 'nonce' );

        $first_name = sanitize_text_field( $_POST['first_name'] ?? '' );
        $last_name  = sanitize_text_field( $_POST['last_name'] ?? '' );
        $email      = sanitize_email( $_POST['email'] ?? '' );
        $password   = $_POST['password'] ?? '';
        $phone      = sanitize_text_field( $_POST['phone'] ?? '' );

        if ( ! $first_name || ! $last_name || ! $email || ! $password ) {
            wp_send_json_error( [ 'message' => __( 'All fields are required.', 'ts-membership' ) ] );
        }

        if ( ! is_email( $email ) ) {
            wp_send_json_error( [ 'message' => __( 'Please enter a valid email address.', 'ts-membership' ) ] );
        }

        if ( email_exists( $email ) ) {
            wp_send_json_error( [ 'message' => __( 'An account with that email already exists.', 'ts-membership' ) ] );
        }

        if ( strlen( $password ) < 8 ) {
            wp_send_json_error( [ 'message' => __( 'Password must be at least 8 characters.', 'ts-membership' ) ] );
        }

        $username = sanitize_user( strtolower( $first_name . '.' . $last_name . '.' . wp_rand( 100, 999 ) ) );

        $user_id = wp_create_user( $username, $password, $email );

        if ( is_wp_error( $user_id ) ) {
            wp_send_json_error( [ 'message' => $user_id->get_error_message() ] );
        }

        // Set role and meta
        $user = new WP_User( $user_id );
        $user->set_role( 'TRACKSUITE_parent' );
        update_user_meta( $user_id, 'first_name', $first_name );
        update_user_meta( $user_id, 'last_name',  $last_name );
        update_user_meta( $user_id, 'TRACKSUITE_phone', $phone );

        // Send welcome email
        $emails = new TRACKSUITE_Emails();
        $emails->send_parent_welcome( $user_id );

        wp_send_json_success( [
            'message' => __( 'Account created! Please log in.', 'ts-membership' ),
            'user_id' => $user_id,
        ] );
    }

    /**
     * AJAX: Add an athlete profile to a parent account.
     */
    public function handle_add_athlete() {
        check_ajax_referer( 'TRACKSUITE_athlete_nonce', 'nonce' );

        if ( ! is_user_logged_in() ) {
            wp_send_json_error( [ 'message' => __( 'You must be logged in.', 'ts-membership' ) ] );
        }

        $parent_id = get_current_user_id();
        $members   = new TRACKSUITE_Members();

        $athlete_id = $members->create( [
            'parent_id'               => $parent_id,
            'first_name'              => sanitize_text_field( $_POST['first_name'] ?? '' ),
            'last_name'               => sanitize_text_field( $_POST['last_name'] ?? '' ),
            'dob'                     => sanitize_text_field( $_POST['dob'] ?? '' ),
            'gender'                  => sanitize_text_field( $_POST['gender'] ?? '' ),
            'team_level'              => sanitize_text_field( $_POST['team_level'] ?? '' ),
            'school'                  => sanitize_text_field( $_POST['school'] ?? '' ),
            'emergency_contact_name'  => sanitize_text_field( $_POST['emergency_contact_name'] ?? '' ),
            'emergency_contact_phone' => sanitize_text_field( $_POST['emergency_contact_phone'] ?? '' ),
        ] );

        if ( is_wp_error( $athlete_id ) ) {
            wp_send_json_error( [ 'message' => $athlete_id->get_error_message() ] );
        }

        wp_send_json_success( [
            'message'    => __( 'Athlete added successfully.', 'ts-membership' ),
            'athlete_id' => $athlete_id,
        ] );
    }

    /**
     * AJAX: Register an athlete for a season (create membership record).
     */
    public function handle_register_membership() {
        check_ajax_referer( 'TRACKSUITE_membership_nonce', 'nonce' );

        if ( ! is_user_logged_in() ) {
            wp_send_json_error( [ 'message' => __( 'You must be logged in.', 'ts-membership' ) ] );
        }

        global $wpdb;

        $athlete_id = absint( $_POST['athlete_id'] ?? 0 );
        $season_id  = absint( $_POST['season_id'] ?? 0 );
        $tier       = sanitize_text_field( $_POST['tier'] ?? 'standard' );

        // Validate athlete belongs to current parent
        $members = new TRACKSUITE_Members();
        $athlete = $members->get( $athlete_id );

        if ( ! $athlete || (int) $athlete->parent_id !== get_current_user_id() ) {
            wp_send_json_error( [ 'message' => __( 'Invalid athlete.', 'ts-membership' ) ] );
        }

        // Get season fee
        $seasons = new TRACKSUITE_Seasons();
        $season  = $seasons->get( $season_id );

        if ( ! $season ) {
            wp_send_json_error( [ 'message' => __( 'Invalid season.', 'ts-membership' ) ] );
        }

        $amount_due = ( 'premium' === $tier ) ? (float) $season->fee_premium : (float) $season->fee_standard;

        // Check for duplicate registration
        $existing = $wpdb->get_var( $wpdb->prepare(
            "SELECT id FROM {$wpdb->prefix}TRACKSUITE_memberships WHERE athlete_id = %d AND season_id = %d",
            $athlete_id, $season_id
        ) );

        if ( $existing ) {
            wp_send_json_error( [ 'message' => __( 'This athlete is already registered for this season.', 'ts-membership' ) ] );
        }

        $result = $wpdb->insert( "{$wpdb->prefix}TRACKSUITE_memberships", [
            'athlete_id'     => $athlete_id,
            'season_id'      => $season_id,
            'tier'           => $tier,
            'status'         => 'pending',
            'payment_status' => 'unpaid',
            'amount_due'     => $amount_due,
            'amount_paid'    => 0.00,
        ] );

        if ( false === $result ) {
            wp_send_json_error( [ 'message' => $wpdb->last_error ] );
        }

        wp_send_json_success( [
            'message'       => __( 'Registration successful! Please complete payment.', 'ts-membership' ),
            'membership_id' => $wpdb->insert_id,
            'amount_due'    => $amount_due,
        ] );
    }
}

