<?php
/**
 * Admin panel — registers WP Admin menus, pages, and assets.
 *
 * @package TRACKSUITE_Membership
 */

defined( 'ABSPATH' ) || exit;

class TRACKSUITE_Admin {

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
            __( 'Xtreme Force', 'ts-membership' ),
            __( 'Xtreme Force', 'ts-membership' ),
            'TRACKSUITE_manage_members',
            'ts-dashboard',
            [ $this, 'page_dashboard' ],
            'dashicons-groups',
            30
        );

        // Dashboard (same as top-level)
        add_submenu_page(
            'ts-dashboard',
            __( 'Dashboard', 'ts-membership' ),
            __( 'Dashboard', 'ts-membership' ),
            'TRACKSUITE_manage_members',
            'ts-dashboard',
            [ $this, 'page_dashboard' ]
        );

        // Members
        add_submenu_page(
            'ts-dashboard',
            __( 'Members', 'ts-membership' ),
            __( 'Members', 'ts-membership' ),
            'TRACKSUITE_manage_members',
            'ts-members',
            [ $this, 'page_members' ]
        );

        // Seasons
        add_submenu_page(
            'ts-dashboard',
            __( 'Seasons', 'ts-membership' ),
            __( 'Seasons', 'ts-membership' ),
            'TRACKSUITE_manage_seasons',
            'ts-seasons',
            [ $this, 'page_seasons' ]
        );

        // Meets
        add_submenu_page(
            'ts-dashboard',
            __( 'Meets', 'ts-membership' ),
            __( 'Meets', 'ts-membership' ),
            'TRACKSUITE_manage_meets',
            'ts-meets',
            [ $this, 'page_meets' ]
        );

        // Travel
        add_submenu_page(
            'ts-dashboard',
            __( 'Travel', 'ts-membership' ),
            __( 'Travel', 'ts-membership' ),
            'TRACKSUITE_manage_travel',
            'ts-travel',
            [ $this, 'page_travel' ]
        );

        // Payroll
        add_submenu_page(
            'ts-dashboard',
            __( 'Payroll', 'ts-membership' ),
            __( 'Payroll', 'ts-membership' ),
            'TRACKSUITE_manage_payroll',
            'ts-payroll',
            [ $this, 'page_payroll' ]
        );

        // Reports
        add_submenu_page(
            'ts-dashboard',
            __( 'Reports', 'ts-membership' ),
            __( 'Reports', 'ts-membership' ),
            'TRACKSUITE_view_reports',
            'ts-reports',
            [ $this, 'page_reports' ]
        );

        // Settings
        add_submenu_page(
            'ts-dashboard',
            __( 'Settings', 'ts-membership' ),
            __( 'Settings', 'ts-membership' ),
            'TRACKSUITE_manage_settings',
            'ts-settings',
            [ $this, 'page_settings' ]
        );
    }

    /**
     * Enqueue admin CSS and JS.
     *
     * @param string $hook Current admin page hook.
     */
    public function enqueue_assets( string $hook ) {
        if ( strpos( $hook, 'ts-' ) === false ) {
            return;
        }
        wp_enqueue_style(
            'ts-admin',
            TRACKSUITE_PLUGIN_URL . 'admin/assets/admin.css',
            [],
            TRACKSUITE_VERSION
        );
        wp_enqueue_script(
            'ts-admin',
            TRACKSUITE_PLUGIN_URL . 'admin/assets/admin.js',
            [ 'jquery' ],
            TRACKSUITE_VERSION,
            true
        );
        wp_localize_script( 'ts-admin', 'xftcAdmin', [
            'ajaxUrl' => admin_url( 'admin-ajax.php' ),
            'nonce'   => wp_create_nonce( 'TRACKSUITE_admin_nonce' ),
        ] );
    }

    // ── Page Renderers ────────────────────────────────────────────────────────

    public function page_dashboard() {
        $members  = new TRACKSUITE_Members();
        $seasons  = new TRACKSUITE_Seasons();
        $total    = $members->count();
        $active   = $seasons->get_active();
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/dashboard.php';
    }

    public function page_members() {
        $members = new TRACKSUITE_Members();
        $search  = sanitize_text_field( $_GET['s'] ?? '' );
        $list    = $members->get_all( [ 'search' => $search, 'limit' => 50 ] );
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/members.php';
    }

    public function page_seasons() {
        $seasons = new TRACKSUITE_Seasons();
        $list    = $seasons->get_all();
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/seasons.php';
    }

    public function page_meets() {
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/meets.php';
    }

    public function page_travel() {
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/travel.php';
    }

    public function page_payroll() {
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/payroll.php';
    }

    public function page_reports() {
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/reports.php';
    }

    public function page_settings() {
        if ( isset( $_POST['TRACKSUITE_save_settings'] ) && check_admin_referer( 'TRACKSUITE_settings_nonce' ) ) {
            update_option( 'TRACKSUITE_club_name',         sanitize_text_field( $_POST['TRACKSUITE_club_name'] ?? '' ) );
            update_option( 'TRACKSUITE_admin_email',       sanitize_email( $_POST['TRACKSUITE_admin_email'] ?? '' ) );
            update_option( 'TRACKSUITE_stripe_mode',       sanitize_text_field( $_POST['TRACKSUITE_stripe_mode'] ?? 'test' ) );
            update_option( 'TRACKSUITE_stripe_public_key', sanitize_text_field( $_POST['TRACKSUITE_stripe_public_key'] ?? '' ) );
            update_option( 'TRACKSUITE_stripe_secret_key', sanitize_text_field( $_POST['TRACKSUITE_stripe_secret_key'] ?? '' ) );
            add_settings_error( 'TRACKSUITE_settings', 'saved', __( 'Settings saved.', 'ts-membership' ), 'success' );
        }
        include TRACKSUITE_PLUGIN_DIR . 'admin/views/settings.php';
    }
}

