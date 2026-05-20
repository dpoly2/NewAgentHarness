<?php
/**
 * Admin View — Payment History & Settings
 *
 * WP Admin → Xtreme Force → Payments
 *
 * @package XFTC_Membership
 * @since   0.2.0
 *
 * ─── STRIPE SETUP REQUIRED ───────────────────────────────────────────────────
 * Enter your Stripe API keys below to activate payment processing.
 * Get your keys at: https://dashboard.stripe.com/apikeys
 * ─────────────────────────────────────────────────────────────────────────────
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// Save settings on form submit
if ( isset( $_POST['xftc_payments_nonce'] ) && wp_verify_nonce( $_POST['xftc_payments_nonce'], 'xftc_save_payment_settings' ) ) {
    update_option( 'xftc_stripe_test_mode',              isset( $_POST['xftc_stripe_test_mode'] ) ? 1 : 0 );
    update_option( 'xftc_stripe_test_publishable_key',   sanitize_text_field( $_POST['xftc_stripe_test_publishable_key'] ?? '' ) );
    update_option( 'xftc_stripe_test_secret_key',        sanitize_text_field( $_POST['xftc_stripe_test_secret_key'] ?? '' ) );
    update_option( 'xftc_stripe_live_publishable_key',   sanitize_text_field( $_POST['xftc_stripe_live_publishable_key'] ?? '' ) );
    update_option( 'xftc_stripe_live_secret_key',        sanitize_text_field( $_POST['xftc_stripe_live_secret_key'] ?? '' ) );
    update_option( 'xftc_stripe_webhook_secret',         sanitize_text_field( $_POST['xftc_stripe_webhook_secret'] ?? '' ) );

    echo '<div class="notice notice-success"><p><strong>Payment settings saved.</strong></p></div>';
}

// Current values
$test_mode          = get_option( 'xftc_stripe_test_mode', 1 );
$test_pub_key       = get_option( 'xftc_stripe_test_publishable_key', '' );
$test_sec_key       = get_option( 'xftc_stripe_test_secret_key', '' );
$live_pub_key       = get_option( 'xftc_stripe_live_publishable_key', '' );
$live_sec_key       = get_option( 'xftc_stripe_live_secret_key', '' );
$webhook_secret     = get_option( 'xftc_stripe_webhook_secret', '' );
$is_configured      = ! empty( $test_mode ? $test_sec_key : $live_sec_key );
?>

<div class="wrap xftc-admin-payments">
    <h1>💳 Payments</h1>

    <!-- Status Banner -->
    <?php if ( $is_configured ) : ?>
        <div class="notice notice-success inline">
            <p>✅ Stripe is <strong>configured</strong> and running in <strong><?php echo $test_mode ? 'TEST' : 'LIVE'; ?> mode</strong>.</p>
        </div>
    <?php else : ?>
        <div class="notice notice-warning inline">
            <p>⚠️ <strong>Stripe is not yet configured.</strong> Enter your API keys below to enable payment processing.</p>
            <p>Get your keys at <a href="https://dashboard.stripe.com/apikeys" target="_blank">dashboard.stripe.com/apikeys</a></p>
        </div>
    <?php endif; ?>

    <hr>

    <!-- Stripe Settings Form -->
    <h2>Stripe API Configuration</h2>
    <form method="post" action="">
        <?php wp_nonce_field( 'xftc_save_payment_settings', 'xftc_payments_nonce' ); ?>

        <table class="form-table">
            <tr>
                <th scope="row">Mode</th>
                <td>
                    <label>
                        <input type="checkbox" name="xftc_stripe_test_mode" value="1" <?php checked( $test_mode, 1 ); ?>>
                        <strong>Test Mode</strong> — Use test keys (no real charges)
                    </label>
                    <p class="description">Uncheck this to switch to Live mode. Only disable test mode when you're ready to accept real payments.</p>
                </td>
            </tr>
        </table>

        <h3>🧪 Test Keys <span style="font-weight:normal;font-size:13px;">(pk_test_... / sk_test_...)</span></h3>
        <table class="form-table">
            <tr>
                <th scope="row"><label for="xftc_stripe_test_publishable_key">Test Publishable Key</label></th>
                <td>
                    <input type="text" id="xftc_stripe_test_publishable_key" name="xftc_stripe_test_publishable_key"
                        value="<?php echo esc_attr( $test_pub_key ); ?>"
                        placeholder="pk_test_..."
                        class="regular-text">
                    <p class="description">Safe to expose on the front end. Used to initialize Stripe.js.</p>
                </td>
            </tr>
            <tr>
                <th scope="row"><label for="xftc_stripe_test_secret_key">Test Secret Key</label></th>
                <td>
                    <input type="password" id="xftc_stripe_test_secret_key" name="xftc_stripe_test_secret_key"
                        value="<?php echo esc_attr( $test_sec_key ); ?>"
                        placeholder="sk_test_..."
                        class="regular-text">
                    <p class="description">⚠️ Never expose this key on the front end. Server-side only.</p>
                </td>
            </tr>
        </table>

        <h3>🚀 Live Keys <span style="font-weight:normal;font-size:13px;">(pk_live_... / sk_live_...)</span></h3>
        <table class="form-table">
            <tr>
                <th scope="row"><label for="xftc_stripe_live_publishable_key">Live Publishable Key</label></th>
                <td>
                    <input type="text" id="xftc_stripe_live_publishable_key" name="xftc_stripe_live_publishable_key"
                        value="<?php echo esc_attr( $live_pub_key ); ?>"
                        placeholder="pk_live_..."
                        class="regular-text">
                </td>
            </tr>
            <tr>
                <th scope="row"><label for="xftc_stripe_live_secret_key">Live Secret Key</label></th>
                <td>
                    <input type="password" id="xftc_stripe_live_secret_key" name="xftc_stripe_live_secret_key"
                        value="<?php echo esc_attr( $live_sec_key ); ?>"
                        placeholder="sk_live_..."
                        class="regular-text">
                    <p class="description">⚠️ Never expose this key on the front end. Server-side only.</p>
                </td>
            </tr>
        </table>

        <h3>🔗 Webhook Configuration</h3>
        <table class="form-table">
            <tr>
                <th scope="row">Webhook Endpoint URL</th>
                <td>
                    <code><?php echo esc_url( get_rest_url( null, 'xftc/v1/payments/webhook' ) ); ?></code>
                    <p class="description">Add this URL in your <a href="https://dashboard.stripe.com/webhooks" target="_blank">Stripe Webhooks dashboard</a>. Listen for: <code>checkout.session.completed</code>, <code>payment_intent.payment_failed</code></p>
                </td>
            </tr>
            <tr>
                <th scope="row"><label for="xftc_stripe_webhook_secret">Webhook Signing Secret</label></th>
                <td>
                    <input type="password" id="xftc_stripe_webhook_secret" name="xftc_stripe_webhook_secret"
                        value="<?php echo esc_attr( $webhook_secret ); ?>"
                        placeholder="whsec_..."
                        class="regular-text">
                    <p class="description">Found in your Stripe Webhooks dashboard after creating the endpoint.</p>
                </td>
            </tr>
        </table>

        <?php submit_button( 'Save Payment Settings' ); ?>
    </form>

    <hr>

    <!-- Payment History Table (Placeholder) -->
    <h2>Payment History</h2>
    <p class="description">Recent transactions will appear here once Stripe is configured and payments are processed.</p>

    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th>Date</th>
                <th>Payer</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Gateway</th>
                <th>Transaction ID</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <?php
            // TODO: Load from wp_xftc_payments when Stripe is active
            global $wpdb;
            $payments = []; // $wpdb->get_results("SELECT * FROM {$wpdb->prefix}xftc_payments ORDER BY created_at DESC LIMIT 50");

            if ( empty( $payments ) ) : ?>
                <tr>
                    <td colspan="7" style="text-align:center;padding:20px;">
                        <em>No payment records yet. Configure Stripe above to begin accepting payments.</em>
                    </td>
                </tr>
            <?php else :
                foreach ( $payments as $payment ) : ?>
                    <tr>
                        <td><?php echo esc_html( $payment->created_at ); ?></td>
                        <td><?php echo esc_html( get_userdata( $payment->user_id )->display_name ?? '—' ); ?></td>
                        <td><?php echo esc_html( ucfirst( $payment->reference_type ) ); ?></td>
                        <td>$<?php echo number_format( $payment->amount, 2 ); ?></td>
                        <td><?php echo esc_html( strtoupper( $payment->gateway ) ); ?></td>
                        <td><code><?php echo esc_html( $payment->transaction_id ); ?></code></td>
                        <td>
                            <span class="xftc-status xftc-status-<?php echo esc_attr( $payment->status ); ?>">
                                <?php echo esc_html( ucfirst( $payment->status ) ); ?>
                            </span>
                        </td>
                    </tr>
                <?php endforeach;
            endif; ?>
        </tbody>
    </table>

    <!-- Manual Payment Entry (Placeholder) -->
    <hr>
    <h2>Record Manual Payment</h2>
    <p class="description">Use this to record cash or check payments received outside of Stripe.</p>

    <form method="post" action="">
        <?php wp_nonce_field( 'xftc_manual_payment', 'xftc_manual_payment_nonce' ); ?>
        <table class="form-table">
            <tr>
                <th><label for="manual_user">Parent / User</label></th>
                <td>
                    <?php
                    // TODO: Populate with actual XFTC parent users
                    wp_dropdown_users([
                        'name'             => 'manual_user_id',
                        'id'               => 'manual_user',
                        'show_option_none' => '— Select Parent —',
                        'role'             => 'xftc_parent',
                    ]);
                    ?>
                </td>
            </tr>
            <tr>
                <th><label for="manual_type">Payment Type</label></th>
                <td>
                    <select name="manual_type" id="manual_type">
                        <option value="membership">Membership Fee</option>
                        <option value="travel">Travel Fee</option>
                        <option value="other">Other</option>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label for="manual_amount">Amount ($)</label></th>
                <td><input type="number" name="manual_amount" id="manual_amount" step="0.01" min="0" class="small-text" placeholder="0.00"></td>
            </tr>
            <tr>
                <th><label for="manual_notes">Notes</label></th>
                <td><input type="text" name="manual_notes" id="manual_notes" class="regular-text" placeholder="e.g. Check #1042, Cash received at practice"></td>
            </tr>
        </table>
        <?php submit_button( 'Record Payment', 'secondary' ); ?>
    </form>

</div><!-- .xftc-admin-payments -->
