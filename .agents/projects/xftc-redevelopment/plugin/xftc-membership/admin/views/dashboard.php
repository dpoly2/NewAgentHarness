<?php
/**
 * Admin Dashboard View — Xtreme Force Track Club
 * Variables: $total, $active, $upcoming_meets, $recent_payments, $payroll_due, $new_registrations
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

global $wpdb;

// ── Live stats ────────────────────────────────────────────────────────────────
$at = $wpdb->prefix . 'xftc_athletes';
$mt = $wpdb->prefix . 'xftc_meets';
$pt = $wpdb->prefix . 'xftc_payments';
$pw = $wpdb->prefix . 'xftc_payroll';
$mb = $wpdb->prefix . 'xftc_memberships';
$st = $wpdb->prefix . 'xftc_staff';

$total_athletes   = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$at}" );
$active_members   = (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$mb} WHERE status='active'" );
$upcoming_meets   = $wpdb->get_results( "SELECT * FROM {$mt} WHERE status='upcoming' AND meet_date >= CURDATE() ORDER BY meet_date ASC LIMIT 5" );
$upcoming_count   = count( $upcoming_meets );
$recent_payments  = $wpdb->get_results( "SELECT p.*, u.display_name FROM {$pt} p LEFT JOIN {$wpdb->users} u ON p.user_id=u.ID WHERE p.status='completed' ORDER BY p.created_at DESC LIMIT 8" );
$total_revenue    = (float) $wpdb->get_var( "SELECT SUM(amount) FROM {$pt} WHERE status='completed'" );
$payroll_due      = $wpdb->get_results(
    "SELECT pw.*, u.display_name, s.role FROM {$pw} pw
     LEFT JOIN {$st} s ON pw.staff_id=s.id
     LEFT JOIN {$wpdb->users} u ON s.user_id=u.ID
     WHERE pw.status='pending' ORDER BY pw.period_end ASC LIMIT 5"
);
$payroll_due_total = (float) $wpdb->get_var( "SELECT SUM(net_pay) FROM {$pw} WHERE status='pending'" );
$new_registrations = $wpdb->get_results(
    "SELECT mb.*, a.first_name, a.last_name, u.user_email
     FROM {$mb} mb
     LEFT JOIN {$at} a ON mb.athlete_id=a.id
     LEFT JOIN {$wpdb->users} u ON a.parent_id=u.ID
     WHERE mb.registered_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
     ORDER BY mb.registered_at DESC LIMIT 8"
);
$new_reg_count    = count( $new_registrations );
$outstanding      = (float) $wpdb->get_var( "SELECT SUM(amount_due - amount_paid) FROM {$mb} WHERE payment_status IN ('unpaid','partial')" );
?>

<div class="wrap xftc-admin-wrap">

    <!-- ── Page Header ──────────────────────────────────────────────────────── -->
    <div class="xftc-dashboard-header">
        <h1 class="xftc-page-title">
            <span class="dashicons dashicons-groups"></span>
            Xtreme Force Dashboard
        </h1>
        <div class="xftc-dashboard-header__season">
            <?php if ( $active ) : ?>
                <span class="xftc-season-badge xftc-season-badge--active">
                    ✅ Active Season: <?php echo esc_html( $active->name ); ?>
                </span>
            <?php else : ?>
                <span class="xftc-season-badge xftc-season-badge--none">⚠️ No Active Season</span>
            <?php endif; ?>
            <span class="xftc-dashboard-date"><?php echo esc_html( date( 'l, F j, Y' ) ); ?></span>
        </div>
    </div>

    <!-- ── KPI Stat Cards ───────────────────────────────────────────────────── -->
    <div class="xftc-stats-grid">

        <div class="xftc-stat-card xftc-stat-card--blue">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-groups"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number"><?php echo esc_html( $total_athletes ); ?></div>
                <div class="xftc-stat-label">Total Athletes</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members' ) ); ?>" class="xftc-stat-link">View All →</a>
        </div>

        <div class="xftc-stat-card xftc-stat-card--green">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-yes-alt"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number"><?php echo esc_html( $active_members ); ?></div>
                <div class="xftc-stat-label">Active Members</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members&status=active' ) ); ?>" class="xftc-stat-link">View →</a>
        </div>

        <div class="xftc-stat-card xftc-stat-card--orange">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-calendar-alt"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number"><?php echo esc_html( $upcoming_count ); ?></div>
                <div class="xftc-stat-label">Upcoming Meets</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets' ) ); ?>" class="xftc-stat-link">View →</a>
        </div>

        <div class="xftc-stat-card xftc-stat-card--purple">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-money-alt"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number">$<?php echo number_format( $total_revenue, 2 ); ?></div>
                <div class="xftc-stat-label">Total Revenue</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payments' ) ); ?>" class="xftc-stat-link">View →</a>
        </div>

        <div class="xftc-stat-card xftc-stat-card--red">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-warning"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number">$<?php echo number_format( $outstanding, 2 ); ?></div>
                <div class="xftc-stat-label">Outstanding Balances</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members&payment_status=unpaid' ) ); ?>" class="xftc-stat-link">Collect →</a>
        </div>

        <div class="xftc-stat-card xftc-stat-card--teal">
            <div class="xftc-stat-icon"><span class="dashicons dashicons-clipboard"></span></div>
            <div class="xftc-stat-body">
                <div class="xftc-stat-number"><?php echo esc_html( $new_reg_count ); ?></div>
                <div class="xftc-stat-label">New This Week</div>
            </div>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members&filter=week' ) ); ?>" class="xftc-stat-link">View →</a>
        </div>

    </div><!-- /.xftc-stats-grid -->

    <!-- ── Main Widget Grid ─────────────────────────────────────────────────── -->
    <div class="xftc-dashboard-grid">

        <!-- ── Widget: Upcoming Meets ────────────────────────────────────────── -->
        <div class="xftc-widget">
            <div class="xftc-widget__header">
                <h2><span class="dashicons dashicons-calendar-alt"></span> Upcoming Meets</h2>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets&action=new' ) ); ?>" class="xftc-widget__action button button-small">+ Add Meet</a>
            </div>
            <div class="xftc-widget__body">
                <?php if ( empty( $upcoming_meets ) ) : ?>
                    <p class="xftc-empty">No upcoming meets scheduled. <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets&action=new' ) ); ?>">Create one →</a></p>
                <?php else : ?>
                    <table class="xftc-widget-table">
                        <thead>
                            <tr><th>Meet</th><th>Date</th><th>Location</th><th>Type</th><th></th></tr>
                        </thead>
                        <tbody>
                        <?php foreach ( $upcoming_meets as $meet ) :
                            $days_away = (int) floor( ( strtotime( $meet->meet_date ) - time() ) / 86400 );
                            $urgency   = $days_away <= 7 ? 'xftc-badge--red' : ( $days_away <= 14 ? 'xftc-badge--orange' : 'xftc-badge--green' );
                        ?>
                            <tr>
                                <td><strong><?php echo esc_html( $meet->name ); ?></strong></td>
                                <td>
                                    <?php echo esc_html( date( 'M j', strtotime( $meet->meet_date ) ) ); ?>
                                    <span class="xftc-badge <?php echo $urgency; ?>">
                                        <?php echo $days_away <= 0 ? 'Today' : "in {$days_away}d"; ?>
                                    </span>
                                </td>
                                <td><?php echo esc_html( $meet->location ?? '—' ); ?></td>
                                <td><span class="xftc-badge xftc-badge--blue"><?php echo esc_html( ucfirst( $meet->type ) ); ?></span></td>
                                <td><a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets&action=edit&id=' . $meet->id ) ); ?>">Edit</a></td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div><!-- /.xftc-widget Upcoming Meets -->

        <!-- ── Widget: New Registrations ────────────────────────────────────── -->
        <div class="xftc-widget">
            <div class="xftc-widget__header">
                <h2><span class="dashicons dashicons-clipboard"></span> New Registrations <span class="xftc-badge xftc-badge--blue">Last 7 days</span></h2>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members' ) ); ?>" class="xftc-widget__action">View All →</a>
            </div>
            <div class="xftc-widget__body">
                <?php if ( empty( $new_registrations ) ) : ?>
                    <p class="xftc-empty">No new registrations this week.</p>
                <?php else : ?>
                    <table class="xftc-widget-table">
                        <thead><tr><th>Athlete</th><th>Email</th><th>Tier</th><th>Status</th><th>Registered</th></tr></thead>
                        <tbody>
                        <?php foreach ( $new_registrations as $reg ) :
                            $status_class = $reg->payment_status === 'paid' ? 'xftc-badge--green' : ( $reg->payment_status === 'partial' ? 'xftc-badge--orange' : 'xftc-badge--red' );
                        ?>
                            <tr>
                                <td><strong><?php echo esc_html( $reg->first_name . ' ' . $reg->last_name ); ?></strong></td>
                                <td><?php echo esc_html( $reg->user_email ?? '—' ); ?></td>
                                <td><span class="xftc-badge xftc-badge--blue"><?php echo esc_html( ucfirst( $reg->tier ?? 'standard' ) ); ?></span></td>
                                <td><span class="xftc-badge <?php echo $status_class; ?>"><?php echo esc_html( ucfirst( $reg->payment_status ) ); ?></span></td>
                                <td><?php echo esc_html( date( 'M j', strtotime( $reg->registered_at ) ) ); ?></td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div><!-- /.xftc-widget New Registrations -->

        <!-- ── Widget: Recent Payments ──────────────────────────────────────── -->
        <div class="xftc-widget">
            <div class="xftc-widget__header">
                <h2><span class="dashicons dashicons-money-alt"></span> Recent Payments</h2>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payments' ) ); ?>" class="xftc-widget__action">View All →</a>
            </div>
            <div class="xftc-widget__body">
                <?php if ( empty( $recent_payments ) ) : ?>
                    <p class="xftc-empty">No payments recorded yet.</p>
                <?php else : ?>
                    <table class="xftc-widget-table">
                        <thead><tr><th>Payer</th><th>Amount</th><th>Type</th><th>Gateway</th><th>Date</th></tr></thead>
                        <tbody>
                        <?php foreach ( $recent_payments as $pmt ) : ?>
                            <tr>
                                <td><strong><?php echo esc_html( $pmt->display_name ?? '—' ); ?></strong></td>
                                <td><strong>$<?php echo number_format( $pmt->amount, 2 ); ?></strong></td>
                                <td><?php echo esc_html( ucfirst( $pmt->reference_type ?? 'other' ) ); ?></td>
                                <td><span class="xftc-badge xftc-badge--<?php echo $pmt->gateway === 'stripe' ? 'purple' : ( $pmt->gateway === 'manual' ? 'teal' : 'blue' ); ?>">
                                    <?php echo esc_html( ucfirst( $pmt->gateway ) ); ?>
                                </span></td>
                                <td><?php echo esc_html( date( 'M j', strtotime( $pmt->created_at ) ) ); ?></td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div><!-- /.xftc-widget Recent Payments -->

        <!-- ── Widget: Payroll Due ───────────────────────────────────────────── -->
        <div class="xftc-widget">
            <div class="xftc-widget__header">
                <h2><span class="dashicons dashicons-id-alt"></span> Payroll Due
                    <?php if ( $payroll_due_total > 0 ) : ?>
                        <span class="xftc-badge xftc-badge--red">$<?php echo number_format( $payroll_due_total, 2 ); ?> pending</span>
                    <?php endif; ?>
                </h2>
                <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payroll' ) ); ?>" class="xftc-widget__action">Manage →</a>
            </div>
            <div class="xftc-widget__body">
                <?php if ( empty( $payroll_due ) ) : ?>
                    <p class="xftc-empty">✅ No pending payroll entries.</p>
                <?php else : ?>
                    <table class="xftc-widget-table">
                        <thead><tr><th>Staff</th><th>Role</th><th>Period</th><th>Net Pay</th><th></th></tr></thead>
                        <tbody>
                        <?php foreach ( $payroll_due as $entry ) : ?>
                            <tr>
                                <td><strong><?php echo esc_html( $entry->display_name ?? '—' ); ?></strong></td>
                                <td><?php echo esc_html( $entry->role ?? '—' ); ?></td>
                                <td><?php echo esc_html( date( 'M j', strtotime( $entry->period_start ) ) . '–' . date( 'M j', strtotime( $entry->period_end ) ) ); ?></td>
                                <td><strong>$<?php echo number_format( $entry->net_pay, 2 ); ?></strong></td>
                                <td>
                                    <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payroll&action=mark_paid&id=' . $entry->id ) ); ?>" class="button button-small button-primary">Mark Paid</a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div><!-- /.xftc-widget Payroll Due -->

    </div><!-- /.xftc-dashboard-grid -->

    <!-- ── Quick Actions Bar ────────────────────────────────────────────────── -->
    <div class="xftc-quick-actions">
        <h3>Quick Actions</h3>
        <div class="xftc-quick-actions__buttons">
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members' ) ); ?>" class="button button-primary">👥 View Members</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets&action=new' ) ); ?>" class="button">📅 Add Meet</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-seasons' ) ); ?>" class="button">🗓️ Manage Seasons</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payroll&action=new' ) ); ?>" class="button">💵 Log Payroll</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-payments&action=new' ) ); ?>" class="button">💳 Record Payment</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-reports' ) ); ?>" class="button">📊 View Reports</a>
            <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-settings' ) ); ?>" class="button">⚙️ Settings</a>
        </div>
    </div>

</div><!-- /.wrap.xftc-admin-wrap -->
