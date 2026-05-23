<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap xftc-admin-wrap">
    <h1 class="xftc-page-title">
        <span class="dashicons dashicons-admin-generic"></span>
        <?php esc_html_e( 'XFTC Settings', 'xftc-membership' ); ?>
    </h1>

    <?php settings_errors( 'xftc_settings' ); ?>

    <form method="post">
        <?php wp_nonce_field( 'xftc_settings_nonce' ); ?>
        <table class="form-table">
            <tr>
                <th><?php esc_html_e( 'Club Name', 'xftc-membership' ); ?></th>
                <td><input type="text" name="xftc_club_name" value="<?php echo esc_attr( get_option( 'xftc_club_name' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Admin Email', 'xftc-membership' ); ?></th>
                <td><input type="email" name="xftc_admin_email" value="<?php echo esc_attr( get_option( 'xftc_admin_email' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Mode', 'xftc-membership' ); ?></th>
                <td>
                    <select name="xftc_stripe_mode">
                        <option value="test" <?php selected( get_option( 'xftc_stripe_mode' ), 'test' ); ?>><?php esc_html_e( 'Test', 'xftc-membership' ); ?></option>
                        <option value="live" <?php selected( get_option( 'xftc_stripe_mode' ), 'live' ); ?>><?php esc_html_e( 'Live', 'xftc-membership' ); ?></option>
                    </select>
                </td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Publishable Key', 'xftc-membership' ); ?></th>
                <td><input type="text" name="xftc_stripe_public_key" value="<?php echo esc_attr( get_option( 'xftc_stripe_public_key' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Secret Key', 'xftc-membership' ); ?></th>
                <td><input type="password" name="xftc_stripe_secret_key" value="<?php echo esc_attr( get_option( 'xftc_stripe_secret_key' ) ); ?>" class="regular-text"></td>
            </tr>
        </table>
        <p class="submit">
            <input type="submit" name="xftc_save_settings" class="button-primary" value="<?php esc_attr_e( 'Save Settings', 'xftc-membership' ); ?>">
        </p>
    </form>
</div>
