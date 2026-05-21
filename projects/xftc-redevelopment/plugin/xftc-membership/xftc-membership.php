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
 * Text Domain:     ts-membership
 * Domain Path:     /languages
 */

defined( 'ABSPATH' ) || exit;

// ─── Constants ───────────────────────────────────────────────────────────────
define( 'TRACKSUITE_VERSION',     '0.2.0' );
define( 'TRACKSUITE_PLUGIN_FILE', __FILE__ );
define( 'TRACKSUITE_PLUGIN_DIR',  plugin_dir_path( __FILE__ ) );
define( 'TRACKSUITE_PLUGIN_URL',  plugin_dir_url( __FILE__ ) );
define( 'TRACKSUITE_PLUGIN_BASE', plugin_basename( __FILE__ ) );

// ─── Activator / Deactivator must load immediately (before activation hook fires) ──
require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-activator.php';
require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-deactivator.php';

// ─── Activation / Deactivation hooks ─────────────────────────────────────────
register_activation_hook(   __FILE__, [ 'TRACKSUITE_Activator',   'activate'   ] );
register_deactivation_hook( __FILE__, [ 'TRACKSUITE_Deactivator', 'deactivate' ] );

// ─── Autoloader (for runtime class resolution) ────────────────────────────────
spl_autoload_register( function ( $class ) {
    if ( strncmp( 'TRACKSUITE_', $class, 5 ) !== 0 ) {
        return;
    }
    $relative = strtolower( str_replace( [ 'TRACKSUITE_', '_' ], [ '', '-' ], $class ) );
    $paths = [
        TRACKSUITE_PLUGIN_DIR . "includes/class-{$relative}.php",
        TRACKSUITE_PLUGIN_DIR . "admin/class-{$relative}.php",
        TRACKSUITE_PLUGIN_DIR . "public/class-{$relative}.php",
        TRACKSUITE_PLUGIN_DIR . "api/class-{$relative}.php",
    ];
    foreach ( $paths as $path ) {
        if ( file_exists( $path ) ) {
            require_once $path;
            return;
        }
    }
} );

// ─── Bootstrap (runs after all plugins are loaded) ───────────────────────────
function TRACKSUITE_run() {
    // Core includes
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-roles.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-members.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-seasons.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-registration.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-emails.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-meets.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-results.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-travel.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-payroll.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'includes/class-ts-payments.php';

    // Admin & public layers
    require_once TRACKSUITE_PLUGIN_DIR . 'admin/class-ts-admin.php';
    require_once TRACKSUITE_PLUGIN_DIR . 'public/class-ts-public.php';

    // REST API
    require_once TRACKSUITE_PLUGIN_DIR . 'api/class-ts-rest-api.php';

    // Init roles
    $roles = new TRACKSUITE_Roles();
    $roles->init();

    // Init REST API
    new TRACKSUITE_REST_API();

    // Init admin
    $admin = new TRACKSUITE_Admin();
    if ( is_admin() ) {
        $admin->init();
    }

    // Init public
    $public = new TRACKSUITE_Public();
    $public->init();
}
add_action( 'plugins_loaded', 'TRACKSUITE_run' );

