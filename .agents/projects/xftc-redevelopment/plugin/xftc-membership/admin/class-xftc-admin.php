<?php
/**
 * Admin panel — registers WP Admin menus, pages, and assets.
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Admin {

    public function init() {
        add_action( 'admin_menu',            [ $this, 'register_menus' ] );
        add_action( 'admin_enqueue_scripts', [ $this, 'enqueue_assets' ] );
    }

    /**
     * Register the top-level WP Admin menu and sub-menus.
     */
    public function register_menus() {
        // Top-level menu
        add_menu_page(
            __( 'Xtreme Force', 'xftc-membership' ),
            __( 'Xtreme Force', 'xftc-membership' ),
            'xftc_manage_members',
            'xftc-dashboard',
            [ $this, 'page_dashboard' ],
            'dashicons-groups',
            30
        );

        // Dashboard (same as top-level)
        add_submenu_page(
            'xftc-dashboard',
            __( 'Dashboard', 'xftc-membership' ),
            __( 'Dashboard', 'xftc-membership' ),
            'xftc_manage_members',
            'xftc-dashboard',
            [ $this, 'page_dashboard' ]
        );

        // Members
        add_submenu_page(
            'xftc-dashboard',
            __( 'Members', 'xftc-membership' ),
            __( 'Members', 'xftc-membership' ),
            'xftc_manage_members',
            'xftc-members',
            [ $this, 'page_members' ]
        );

        // Seasons
        add_submenu_page(
            'xftc-dashboard',
            __( 'Seasons', 'xftc-membership' ),
            __( 'Seasons', 'xftc-membership' ),
            'xftc_manage_seasons',
            'xftc-seasons',
            [ $this, 'page_seasons' ]
        );

        // Meets
        add_submenu_page(
            'xftc-dashboard',
            __( 'Meets', 'xftc-membership' ),
            __( 'Meets', 'xftc-membership' ),
            'xftc_manage_meets',
            'xftc-meets',
            [ $this, 'page_meets' ]
        );

        // Travel
        add_submenu_page(
            'xftc-dashboard',
            __( 'Travel', 'xftc-membership' ),
            __( 'Travel', 'xftc-membership' ),
            'xftc_manage_travel',
            'xftc-travel',
            [ $this, 'page_travel' ]
        );

        // Payroll
        add_submenu_page(
            'xftc-dashboard',
            __( 'Payroll', 'xftc-membership' ),
            __( 'Payroll', 'xftc-membership' ),
            'xftc_manage_payroll',
            'xftc-payroll',
            [ $this, 'page_payroll' ]
        );

        // Reports
        add_submenu_page(
            'xftc-dashboard',
            __( 'Reports', 'xftc-membership' ),
            __( 'Reports', 'xftc-membership' ),
            'xftc_view_reports',
            'xftc-reports',
            [ $this, 'page_reports' ]
        );

        // Settings
        add_submenu_page(
            'xftc-dashboard',
            __( 'Settings', 'xftc-membership' ),
            __( 'Settings', 'xftc-membership' ),
            'xftc_manage_settings',
            'xftc-settings',
            [ $this, 'page_settings' ]
        );
    }

    /**
     * Enqueue admin CSS and JS.
     *
     * @param string $hook Current admin page hook.
     */
    public function enqueue_assets( string $hook ) {
        if ( strpos( $hook, 'xftc-' ) === false ) {
            return;
        }
        wp_enqueue_style(
            'xftc-admin',
            XFTC_PLUGIN_URL . 'admin/assets/admin.css',
            [],
            XFTC_VERSION
        );
        wp_enqueue_script(
            'xftc-admin',
            XFTC_PLUGIN_URL . 'admin/assets/admin.js',
            [ 'jquery' ],
            XFTC_VERSION,
            true
        );
        wp_localize_script( 'xftc-admin', 'xftcAdmin', [
            'ajaxUrl' => admin_url( 'admin-ajax.php' ),
            'nonce'   => wp_create_nonce( 'xftc_admin_nonce' ),
        ] );
    }

    // ── Page Renderers ────────────────────────────────────────────────────────

    public function page_dashboard() {
        $members  = new XFTC_Members();
        $seasons  = new XFTC_Seasons();
        $total    = $members->count();
        $active   = $seasons->get_active();
        include XFTC_PLUGIN_DIR . 'admin/views/dashboard.php';
    }

    public function page_members() {
        $members = new XFTC_Members();
        $search  = sanitize_text_field( $_GET['s'] ?? '' );
        $list    = $members->get_all( [ 'search' => $search, 'limit' => 50 ] );
        include XFTC_PLUGIN_DIR . 'admin/views/members.php';
    }

    public function page_seasons() {
        $seasons = new XFTC_Seasons();
        $list    = $seasons->get_all();
        include XFTC_PLUGIN_DIR . 'admin/views/seasons.php';
    }

    public function page_meets() {
        include XFTC_PLUGIN_DIR . 'admin/views/meets.php';
    }

    public function page_travel() {
        include XFTC_PLUGIN_DIR . 'admin/views/travel.php';
    }

    public function page_payroll() {
        include XFTC_PLUGIN_DIR . 'admin/views/payroll.php';
    }

    public function page_reports() {
        include XFTC_PLUGIN_DIR . 'admin/views/reports.php';
    }

    public function page_settings() {
        if ( isset( $_POST['xftc_save_settings'] ) && check_admin_referer( 'xftc_settings_nonce' ) ) {
            update_option( 'xftc_club_name',         sanitize_text_field( $_POST['xftc_club_name'] ?? '' ) );
            update_option( 'xftc_admin_email',       sanitize_email( $_POST['xftc_admin_email'] ?? '' ) );
            update_option( 'xftc_stripe_mode',       sanitize_text_field( $_POST['xftc_stripe_mode'] ?? 'test' ) );
            update_option( 'xftc_stripe_public_key', sanitize_text_field( $_POST['xftc_stripe_public_key'] ?? '' ) );
            update_option( 'xftc_stripe_secret_key', sanitize_text_field( $_POST['xftc_stripe_secret_key'] ?? '' ) );
            add_settings_error( 'xftc_settings', 'saved', __( 'Settings saved.', 'xftc-membership' ), 'success' );
        }
        include XFTC_PLUGIN_DIR . 'admin/views/settings.php';
    }
}
