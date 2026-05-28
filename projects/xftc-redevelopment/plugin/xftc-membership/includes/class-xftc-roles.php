<?php
/**
 * Registers and manages custom XFTC user roles and capabilities.
 *
 * Roles:
 *  - TRACKSUITE_parent   : Register and manage athletes, pay fees, register for meets/travel
 *  - TRACKSUITE_athlete  : View own stats, history, and upcoming meets
 *  - TRACKSUITE_coach    : Create meets, register athletes, enter results
 *  - TRACKSUITE_admin    : Full access to all plugin functionality
 *  - TRACKSUITE_staff    : Update hours, view pay history
 *
 * @package TRACKSUITE_Membership
 */

defined( 'ABSPATH' ) || exit;

class TRACKSUITE_Roles {

    /**
     * Hook into WordPress init to register roles.
     */
    public function init() {
        add_action( 'init', [ $this, 'register_roles' ] );
    }

    /**
     * Register all custom roles.
     * Uses add_role() — safe to call repeatedly (WP ignores if already exists).
     */
    public function register_roles() {

        // ── Parent ────────────────────────────────────────────────────────────
        add_role( 'TRACKSUITE_parent', __( 'XFTC Parent', 'ts-membership' ), [
            'read'                      => true,
            'TRACKSUITE_register_athlete'     => true,
            'TRACKSUITE_manage_own_athletes'  => true,
            'TRACKSUITE_view_own_payments'    => true,
            'TRACKSUITE_register_for_meet'    => true,
            'TRACKSUITE_register_travel'      => true,
        ] );

        // ── Athlete ───────────────────────────────────────────────────────────
        add_role( 'TRACKSUITE_athlete', __( 'XFTC Athlete', 'ts-membership' ), [
            'read'                  => true,
            'TRACKSUITE_view_own_stats'   => true,
            'TRACKSUITE_view_own_history' => true,
            'TRACKSUITE_view_meets'       => true,
        ] );

        // ── Coach ─────────────────────────────────────────────────────────────
        add_role( 'TRACKSUITE_coach', __( 'XFTC Coach', 'ts-membership' ), [
            'read'                      => true,
            'TRACKSUITE_create_meets'         => true,
            'TRACKSUITE_edit_meets'           => true,
            'TRACKSUITE_register_athletes'    => true,
            'TRACKSUITE_enter_results'        => true,
            'TRACKSUITE_view_all_athletes'    => true,
            'TRACKSUITE_view_all_stats'       => true,
        ] );

        // ── Admin ─────────────────────────────────────────────────────────────
        add_role( 'TRACKSUITE_admin', __( 'XFTC Admin', 'ts-membership' ), [
            'read'                      => true,
            'TRACKSUITE_manage_members'       => true,
            'TRACKSUITE_manage_seasons'       => true,
            'TRACKSUITE_manage_meets'         => true,
            'TRACKSUITE_manage_travel'        => true,
            'TRACKSUITE_manage_payments'      => true,
            'TRACKSUITE_manage_payroll'       => true,
            'TRACKSUITE_manage_staff'         => true,
            'TRACKSUITE_view_reports'         => true,
            'TRACKSUITE_export_data'          => true,
            'TRACKSUITE_manage_settings'      => true,
            'TRACKSUITE_register_athlete'     => true,
            'TRACKSUITE_enter_results'        => true,
            'TRACKSUITE_create_meets'         => true,
            'TRACKSUITE_edit_meets'           => true,
            'TRACKSUITE_view_all_athletes'    => true,
            'TRACKSUITE_view_all_stats'       => true,
            // Standard WP admin caps
            'manage_options'            => true,
            'edit_users'                => true,
        ] );

        // ── Staff ─────────────────────────────────────────────────────────────
        add_role( 'TRACKSUITE_staff', __( 'XFTC Staff', 'ts-membership' ), [
            'read'                      => true,
            'TRACKSUITE_update_own_hours'     => true,
            'TRACKSUITE_view_own_payroll'     => true,
        ] );

        // Also give the built-in administrator role all XFTC caps
        $wp_admin = get_role( 'administrator' );
        if ( $wp_admin ) {
            $TRACKSUITE_caps = [
                'TRACKSUITE_manage_members', 'TRACKSUITE_manage_seasons', 'TRACKSUITE_manage_meets',
                'TRACKSUITE_manage_travel',  'TRACKSUITE_manage_payments','TRACKSUITE_manage_payroll',
                'TRACKSUITE_manage_staff',   'TRACKSUITE_view_reports',   'TRACKSUITE_export_data',
                'TRACKSUITE_manage_settings','TRACKSUITE_register_athlete','TRACKSUITE_enter_results',
                'TRACKSUITE_create_meets',   'TRACKSUITE_edit_meets',     'TRACKSUITE_view_all_athletes',
                'TRACKSUITE_view_all_stats',
            ];
            foreach ( $TRACKSUITE_caps as $cap ) {
                $wp_admin->add_cap( $cap );
            }
        }
    }

    /**
     * Remove all custom roles on plugin uninstall.
     * Called from uninstall.php.
     */
    public static function remove_roles() {
        remove_role( 'TRACKSUITE_parent' );
        remove_role( 'TRACKSUITE_athlete' );
        remove_role( 'TRACKSUITE_coach' );
        remove_role( 'TRACKSUITE_admin' );
        remove_role( 'TRACKSUITE_staff' );
    }
}

