<?php
/**
 * Admin View — Payroll
 * WP Admin → Xtreme Force → Payroll
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

$payroll_mgr = new TRACKSUITE_Payroll();

// Handle actions
if ( isset( $_POST['TRACKSUITE_payroll_nonce'] ) && wp_verify_nonce( $_POST['TRACKSUITE_payroll_nonce'], 'TRACKSUITE_save_payroll' ) ) {
    $action = sanitize_key( $_POST['action_type'] ?? 'create' );
    if ( $action === 'create_staff' ) {
        $payroll_mgr->add_staff( $_POST );
        echo '<div class="notice notice-success"><p>Staff member added.</p></div>';
    } elseif ( $action === 'create_payroll' ) {
        $id = $payroll_mgr->create_payroll_entry( $_POST );
        echo $id
            ? '<div class="notice notice-success"><p>Payroll entry created.</p></div>'
            : '<div class="notice notice-error"><p>Failed to create entry.</p></div>';
    }
}
if ( isset( $_GET['mark_paid'] ) && check_admin_referer( 'TRACKSUITE_payroll_paid' ) ) {
    $payroll_mgr->mark_paid( (int) $_GET['mark_paid'] );
    echo '<div class="notice notice-success"><p>Marked as paid.</p></div>';
}
if ( isset( $_GET['void'] ) && check_admin_referer( 'TRACKSUITE_payroll_void' ) ) {
    $payroll_mgr->void_entry( (int) $_GET['void'] );
}
if ( isset( $_GET['export_csv'] ) ) {
    $payroll_mgr->export_payroll_csv( $_GET['period_start'] ?? '', $_GET['period_end'] ?? '' );
}

$all_staff   = $payroll_mgr->get_all_staff();
$all_payroll = $payroll_mgr->get_all_payroll();
$pending     = $payroll_mgr->get_pending_payroll();
?>

<div class="wrap ts-admin-payroll">
    <h1>💵 Payroll</h1>

    <!-- Pending Alert -->
    <?php if ( ! empty( $pending ) ) : ?>
    <div class="notice notice-warning">
        <p><strong><?php echo count( $pending ); ?> payroll entries pending payment.</strong></p>
    </div>
    <?php endif; ?>

    <!-- Export Controls -->
    <div style="margin-bottom:16px;">
        <form method="get" style="display:inline-flex;gap:8px;align-items:center;">
            <input type="hidden" name="page" value="ts-payroll">
            <input type="hidden" name="export_csv" value="1">
            <label>From: <input type="date" name="period_start"></label>
            <label>To: <input type="date" name="period_end"></label>
            <button type="submit" class="button">📥 Export CSV</button>
        </form>
    </div>

    <!-- Payroll Ledger -->
    <h2>Payroll Ledger</h2>
    <table class="wp-list-table widefat fixed striped">
        <thead><tr><th>Staff</th><th>Role</th><th>Period</th><th>Hours</th><th>Gross</th><th>Deductions</th><th>Net</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
        <?php if ( empty( $all_payroll ) ) : ?>
            <tr><td colspan="9" style="text-align:center;"><em>No payroll entries yet.</em></td></tr>
        <?php else : foreach ( $all_payroll as $p ) : ?>
            <tr>
                <td><?php echo esc_html( $p['display_name'] ); ?></td>
                <td><?php echo esc_html( $p['role'] ); ?></td>
                <td><?php echo esc_html( $p['period_start'] . ' – ' . $p['period_end'] ); ?></td>
                <td><?php echo esc_html( $p['hours_worked'] ); ?></td>
                <td>$<?php echo number_format( $p['gross_pay'], 2 ); ?></td>
                <td>$<?php echo number_format( $p['deductions'], 2 ); ?></td>
                <td><strong>$<?php echo number_format( $p['net_pay'], 2 ); ?></strong></td>
                <td><span class="ts-status ts-status-<?php echo esc_attr( $p['status'] ); ?>"><?php echo esc_html( ucfirst( $p['status'] ) ); ?></span></td>
                <td>
                    <?php if ( $p['status'] === 'pending' ) : ?>
                        <a href="?page=ts-payroll&mark_paid=<?php echo $p['id']; ?>&<?php echo wp_create_nonce( 'TRACKSUITE_payroll_paid' ); ?>">Mark Paid</a> |
                        <a href="?page=ts-payroll&void=<?php echo $p['id']; ?>&<?php echo wp_create_nonce( 'TRACKSUITE_payroll_void' ); ?>" onclick="return confirm('Void this entry?')">Void</a>
                    <?php else : echo '—'; endif; ?>
                </td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>

    <hr>

    <!-- Create Payroll Entry -->
    <h2>Create Payroll Entry</h2>
    <form method="post">
        <?php wp_nonce_field( 'TRACKSUITE_save_payroll', 'TRACKSUITE_payroll_nonce' ); ?>
        <input type="hidden" name="action_type" value="create_payroll">
        <table class="form-table">
            <tr>
                <th><label>Staff Member</label></th>
                <td>
                    <select name="staff_id" required>
                        <option value="">— Select Staff —</option>
                        <?php foreach ( $all_staff as $s ) : ?>
                            <option value="<?php echo $s['id']; ?>"><?php echo esc_html( $s['display_name'] . ' — ' . $s['role'] . ' ($' . number_format( $s['hourly_wage'], 2 ) . '/hr)' ); ?></option>
                        <?php endforeach; ?>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label>Period Start</label></th>
                <td><input type="date" name="period_start" required></td>
            </tr>
            <tr>
                <th><label>Period End</label></th>
                <td><input type="date" name="period_end" required></td>
            </tr>
            <tr>
                <th><label>Hours Worked</label></th>
                <td><input type="number" name="hours_worked" step="0.25" min="0" required class="small-text"></td>
            </tr>
            <tr>
                <th><label>Deductions ($)</label></th>
                <td><input type="number" name="deductions" step="0.01" min="0" value="0.00" class="small-text"></td>
            </tr>
            <tr>
                <th><label>Notes</label></th>
                <td><input type="text" name="notes" class="regular-text" placeholder="Optional notes"></td>
            </tr>
        </table>
        <?php submit_button( 'Create Payroll Entry' ); ?>
    </form>

    <hr>

    <!-- Staff Management -->
    <h2>Staff List</h2>
    <table class="wp-list-table widefat fixed striped">
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Hourly Wage</th><th>Hire Date</th><th>Status</th></tr></thead>
        <tbody>
        <?php if ( empty( $all_staff ) ) : ?>
            <tr><td colspan="6" style="text-align:center;"><em>No staff on file yet.</em></td></tr>
        <?php else : foreach ( $all_staff as $s ) : ?>
            <tr>
                <td><?php echo esc_html( $s['display_name'] ); ?></td>
                <td><?php echo esc_html( $s['user_email'] ); ?></td>
                <td><?php echo esc_html( $s['role'] ); ?></td>
                <td>$<?php echo number_format( $s['hourly_wage'], 2 ); ?>/hr</td>
                <td><?php echo esc_html( $s['hire_date'] ); ?></td>
                <td><span class="ts-status ts-status-<?php echo esc_attr( $s['status'] ); ?>"><?php echo esc_html( ucfirst( $s['status'] ) ); ?></span></td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>

    <h3>Add Staff Member</h3>
    <form method="post">
        <?php wp_nonce_field( 'TRACKSUITE_save_payroll', 'TRACKSUITE_payroll_nonce' ); ?>
        <input type="hidden" name="action_type" value="create_staff">
        <table class="form-table">
            <tr>
                <th><label>WordPress User</label></th>
                <td><?php wp_dropdown_users( [ 'name' => 'user_id', 'show_option_none' => '— Select User —', 'role__in' => ['TRACKSUITE_staff','TRACKSUITE_coach','administrator'] ] ); ?></td>
            </tr>
            <tr>
                <th><label>Role/Title</label></th>
                <td><input type="text" name="role" class="regular-text" placeholder="e.g. Head Coach, Assistant Coach, Manager"></td>
            </tr>
            <tr>
                <th><label>Hourly Wage ($)</label></th>
                <td><input type="number" name="hourly_wage" step="0.01" min="0" class="small-text" placeholder="0.00"></td>
            </tr>
            <tr>
                <th><label>Hire Date</label></th>
                <td><input type="date" name="hire_date"></td>
            </tr>
        </table>
        <?php submit_button( 'Add Staff Member', 'secondary' ); ?>
    </form>
</div>

