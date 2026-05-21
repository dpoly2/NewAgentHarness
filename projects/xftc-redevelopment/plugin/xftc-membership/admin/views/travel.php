<?php
/**
 * Admin View — Travel & Logistics
 * WP Admin → Xtreme Force → Travel
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

$travel_mgr = new TRACKSUITE_Travel();
$meets_mgr  = new TRACKSUITE_Meets();

if ( isset( $_GET['export_manifest'] ) ) {
    $travel_mgr->export_manifest_csv( (int) $_GET['export_manifest'] );
}
if ( isset( $_GET['mark_paid'] ) && check_admin_referer( 'TRACKSUITE_travel_paid' ) ) {
    $travel_mgr->mark_paid( (int) $_GET['mark_paid'] );
    echo '<div class="notice notice-success"><p>Marked as paid.</p></div>';
}
if ( isset( $_POST['TRACKSUITE_travel_nonce'] ) && wp_verify_nonce( $_POST['TRACKSUITE_travel_nonce'], 'TRACKSUITE_save_travel' ) ) {
    if ( ! empty( $_POST['assign_seat'] ) ) {
        $travel_mgr->assign_seat( (int) $_POST['booking_id'], sanitize_text_field( $_POST['bus_seat'] ) );
        $travel_mgr->assign_room( (int) $_POST['booking_id'], sanitize_text_field( $_POST['hotel_room'] ) );
        echo '<div class="notice notice-success"><p>Assignment updated.</p></div>';
    }
}

$selected_meet = isset( $_GET['meet_id'] ) ? (int) $_GET['meet_id'] : 0;
$meets         = $meets_mgr->get_all_meets();
$bookings      = $selected_meet ? $travel_mgr->get_meet_travel( $selected_meet ) : [];
$totals        = $selected_meet ? $travel_mgr->get_meet_travel_totals( $selected_meet ) : [];
?>

<div class="wrap ts-admin-travel">
    <h1>🚌 Travel & Logistics</h1>

    <!-- Meet Selector -->
    <form method="get" style="margin-bottom:16px;">
        <input type="hidden" name="page" value="ts-travel">
        <label><strong>View Travel For:</strong>
            <select name="meet_id" onchange="this.form.submit()">
                <option value="">— Select Meet —</option>
                <?php foreach ( $meets as $m ) : ?>
                    <option value="<?php echo $m['id']; ?>" <?php selected( $selected_meet, $m['id'] ); ?>>
                        <?php echo esc_html( $m['name'] . ' — ' . date( 'M j, Y', strtotime( $m['meet_date'] ) ) ); ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </label>
        <?php if ( $selected_meet ) : ?>
            <a href="?page=ts-travel&meet_id=<?php echo $selected_meet; ?>&export_manifest=<?php echo $selected_meet; ?>" class="button">📥 Export Manifest</a>
        <?php endif; ?>
    </form>

    <?php if ( $selected_meet && ! empty( $totals ) ) : ?>
    <!-- Totals Summary -->
    <div class="ts-stats-row" style="display:flex;gap:16px;margin-bottom:16px;">
        <div class="ts-stat-card"><strong><?php echo $totals['total_bookings']; ?></strong><span>Total Bookings</span></div>
        <div class="ts-stat-card"><strong>$<?php echo number_format( $totals['total_due'], 2 ); ?></strong><span>Total Due</span></div>
        <div class="ts-stat-card"><strong>$<?php echo number_format( $totals['total_paid'], 2 ); ?></strong><span>Collected</span></div>
        <div class="ts-stat-card"><strong style="color:#c0392b;">$<?php echo number_format( $totals['total_unpaid'], 2 ); ?></strong><span>Outstanding</span></div>
    </div>

    <!-- Bookings Table -->
    <table class="wp-list-table widefat fixed striped">
        <thead><tr><th>Athlete</th><th>Team Level</th><th>Type</th><th>Bus Seat</th><th>Hotel Room</th><th>Fee</th><th>Payment</th><th>Actions</th></tr></thead>
        <tbody>
        <?php if ( empty( $bookings ) ) : ?>
            <tr><td colspan="8" style="text-align:center;"><em>No travel bookings for this meet.</em></td></tr>
        <?php else : foreach ( $bookings as $b ) : ?>
            <tr>
                <td><?php echo esc_html( $b['first_name'] . ' ' . $b['last_name'] ); ?></td>
                <td><?php echo esc_html( $b['team_level'] ); ?></td>
                <td><?php echo esc_html( strtoupper( $b['travel_type'] ) ); ?></td>
                <td><?php echo esc_html( $b['bus_seat'] ?: '—' ); ?></td>
                <td><?php echo esc_html( $b['hotel_room'] ?: '—' ); ?></td>
                <td>$<?php echo number_format( $b['travel_fee'], 2 ); ?></td>
                <td><span class="ts-status ts-status-<?php echo esc_attr( $b['payment_status'] ); ?>"><?php echo esc_html( ucfirst( $b['payment_status'] ) ); ?></span></td>
                <td>
                    <?php if ( $b['payment_status'] === 'unpaid' ) : ?>
                        <a href="?page=ts-travel&meet_id=<?php echo $selected_meet; ?>&mark_paid=<?php echo $b['id']; ?>&<?php echo wp_create_nonce( 'TRACKSUITE_travel_paid' ); ?>">Mark Paid</a> |
                    <?php endif; ?>
                    <a href="#assign-<?php echo $b['id']; ?>">Assign Seat/Room</a>
                </td>
            </tr>
            <!-- Inline assignment form -->
            <tr id="assign-<?php echo $b['id']; ?>" style="display:none;">
                <td colspan="8">
                    <form method="post" style="display:flex;gap:8px;align-items:center;padding:8px;">
                        <?php wp_nonce_field( 'TRACKSUITE_save_travel', 'TRACKSUITE_travel_nonce' ); ?>
                        <input type="hidden" name="booking_id" value="<?php echo $b['id']; ?>">
                        <input type="hidden" name="assign_seat" value="1">
                        <label>Bus Seat: <input type="text" name="bus_seat" value="<?php echo esc_attr( $b['bus_seat'] ); ?>" style="width:60px;"></label>
                        <label>Hotel Room: <input type="text" name="hotel_room" value="<?php echo esc_attr( $b['hotel_room'] ); ?>" style="width:80px;"></label>
                        <button type="submit" class="button button-small">Save</button>
                    </form>
                </td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>
    <?php endif; ?>

    <hr>

    <!-- Travel Fee Settings -->
    <h2>Travel Fee Settings</h2>
    <form method="post" action="options.php">
        <?php settings_fields( 'TRACKSUITE_travel_settings' ); ?>
        <table class="form-table">
            <tr>
                <th>Bus Fee ($)</th>
                <td><input type="number" step="0.01" name="TRACKSUITE_travel_fee_bus" value="<?php echo esc_attr( get_option( 'TRACKSUITE_travel_fee_bus', '25.00' ) ); ?>" class="small-text"></td>
            </tr>
            <tr>
                <th>Hotel Fee ($)</th>
                <td><input type="number" step="0.01" name="TRACKSUITE_travel_fee_hotel" value="<?php echo esc_attr( get_option( 'TRACKSUITE_travel_fee_hotel', '75.00' ) ); ?>" class="small-text"></td>
            </tr>
        </table>
        <?php submit_button( 'Save Fee Settings' ); ?>
    </form>
</div>

<script>
document.querySelectorAll('a[href^="#assign-"]').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const row = document.querySelector(link.getAttribute('href'));
        if (row) row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
    });
});
</script>

