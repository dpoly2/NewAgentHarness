<?php
/**
 * Public view — Payments & Travel (used by [TRACKSUITE_my_payments] and [TRACKSUITE_my_travel])
 * Variables: $payments, $travel, $atts
 * @package TRACKSUITE_Membership
 */
defined( 'ABSPATH' ) || exit;
?>

<?php // ── Payments view ───────────────────────────────────────────────────────
if ( isset( $payments ) ) :
    if ( empty( $payments ) ) : ?>
        <p class="ts-empty">No payment history yet.</p>
    <?php else : ?>
        <div class="ts-table-wrap">
            <table class="ts-table">
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
                        'completed' => 'ts-badge--success',
                        'pending'   => 'ts-badge--warning',
                        'failed'    => 'ts-badge--danger',
                        'refunded'  => 'ts-badge--info',
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
                    <td><span class="ts-badge <?php echo esc_attr( $status_class ); ?>"><?php echo esc_html( ucfirst( $p['status'] ?? '' ) ); ?></span></td>
                    <td><?php echo esc_html( ucfirst( $p['gateway'] ?? 'Manual' ) ); ?></td>
                    <td>
                        <?php if ( ! empty( $p['transaction_id'] ) ) : ?>
                            <a href="<?php echo esc_url( home_url( '/receipt/?txn=' . $p['transaction_id'] ) ); ?>"
                               class="ts-link" target="_blank">
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
        <p class="ts-empty">No travel bookings on record.</p>
    <?php else : ?>
        <div class="ts-table-wrap">
            <table class="ts-table">
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
                        ? 'ts-badge--success'
                        : ( $t['payment_status'] === 'refunded' ? 'ts-badge--info' : 'ts-badge--warning' );
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
                    <td><span class="ts-badge <?php echo esc_attr( $status_class ); ?>"><?php echo esc_html( ucfirst( $t['payment_status'] ?? '' ) ); ?></span></td>
                </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>
<?php endif; ?>

