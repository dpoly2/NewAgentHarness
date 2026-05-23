<?php
/**
 * Registers and manages custom XFTC user roles and capabilities.
 *
 * Roles:
 *  - xftc_parent   : Register and manage athletes, pay fees, register for meets/travel
 *  - xftc_athlete  : View own stats, history, and upcoming meets
 *  - xftc_coach    : Create meets, register athletes, enter results
 *  - xftc_admin    : Full access to all plugin functionality
 *  - xftc_staff    : Update hours, view pay history
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Roles {

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
        add_role( 'xftc_parent', __( 'XFTC Parent', 'xftc-membership' ), [
            'read'                      => true,
            'xftc_register_athlete'     => true,
            'xftc_manage_own_athletes'  => true,
            'xftc_view_own_payments'    => true,
            'xftc_register_for_meet'    => true,
            'xftc_register_travel'      => true,
        ] );

        // ── Athlete ───────────────────────────────────────────────────────────
        add_role( 'xftc_athlete', __( 'XFTC Athlete', 'xftc-membership' ), [
            'read'                  => true,
            'xftc_view_own_stats'   => true,
            'xftc_view_own_history' => true,
            'xftc_view_meets'       => true,
        ] );

        // ── Coach ─────────────────────────────────────────────────────────────
        add_role( 'xftc_coach', __( 'XFTC Coach', 'xftc-membership' ), [
            'read'                      => true,
            'xftc_create_meets'         => true,
            'xftc_edit_meets'           => true,
            'xftc_register_athletes'    => true,
            'xftc_enter_results'        => true,
            'xftc_view_all_athletes'    => true,
            'xftc_view_all_stats'       => true,
        ] );

        // ── Admin ─────────────────────────────────────────────────────────────
        add_role( 'xftc_admin', __( 'XFTC Admin', 'xftc-membership' ), [
            'read'                      => true,
            'xftc_manage_members'       => true,
            'xftc_manage_seasons'       => true,
            'xftc_manage_meets'         => true,
            'xftc_manage_travel'        => true,
            'xftc_manage_payments'      => true,
            'xftc_manage_payroll'       => true,
            'xftc_manage_staff'         => true,
            'xftc_view_reports'         => true,
            'xftc_export_data'          => true,
            'xftc_manage_settings'      => true,
            'xftc_register_athlete'     => true,
            'xftc_enter_results'        => true,
            'xftc_create_meets'         => true,
            'xftc_edit_meets'           => true,
            'xftc_view_all_athletes'    => true,
            'xftc_view_all_stats'       => true,
            // Standard WP admin caps
            'manage_options'            => true,
            'edit_users'                => true,
        ] );

        // ── Staff ─────────────────────────────────────────────────────────────
        add_role( 'xftc_staff', __( 'XFTC Staff', 'xftc-membership' ), [
            'read'                      => true,
            'xftc_update_own_hours'     => true,
            'xftc_view_own_payroll'     => true,
        ] );

        // Also give the built-in administrator role all XFTC caps
        $wp_admin = get_role( 'administrator' );
        if ( $wp_admin ) {
            $xftc_caps = [
                'xftc_manage_members', 'xftc_manage_seasons', 'xftc_manage_meets',
                'xftc_manage_travel',  'xftc_manage_payments','xftc_manage_payroll',
                'xftc_manage_staff',   'xftc_view_reports',   'xftc_export_data',
                'xftc_manage_settings','xftc_register_athlete','xftc_enter_results',
                'xftc_create_meets',   'xftc_edit_meets',     'xftc_view_all_athletes',
                'xftc_view_all_stats',
            ];
            foreach ( $xftc_caps as $cap ) {
                $wp_admin->add_cap( $cap );
            }
        }
    }

    /**
     * Remove all custom roles on plugin uninstall.
     * Called from uninstall.php.
     */
    public static function remove_roles() {
        remove_role( 'xftc_parent' );
        remove_role( 'xftc_athlete' );
        remove_role( 'xftc_coach' );
        remove_role( 'xftc_admin' );
        remove_role( 'xftc_staff' );
    }
}
