<?php
/**
 * Public Portal View — Parent Dashboard with tabbed athlete cards
 * Shortcodes: [xftc_my_athletes], [xftc_roster]
 * Variables: $athletes, $active (season), $user, $view, $show_stats
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

global $wpdb;

// ── [xftc_roster] — public athlete card grid ────────────────────────────────
if ( isset( $view ) ) :
    if ( $view === 'cards' ) : ?>
        <div class="xftc-roster-grid">
            <?php if ( empty( $athletes ) ) : ?>
                <p class="xftc-empty">Roster coming soon!</p>
            <?php else : foreach ( $athletes as $athlete ) :
                $initials = strtoupper( substr( $athlete->first_name, 0, 1 ) . substr( $athlete->last_name, 0, 1 ) );
                $age      = ! empty( $athlete->dob ) ? floor( ( time() - strtotime( $athlete->dob ) ) / 31557600 ) : null;
                $rt       = $wpdb->prefix . 'xftc_results';
                $pbs      = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND is_personal_best=1", $athlete->id ) );
                $golds    = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND placement=1", $athlete->id ) );
            ?>
            <div class="xftc-athlete-card">
                <div class="xftc-athlete-card__photo">
                    <div class="xftc-athlete-card__initials"><?php echo esc_html( $initials ); ?></div>
                </div>
                <div class="xftc-athlete-card__body">
                    <div class="xftc-athlete-card__name"><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></div>
                    <div class="xftc-athlete-card__details">
                        <?php
                        $meta = [];
                        if ( $age ) $meta[] = 'Age ' . $age;
                        if ( ! empty( $athlete->team_level ) ) $meta[] = $athlete->team_level;
                        if ( ! empty( $athlete->school ) )     $meta[] = $athlete->school;
                        echo esc_html( implode( ' · ', $meta ) );
                        ?>
                    </div>
                    <?php if ( $show_stats ) : ?>
                    <div class="xftc-athlete-card__stats">
                        <div class="xftc-athlete-card__stat"><strong><?php echo $pbs; ?></strong> PBs</div>
                        <div class="xftc-athlete-card__stat"><strong><?php echo $golds; ?></strong> 🥇</div>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            <?php endforeach; endif; ?>
        </div>

    <?php else : // list view ?>
        <div class="xftc-table-wrap">
            <table class="xftc-table">
                <thead><tr><th>Name</th><th>Level</th><th>School</th></tr></thead>
                <tbody>
                <?php foreach ( $athletes as $athlete ) : ?>
                    <tr>
                        <td><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></td>
                        <td><?php echo esc_html( $athlete->team_level ?? '—' ); ?></td>
                        <td><?php echo esc_html( $athlete->school ?? '—' ); ?></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>

<?php // ── [xftc_my_athletes] — parent portal with tabbed athlete cards ──────
else : ?>

<div class="xftc-portal">

    <?php if ( ! empty( $active ) ) : ?>
    <div class="xftc-season-banner">
        <strong>🏃 Active Season:</strong> <?php echo esc_html( $active->name ); ?>
        <?php if ( ! empty( $active->reg_close ) ) : ?>
            &nbsp;·&nbsp; Registration closes <strong><?php echo esc_html( date( 'M j, Y', strtotime( $active->reg_close ) ) ); ?></strong>
        <?php endif; ?>
    </div>
    <?php endif; ?>

    <?php if ( empty( $athletes ) ) : ?>
        <div class="xftc-empty-state">
            <p>No athletes registered yet.</p>
            <a href="<?php echo esc_url( home_url( '/register' ) ); ?>" class="xftc-btn xftc-btn--primary">➕ Add an Athlete</a>
        </div>

    <?php else : ?>

        <?php foreach ( $athletes as $idx => $athlete ) :
            $initials   = strtoupper( substr( $athlete->first_name, 0, 1 ) . substr( $athlete->last_name, 0, 1 ) );
            $age        = ! empty( $athlete->dob ) ? floor( ( time() - strtotime( $athlete->dob ) ) / 31557600 ) : null;
            $uid        = 'athlete-' . $athlete->id;

            // ── DB tables
            $rt  = $wpdb->prefix . 'xftc_results';
            $met = $wpdb->prefix . 'xftc_meet_entries';
            $mmt = $wpdb->prefix . 'xftc_meets';
            $trt = $wpdb->prefix . 'xftc_travel';
            $pmt = $wpdb->prefix . 'xftc_payments';
            $mbt = $wpdb->prefix . 'xftc_memberships';

            // ── Stats tab data
            $total_results = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d", $athlete->id ) );
            $pbs           = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND is_personal_best=1", $athlete->id ) );
            $club_records  = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND is_club_record=1", $athlete->id ) );
            $golds         = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND placement=1", $athlete->id ) );
            $results_hist  = $wpdb->get_results( $wpdb->prepare(
                "SELECT r.*, m.name AS meet_name, m.meet_date FROM {$rt} r
                 LEFT JOIN {$mmt} m ON r.meet_id=m.id
                 WHERE r.athlete_id=%d ORDER BY m.meet_date DESC LIMIT 10",
                $athlete->id
            ) );
            // Chart data grouped by event category
            $chart_data    = $wpdb->get_results( $wpdb->prepare(
                "SELECT event_category, result_value, recorded_at FROM {$rt}
                 WHERE athlete_id=%d ORDER BY recorded_at ASC",
                $athlete->id
            ) );

            // ── Meet history tab data
            $meet_history  = $wpdb->get_results( $wpdb->prepare(
                "SELECT me.*, m.name AS meet_name, m.meet_date, m.location, m.type, m.status AS meet_status
                 FROM {$met} me
                 LEFT JOIN {$mmt} m ON me.meet_id=m.id
                 WHERE me.athlete_id=%d ORDER BY m.meet_date DESC LIMIT 15",
                $athlete->id
            ) );
            $upcoming_regs = array_filter( $meet_history, fn($m) => $m->meet_status === 'upcoming' );
            $past_regs     = array_filter( $meet_history, fn($m) => $m->meet_status === 'completed' );

            // ── Travel bookings tab data
            $travel_bookings = $wpdb->get_results( $wpdb->prepare(
                "SELECT t.*, m.name AS meet_name, m.meet_date, m.location
                 FROM {$trt} t
                 LEFT JOIN {$mmt} m ON t.meet_id=m.id
                 WHERE t.athlete_id=%d ORDER BY m.meet_date DESC",
                $athlete->id
            ) );

            // ── Membership / payments tab data
            $membership    = $wpdb->get_row( $wpdb->prepare(
                "SELECT * FROM {$mbt} WHERE athlete_id=%d ORDER BY registered_at DESC LIMIT 1",
                $athlete->id
            ) );
            $payment_hist  = $wpdb->get_results( $wpdb->prepare(
                "SELECT p.* FROM {$pmt} p WHERE p.user_id=%d ORDER BY p.created_at DESC LIMIT 10",
                $athlete->parent_id
            ) );
        ?>

        <!-- ── Athlete Card ──────────────────────────────────────────────────── -->
        <div class="xftc-portal-athlete-card" id="<?php echo esc_attr( $uid ); ?>">

            <!-- Card header -->
            <div class="xftc-portal-athlete-card__header">
                <div class="xftc-portal-athlete-card__avatar"><?php echo esc_html( $initials ); ?></div>
                <div class="xftc-portal-athlete-card__info">
                    <h3><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></h3>
                    <div class="xftc-portal-athlete-card__meta">
                        <?php
                        $meta = [];
                        if ( $age )                             $meta[] = 'Age ' . $age;
                        if ( ! empty( $athlete->team_level ) ) $meta[] = $athlete->team_level;
                        if ( ! empty( $athlete->school ) )     $meta[] = $athlete->school;
                        echo esc_html( implode( ' · ', $meta ) );
                        ?>
                    </div>
                    <div class="xftc-portal-athlete-card__kpis">
                        <span class="xftc-kpi"><strong><?php echo $total_results; ?></strong> Results</span>
                        <span class="xftc-kpi"><strong><?php echo $pbs; ?></strong> PBs</span>
                        <span class="xftc-kpi"><strong><?php echo $golds; ?></strong> 🥇 Wins</span>
                        <?php if ( $club_records ) : ?>
                        <span class="xftc-kpi xftc-kpi--record"><strong><?php echo $club_records; ?></strong> 🏆 Club Records</span>
                        <?php endif; ?>
                    </div>
                </div>
                <?php if ( $membership ) :
                    $pay_class = $membership->payment_status === 'paid' ? 'xftc-badge--green' : ( $membership->payment_status === 'partial' ? 'xftc-badge--orange' : 'xftc-badge--red' );
                ?>
                <div class="xftc-portal-athlete-card__status">
                    <span class="xftc-badge <?php echo $pay_class; ?>">
                        <?php echo esc_html( ucfirst( $membership->payment_status ) ); ?>
                    </span>
                    <span class="xftc-badge xftc-badge--blue"><?php echo esc_html( ucfirst( $membership->tier ?? 'standard' ) ); ?></span>
                </div>
                <?php endif; ?>
            </div><!-- /.header -->

            <!-- ── Tab Nav ──────────────────────────────────────────────────── -->
            <div class="xftc-tabs" data-athlete="<?php echo esc_attr( $athlete->id ); ?>">
                <div class="xftc-tabs__nav" role="tablist">
                    <button class="xftc-tab-btn xftc-tab-btn--active" role="tab" data-tab="stats-<?php echo $athlete->id; ?>">📊 Stats</button>
                    <button class="xftc-tab-btn" role="tab" data-tab="meets-<?php echo $athlete->id; ?>">📅 Meet History</button>
                    <button class="xftc-tab-btn" role="tab" data-tab="travel-<?php echo $athlete->id; ?>">✈️ Travel</button>
                    <button class="xftc-tab-btn" role="tab" data-tab="payments-<?php echo $athlete->id; ?>">💳 Payments</button>
                </div>

                <!-- ── TAB: Stats ────────────────────────────────────────────── -->
                <div class="xftc-tab-panel xftc-tab-panel--active" id="stats-<?php echo $athlete->id; ?>">
                    <?php if ( empty( $results_hist ) ) : ?>
                        <p class="xftc-empty">No results recorded yet. Results will appear here after meets are completed.</p>
                    <?php else : ?>
                        <!-- Chart -->
                        <div class="xftc-chart-wrap">
                            <canvas id="chart-<?php echo $athlete->id; ?>" height="120"></canvas>
                        </div>
                        <!-- Results table -->
                        <table class="xftc-table xftc-table--compact">
                            <thead>
                                <tr><th>Meet</th><th>Date</th><th>Event</th><th>Result</th><th>Place</th><th>Badges</th></tr>
                            </thead>
                            <tbody>
                            <?php foreach ( $results_hist as $res ) : ?>
                                <tr>
                                    <td><?php echo esc_html( $res->meet_name ?? '—' ); ?></td>
                                    <td><?php echo esc_html( $res->meet_date ? date( 'M j, Y', strtotime( $res->meet_date ) ) : '—' ); ?></td>
                                    <td><?php echo esc_html( $res->event_category ?? '—' ); ?></td>
                                    <td><strong><?php echo esc_html( $res->result_value ?? '—' ); ?></strong></td>
                                    <td><?php echo $res->placement ? esc_html( '#' . $res->placement ) : '—'; ?></td>
                                    <td>
                                        <?php if ( $res->is_personal_best ) echo '<span class="xftc-badge xftc-badge--green">⚡ PB</span> '; ?>
                                        <?php if ( $res->is_club_record )   echo '<span class="xftc-badge xftc-badge--purple">🏆 CR</span>'; ?>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                        <!-- Chart.js init -->
                        <script>
                        document.addEventListener('DOMContentLoaded', function() {
                            var ctx = document.getElementById('chart-<?php echo $athlete->id; ?>').getContext('2d');
                            var data = <?php
                                $grouped = [];
                                foreach ( $chart_data as $r ) {
                                    $grouped[ $r->event_category ][] = [
                                        'x' => $r->recorded_at,
                                        'y' => is_numeric( $r->result_value ) ? floatval( $r->result_value ) : 0,
                                    ];
                                }
                                $datasets = [];
                                $colors = ['#FF6200','#164f90','#27ae60','#8e44ad','#e74c3c'];
                                $ci = 0;
                                foreach ( $grouped as $event => $points ) {
                                    $datasets[] = [
                                        'label'           => $event,
                                        'data'            => $points,
                                        'borderColor'     => $colors[ $ci % count($colors) ],
                                        'backgroundColor' => $colors[ $ci % count($colors) ] . '33',
                                        'tension'         => 0.3,
                                        'fill'            => false,
                                    ];
                                    $ci++;
                                }
                                echo json_encode(['datasets' => $datasets]);
                            ?>;
                            new Chart(ctx, {
                                type: 'line',
                                data: data,
                                options: {
                                    responsive: true,
                                    scales: {
                                        x: { type: 'time', time: { unit: 'month' }, title: { display: true, text: 'Date' } },
                                        y: { title: { display: true, text: 'Result' } }
                                    },
                                    plugins: { legend: { position: 'top' } }
                                }
                            });
                        });
                        </script>
                    <?php endif; ?>
                </div><!-- /#stats -->

                <!-- ── TAB: Meet History ─────────────────────────────────────── -->
                <div class="xftc-tab-panel" id="meets-<?php echo $athlete->id; ?>">

                    <?php if ( ! empty( $upcoming_regs ) ) : ?>
                        <h4 class="xftc-tab-section-title">📅 Upcoming Meets</h4>
                        <table class="xftc-table xftc-table--compact">
                            <thead><tr><th>Meet</th><th>Date</th><th>Location</th><th>Event</th><th>Division</th></tr></thead>
                            <tbody>
                            <?php foreach ( $upcoming_regs as $entry ) : ?>
                                <tr>
                                    <td><strong><?php echo esc_html( $entry->meet_name ); ?></strong></td>
                                    <td><?php echo esc_html( date( 'M j, Y', strtotime( $entry->meet_date ) ) ); ?></td>
                                    <td><?php echo esc_html( $entry->location ?? '—' ); ?></td>
                                    <td><?php echo esc_html( $entry->event_category ?? '—' ); ?></td>
                                    <td><?php echo esc_html( $entry->division ?? '—' ); ?></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php endif; ?>

                    <?php if ( ! empty( $past_regs ) ) : ?>
                        <h4 class="xftc-tab-section-title">🏁 Past Meets</h4>
                        <table class="xftc-table xftc-table--compact">
                            <thead><tr><th>Meet</th><th>Date</th><th>Location</th><th>Type</th><th>Event</th></tr></thead>
                            <tbody>
                            <?php foreach ( $past_regs as $entry ) : ?>
                                <tr>
                                    <td><strong><?php echo esc_html( $entry->meet_name ); ?></strong></td>
                                    <td><?php echo esc_html( date( 'M j, Y', strtotime( $entry->meet_date ) ) ); ?></td>
                                    <td><?php echo esc_html( $entry->location ?? '—' ); ?></td>
                                    <td><span class="xftc-badge xftc-badge--blue"><?php echo esc_html( ucfirst( $entry->type ?? '' ) ); ?></span></td>
                                    <td><?php echo esc_html( $entry->event_category ?? '—' ); ?></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php endif; ?>

                    <?php if ( empty( $meet_history ) ) : ?>
                        <p class="xftc-empty">No meet registrations yet.
                            <?php if ( ! empty( $active ) ) : ?>
                                <a href="<?php echo esc_url( home_url( '/meets' ) ); ?>">Browse upcoming meets →</a>
                            <?php endif; ?>
                        </p>
                    <?php endif; ?>

                    <div class="xftc-tab-actions">
                        <a href="<?php echo esc_url( home_url( '/meets' ) ); ?>" class="xftc-btn xftc-btn--outline">📋 Register for a Meet →</a>
                    </div>
                </div><!-- /#meets -->

                <!-- ── TAB: Travel ───────────────────────────────────────────── -->
                <div class="xftc-tab-panel" id="travel-<?php echo $athlete->id; ?>">
                    <?php if ( empty( $travel_bookings ) ) : ?>
                        <p class="xftc-empty">No travel bookings yet. Travel options appear when a meet has bus or hotel availability.</p>
                    <?php else : ?>
                        <table class="xftc-table xftc-table--compact">
                            <thead>
                                <tr><th>Meet</th><th>Date</th><th>Type</th><th>Seat/Room</th><th>Fee</th><th>Status</th></tr>
                            </thead>
                            <tbody>
                            <?php foreach ( $travel_bookings as $booking ) :
                                $pay_class = $booking->payment_status === 'paid' ? 'xftc-badge--green' : ( $booking->payment_status === 'refunded' ? 'xftc-badge--teal' : 'xftc-badge--red' );
                            ?>
                                <tr>
                                    <td><strong><?php echo esc_html( $booking->meet_name ); ?></strong></td>
                                    <td><?php echo esc_html( $booking->meet_date ? date( 'M j, Y', strtotime( $booking->meet_date ) ) : '—' ); ?></td>
                                    <td><span class="xftc-badge xftc-badge--blue"><?php echo esc_html( ucfirst( $booking->travel_type ) ); ?></span></td>
                                    <td>
                                        <?php
                                        $details = [];
                                        if ( $booking->bus_seat )   $details[] = 'Seat ' . $booking->bus_seat;
                                        if ( $booking->hotel_room ) $details[] = 'Room ' . $booking->hotel_room;
                                        echo esc_html( $details ? implode( ' · ', $details ) : '—' );
                                        ?>
                                    </td>
                                    <td>$<?php echo number_format( $booking->travel_fee, 2 ); ?></td>
                                    <td><span class="xftc-badge <?php echo $pay_class; ?>"><?php echo esc_html( ucfirst( $booking->payment_status ) ); ?></span></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php endif; ?>
                </div><!-- /#travel -->

                <!-- ── TAB: Payments ─────────────────────────────────────────── -->
                <div class="xftc-tab-panel" id="payments-<?php echo $athlete->id; ?>">

                    <?php if ( $membership ) :
                        $balance = floatval( $membership->amount_due ) - floatval( $membership->amount_paid );
                        $pay_class = $membership->payment_status === 'paid' ? 'xftc-badge--green' : ( $membership->payment_status === 'partial' ? 'xftc-badge--orange' : 'xftc-badge--red' );
                    ?>
                    <div class="xftc-membership-summary">
                        <div class="xftc-membership-summary__item">
                            <span class="label">Membership</span>
                            <span class="xftc-badge <?php echo $pay_class; ?>"><?php echo esc_html( ucfirst( $membership->payment_status ) ); ?></span>
                        </div>
                        <div class="xftc-membership-summary__item">
                            <span class="label">Tier</span>
                            <strong><?php echo esc_html( ucfirst( $membership->tier ?? 'standard' ) ); ?></strong>
                        </div>
                        <div class="xftc-membership-summary__item">
                            <span class="label">Amount Due</span>
                            <strong>$<?php echo number_format( $membership->amount_due, 2 ); ?></strong>
                        </div>
                        <div class="xftc-membership-summary__item">
                            <span class="label">Amount Paid</span>
                            <strong class="xftc-text--green">$<?php echo number_format( $membership->amount_paid, 2 ); ?></strong>
                        </div>
                        <?php if ( $balance > 0 ) : ?>
                        <div class="xftc-membership-summary__item">
                            <span class="label">Balance</span>
                            <strong class="xftc-text--red">$<?php echo number_format( $balance, 2 ); ?></strong>
                        </div>
                        <?php endif; ?>
                    </div>

                    <?php if ( $balance > 0 ) : ?>
                        <div class="xftc-pay-now">
                            <a href="<?php echo esc_url( home_url( '/checkout/?athlete_id=' . $athlete->id ) ); ?>" class="xftc-btn xftc-btn--primary">
                                💳 Pay Balance: $<?php echo number_format( $balance, 2 ); ?> →
                            </a>
                        </div>
                    <?php endif; ?>
                    <?php endif; ?>

                    <?php if ( ! empty( $payment_hist ) ) : ?>
                        <h4 class="xftc-tab-section-title">Payment History</h4>
                        <table class="xftc-table xftc-table--compact">
                            <thead><tr><th>Date</th><th>Type</th><th>Amount</th><th>Gateway</th><th>Status</th></tr></thead>
                            <tbody>
                            <?php foreach ( $payment_hist as $pmt ) :
                                $s_class = $pmt->status === 'completed' ? 'xftc-badge--green' : ( $pmt->status === 'refunded' ? 'xftc-badge--teal' : 'xftc-badge--red' );
                            ?>
                                <tr>
                                    <td><?php echo esc_html( date( 'M j, Y', strtotime( $pmt->created_at ) ) ); ?></td>
                                    <td><?php echo esc_html( ucfirst( $pmt->reference_type ?? 'other' ) ); ?></td>
                                    <td><strong>$<?php echo number_format( $pmt->amount, 2 ); ?></strong></td>
                                    <td><?php echo esc_html( ucfirst( $pmt->gateway ) ); ?></td>
                                    <td><span class="xftc-badge <?php echo $s_class; ?>"><?php echo esc_html( ucfirst( $pmt->status ) ); ?></span></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                    <?php else : ?>
                        <p class="xftc-empty">No payment history yet.</p>
                    <?php endif; ?>

                </div><!-- /#payments -->

            </div><!-- /.xftc-tabs -->
        </div><!-- /.xftc-portal-athlete-card -->

        <?php endforeach; // athletes ?>

        <div class="xftc-portal-actions">
            <a href="<?php echo esc_url( home_url( '/register' ) ); ?>" class="xftc-btn xftc-btn--outline">➕ Add Another Athlete</a>
        </div>

    <?php endif; // athletes not empty ?>

</div><!-- /.xftc-portal -->

<?php endif; // portal vs roster view ?>
