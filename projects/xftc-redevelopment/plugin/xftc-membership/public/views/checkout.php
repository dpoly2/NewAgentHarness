<?php
/**
 * Public View — Stripe Checkout Flow
 *
 * Shortcode: [TRACKSUITE_checkout]
 * Handles membership fee and travel fee payment initiation.
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 *
 * ─── STRIPE SETUP REQUIRED ───────────────────────────────────────────────────
 * This page will remain in placeholder state until Stripe keys are configured
 * in WP Admin → Xtreme Force → Payments.
 * ─────────────────────────────────────────────────────────────────────────────
 */

if ( ! defined( 'ABSPATH' ) ) exit;

$payments     = new TRACKSUITE_Payments();
$is_configured = $payments->is_configured();
$user         = wp_get_current_user();
$is_logged_in = is_user_logged_in();
?>

<div class="ts-checkout-wrap">

    <?php if ( ! $is_logged_in ) : ?>
        <!-- Not logged in -->
        <div class="ts-notice ts-notice-warning">
            <p>You must be logged in to complete a payment. <a href="<?php echo esc_url( wp_login_url( get_permalink() ) ); ?>">Log in here</a>.</p>
        </div>

    <?php elseif ( ! $is_configured ) : ?>
        <!-- Stripe not configured -->
        <div class="ts-notice ts-notice-info">
            <h3>💳 Online Payments Coming Soon</h3>
            <p>We're setting up our secure payment system. In the meantime, please contact your coach or administrator to arrange payment.</p>
            <p><strong>Xtreme Force Track Club</strong><br>
            📧 <a href="mailto:info@xtremeforcetrackclub.org">info@xtremeforcetrackclub.org</a></p>
        </div>

    <?php else : ?>
        <!-- Stripe configured — Checkout form -->
        <h2>Complete Your Payment</h2>

        <?php
        // TODO: Determine what the user is paying for
        // Pull pending membership or travel fees for this user
        // $pending = get_pending_fees_for_user( $user->ID );
        ?>

        <div class="ts-checkout-summary">
            <h3>Order Summary</h3>
            <table class="ts-order-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Athlete</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- TODO: Dynamically populate from pending membership/travel records -->
                    <tr>
                        <td colspan="3" style="text-align:center;padding:16px;">
                            <em>No pending fees found. Contact your administrator if you believe this is an error.</em>
                        </td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2"><strong>Total Due</strong></td>
                        <td><strong>$0.00</strong></td>
                    </tr>
                </tfoot>
            </table>
        </div>

        <!-- Stripe Checkout Button -->
        <div class="ts-checkout-actions">
            <button id="ts-stripe-checkout-btn" class="ts-btn ts-btn-primary" disabled>
                Pay with Card
            </button>
            <p class="ts-secure-notice">
                🔒 Payments are processed securely via <a href="https://stripe.com" target="_blank">Stripe</a>. Your card information is never stored on our servers.
            </p>
        </div>

        <!-- Stripe JS (to be initialized with publishable key) -->
        <script>
            // TODO: Initialize Stripe.js after keys are configured
            // const stripe = Stripe('<?php echo esc_js( $payments->get_publishable_key() ); ?>');
            //
            // document.getElementById('ts-stripe-checkout-btn').addEventListener('click', function() {
            //     fetch('/wp-json/xftc/v1/payments/checkout', {
            //         method: 'POST',
            //         headers: {
            //             'Content-Type': 'application/json',
            //             'X-WP-Nonce': xftcData.nonce
            //         },
            //         body: JSON.stringify({
            //             type: 'membership',
            //             reference_id: xftcData.membershipId,
            //             amount: xftcData.amountDue
            //         })
            //     })
            //     .then(res => res.json())
            //     .then(data => {
            //         return stripe.redirectToCheckout({ sessionId: data.session_id });
            //     })
            //     .catch(err => console.error('Checkout error:', err));
            // });

            console.log('XFTC Checkout: Stripe placeholder active. Configure API keys to enable payments.');
        </script>

    <?php endif; ?>

</div><!-- .ts-checkout-wrap -->

