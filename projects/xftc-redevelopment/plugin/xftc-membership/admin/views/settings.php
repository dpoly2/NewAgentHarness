<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap ts-admin-wrap">
    <h1 class="ts-page-title">
        <span class="dashicons dashicons-admin-generic"></span>
        <?php esc_html_e( 'XFTC Settings', 'ts-membership' ); ?>
    </h1>

    <?php settings_errors( 'TRACKSUITE_settings' ); ?>

    <form method="post">
        <?php wp_nonce_field( 'TRACKSUITE_settings_nonce' ); ?>
        <table class="form-table">
            <tr>
                <th><?php esc_html_e( 'Club Name', 'ts-membership' ); ?></th>
                <td><input type="text" name="TRACKSUITE_club_name" value="<?php echo esc_attr( get_option( 'TRACKSUITE_club_name' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Admin Email', 'ts-membership' ); ?></th>
                <td><input type="email" name="TRACKSUITE_admin_email" value="<?php echo esc_attr( get_option( 'TRACKSUITE_admin_email' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Mode', 'ts-membership' ); ?></th>
                <td>
                    <select name="TRACKSUITE_stripe_mode">
                        <option value="test" <?php selected( get_option( 'TRACKSUITE_stripe_mode' ), 'test' ); ?>><?php esc_html_e( 'Test', 'ts-membership' ); ?></option>
                        <option value="live" <?php selected( get_option( 'TRACKSUITE_stripe_mode' ), 'live' ); ?>><?php esc_html_e( 'Live', 'ts-membership' ); ?></option>
                    </select>
                </td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Publishable Key', 'ts-membership' ); ?></th>
                <td><input type="text" name="TRACKSUITE_stripe_public_key" value="<?php echo esc_attr( get_option( 'TRACKSUITE_stripe_public_key' ) ); ?>" class="regular-text"></td>
            </tr>
            <tr>
                <th><?php esc_html_e( 'Stripe Secret Key', 'ts-membership' ); ?></th>
                <td><input type="password" name="TRACKSUITE_stripe_secret_key" value="<?php echo esc_attr( get_option( 'TRACKSUITE_stripe_secret_key' ) ); ?>" class="regular-text"></td>
            </tr>
        </table>
        <p class="submit">
            <input type="submit" name="TRACKSUITE_save_settings" class="button-primary" value="<?php esc_attr_e( 'Save Settings', 'ts-membership' ); ?>">
        </p>
    </form>
</div>

