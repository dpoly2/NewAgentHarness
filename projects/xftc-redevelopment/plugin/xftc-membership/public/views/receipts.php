<?php
/**
 * Public view — Payments & Travel (used by [xftc_my_payments] and [xftc_my_travel])
 * Variables: $payments, $travel, $atts
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;
?>

<?php // ── Payments view ───────────────────────────────────────────────────────
if ( isset( $payments ) ) :
    if ( empty( $payments ) ) : ?>
        <p class="xftc-empty">No payment history yet.</p>
    <?php else : ?>
        <div class="xftc-table-wrap">
            <table class="xftc-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Method</th>
                        <th>Receipt</th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $payments as $p ) :
                    $status_class = [
                        'completed' => 'xftc-badge--success',
                        'pending'   => 'xftc-badge--warning',
                        'failed'    => 'xftc-badge--danger',
                        'refunded'  => 'xftc-badge--info',
                    ][ $p['status'] ] ?? '';
                    $types = [
                        'membership' => 'Membership',
                        'travel'     => 'Travel',
                        'uniform'    => 'Uniform',
                        'other'      => 'Other',
                    ];
                ?>
                <tr>
                    <td><?php echo ! empty( $p['created_at'] ) ? esc_html( date( 'M j, Y', strtotime( $p['created_at'] ) ) ) : '—'; ?></td>
                    <td><?php echo esc_html( $types[ $p['reference_type'] ] ?? ucfirst( $p['reference_type'] ?? '' ) ); ?></td>
                    <td><strong>$<?php echo esc_html( number_format( (float) ( $p['amount'] ?? 0 ), 2 ) ); ?></strong></td>
                    <td><span class="xftc-badge <?php echo esc_attr( $status_class ); ?>"><?php echo esc_html( ucfirst( $p['status'] ?? '' ) ); ?></span></td>
                    <td><?php echo esc_html( ucfirst( $p['gateway'] ?? 'Manual' ) ); ?></td>
                    <td>
                        <?php if ( ! empty( $p['transaction_id'] ) ) : ?>
                            <a href="<?php echo esc_url( home_url( '/receipt/?txn=' . $p['transaction_id'] ) ); ?>"
                               class="xftc-link" target="_blank">
                                🧾 View
                            </a>
                        <?php else : ?>
                            —
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>
<?php endif; ?>


<?php // ── Travel view ─────────────────────────────────────────────────────────
if ( isset( $travel ) ) :
    if ( empty( $travel ) ) : ?>
        <p class="xftc-empty">No travel bookings on record.</p>
    <?php else : ?>
        <div class="xftc-table-wrap">
            <table class="xftc-table">
                <thead>
                    <tr>
                        <th>Athlete</th>
                        <th>Meet</th>
                        <th>Date</th>
                        <th>Location</th>
                        <th>Type</th>
                        <th>Bus Seat</th>
                        <th>Hotel Room</th>
                        <th>Fee</th>
                        <th>Paid</th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $travel as $t ) :
                    $status_class = $t['payment_status'] === 'paid'
                        ? 'xftc-badge--success'
                        : ( $t['payment_status'] === 'refunded' ? 'xftc-badge--info' : 'xftc-badge--warning' );
                    $types = [ 'bus' => '🚌 Bus', 'hotel' => '🏨 Hotel', 'both' => '🚌 Bus + 🏨 Hotel' ];
                ?>
                <tr>
                    <td><?php echo esc_html( $t['athlete_name'] ?? '—' ); ?></td>
                    <td><?php echo esc_html( $t['meet_name'] ?? '—' ); ?></td>
                    <td><?php echo ! empty( $t['meet_date'] ) ? esc_html( date( 'M j, Y', strtotime( $t['meet_date'] ) ) ) : '—'; ?></td>
                    <td><?php echo esc_html( $t['location'] ?? '—' ); ?></td>
                    <td><?php echo esc_html( $types[ $t['travel_type'] ] ?? ucfirst( $t['travel_type'] ?? '' ) ); ?></td>
                    <td><?php echo esc_html( $t['bus_seat'] ?? '—' ); ?></td>
                    <td><?php echo esc_html( $t['hotel_room'] ?? '—' ); ?></td>
                    <td>$<?php echo esc_html( number_format( (float) ( $t['travel_fee'] ?? 0 ), 2 ) ); ?></td>
                    <td><span class="xftc-badge <?php echo esc_attr( $status_class ); ?>"><?php echo esc_html( ucfirst( $t['payment_status'] ?? '' ) ); ?></span></td>
                </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>
<?php endif; ?>
