<?php
/**
 * Front-end shortcodes and public-facing hooks.
 *
 * Shortcodes:
 *  [xftc_register] — Parent registration form
 *  [xftc_portal]   — Member portal dashboard
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Public {

    public function init() {
        add_shortcode( 'xftc_register', [ $this, 'shortcode_register' ] );
        add_shortcode( 'xftc_portal',   [ $this, 'shortcode_portal' ] );
        add_action( 'wp_enqueue_scripts', [ $this, 'enqueue_assets' ] );
    }

    /**
     * Enqueue public CSS and JS.
     */
    public function enqueue_assets() {
        wp_enqueue_style(
            'xftc-public',
            XFTC_PLUGIN_URL . 'public/assets/public.css',
            [],
            XFTC_VERSION
        );
        wp_enqueue_script(
            'xftc-public',
            XFTC_PLUGIN_URL . 'public/assets/public.js',
            [ 'jquery' ],
            XFTC_VERSION,
            true
        );
        wp_localize_script( 'xftc-public', 'xftcPublic', [
            'ajaxUrl'         => admin_url( 'admin-ajax.php' ),
            'registerNonce'   => wp_create_nonce( 'xftc_register_nonce' ),
            'athleteNonce'    => wp_create_nonce( 'xftc_athlete_nonce' ),
            'membershipNonce' => wp_create_nonce( 'xftc_membership_nonce' ),
        ] );
    }

    /**
     * [xftc_register] — Render parent registration form.
     *
     * @return string HTML
     */
    public function shortcode_register(): string {
        if ( is_user_logged_in() ) {
            $portal_url = home_url( '/member-portal/' );
            return '<p>' . sprintf(
                __( 'You are already logged in. <a href="%s">Go to your portal →</a>', 'xftc-membership' ),
                esc_url( $portal_url )
            ) . '</p>';
        }

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/register.php';
        return ob_get_clean();
    }

    /**
     * [xftc_portal] — Render the member portal.
     *
     * @return string HTML
     */
    public function shortcode_portal(): string {
        if ( ! is_user_logged_in() ) {
            return '<p>' . sprintf(
                __( 'Please <a href="%s">log in</a> to access your portal.', 'xftc-membership' ),
                esc_url( wp_login_url( get_permalink() ) )
            ) . '</p>';
        }

        $user      = wp_get_current_user();
        $members   = new XFTC_Members();
        $athletes  = $members->get_by_parent( $user->ID );
        $seasons   = new XFTC_Seasons();
        $active    = $seasons->get_active();

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/portal.php';
        return ob_get_clean();
    }
}
