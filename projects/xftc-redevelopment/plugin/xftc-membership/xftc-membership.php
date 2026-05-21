<?php
/**
 * Plugin Name:     XFTC Membership
 * Plugin URI:      https://xtremeforcetrackclub.org
 * Description:     Complete membership management system for Xtreme Force Track Club — registration, seasons, meets, results, travel, payroll, and payments.
 * Version:         0.2.0
 * Author:          Xtreme Force Track Club
 * Author URI:      https://xtremeforcetrackclub.org
 * License:         GPL-2.0+
 * License URI:     https://www.gnu.org/licenses/gpl-2.0.txt
 * Text Domain:     xftc-membership
 * Domain Path:     /languages
 */

defined( 'ABSPATH' ) || exit;

// ─── Constants ───────────────────────────────────────────────────────────────
define( 'XFTC_VERSION',     '0.2.0' );
define( 'XFTC_PLUGIN_FILE', __FILE__ );
define( 'XFTC_PLUGIN_DIR',  plugin_dir_path( __FILE__ ) );
define( 'XFTC_PLUGIN_URL',  plugin_dir_url( __FILE__ ) );
define( 'XFTC_PLUGIN_BASE', plugin_basename( __FILE__ ) );

// ─── Activator / Deactivator must load immediately (before activation hook fires) ──
require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-activator.php';
require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-deactivator.php';

// ─── Activation / Deactivation hooks ─────────────────────────────────────────
register_activation_hook(   __FILE__, [ 'XFTC_Activator',   'activate'   ] );
register_deactivation_hook( __FILE__, [ 'XFTC_Deactivator', 'deactivate' ] );

// ─── Autoloader (for runtime class resolution) ────────────────────────────────
spl_autoload_register( function ( $class ) {
    if ( strncmp( 'XFTC_', $class, 5 ) !== 0 ) {
        return;
    }
    $relative = strtolower( str_replace( [ 'XFTC_', '_' ], [ '', '-' ], $class ) );
    $paths = [
        XFTC_PLUGIN_DIR . "includes/class-{$relative}.php",
        XFTC_PLUGIN_DIR . "admin/class-{$relative}.php",
        XFTC_PLUGIN_DIR . "public/class-{$relative}.php",
        XFTC_PLUGIN_DIR . "api/class-{$relative}.php",
    ];
    foreach ( $paths as $path ) {
        if ( file_exists( $path ) ) {
            require_once $path;
            return;
        }
    }
} );

// ─── Bootstrap (runs after all plugins are loaded) ───────────────────────────
function xftc_run() {
    // Core includes
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-roles.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-members.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-seasons.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-registration.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-emails.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-meets.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-results.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-travel.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-payroll.php';
    require_once XFTC_PLUGIN_DIR . 'includes/class-xftc-payments.php';

    // Admin & public layers
    require_once XFTC_PLUGIN_DIR . 'admin/class-xftc-admin.php';
    require_once XFTC_PLUGIN_DIR . 'public/class-xftc-public.php';

    // REST API
    require_once XFTC_PLUGIN_DIR . 'api/class-xftc-rest-api.php';

    // Init roles
    $roles = new XFTC_Roles();
    $roles->init();

    // Init REST API
    new XFTC_REST_API();

    // Init admin
    $admin = new XFTC_Admin();
    if ( is_admin() ) {
        $admin->init();
    }

    // Init public
    $public = new XFTC_Public();
    $public->init();
}
add_action( 'plugins_loaded', 'xftc_run' );
