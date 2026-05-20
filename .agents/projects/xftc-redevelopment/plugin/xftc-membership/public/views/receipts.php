<?php
/**
 * Public View — Payment Receipts & Order History
 *
 * Shortcode: [xftc_receipts]
 * Displays a logged-in parent's payment history and receipt details.
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

if ( ! is_user_logged_in() ) {
    echo '<p>You must be <a href="' . esc_url( wp_login_url( get_permalink() ) ) . '">logged in</a> to view your receipts.</p>';
    return;
}

$user_id  = get_current_user_id();
$payments = new XFTC_Payments();
$history  = $payments->get_payment_history( $user_id );
?>

<div class="xftc-receipts-wrap">
    <h2>Payment History</h2>

    <?php if ( empty( $history ) ) : ?>
        <div class="xftc-notice xftc-notice-info">
            <p>No payments on record yet. Once you complete registration and pay your fees, your receipts will appear here.</p>
        </div>
    <?php else : ?>
        <table class="xftc-receipts-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Status</th>
                    <th>Receipt</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ( $history as $record ) : ?>
                    <tr>
                        <td><?php echo esc_html( date( 'M j, Y', strtotime( $record['created_at'] ) ) ); ?></td>
                        <td><?php echo esc_html( ucfirst( $record['reference_type'] ) . ' Fee' ); ?></td>
                        <td>$<?php echo number_format( $record['amount'], 2 ); ?></td>
                        <td><?php echo esc_html( strtoupper( $record['gateway'] ) ); ?></td>
                        <td>
                            <span class="xftc-status xftc-status-<?php echo esc_attr( $record['status'] ); ?>">
                                <?php echo esc_html( ucfirst( $record['status'] ) ); ?>
                            </span>
                        </td>
                        <td>
                            <?php if ( $record['status'] === 'completed' && $record['gateway'] === 'stripe' ) : ?>
                                <!-- TODO: Link to Stripe receipt URL or generate PDF -->
                                <a href="#" class="xftc-receipt-link">View Receipt</a>
                            <?php else : ?>
                                <span class="xftc-muted">—</span>
                            <?php endif; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    <?php endif; ?>

    <div class="xftc-receipts-footer">
        <p class="xftc-secure-notice">
            🔒 Payments processed by <a href="https://stripe.com" target="_blank">Stripe</a>.
            Questions? Contact us at <a href="mailto:info@xtremeforcetrackclub.org">info@xtremeforcetrackclub.org</a>
        </p>
    </div>
</div><!-- .xftc-receipts-wrap -->
