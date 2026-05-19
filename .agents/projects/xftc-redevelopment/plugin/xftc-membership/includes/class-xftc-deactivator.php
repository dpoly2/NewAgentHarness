<?php
/**
 * Fired during plugin deactivation.
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Deactivator {

    /**
     * Run on plugin deactivation.
     * Note: DB tables and data are preserved on deactivation.
     * Tables are only dropped on full uninstall (uninstall.php).
     */
    public static function deactivate() {
        flush_rewrite_rules();
    }
}
