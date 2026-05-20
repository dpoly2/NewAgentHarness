<?php
/**
 * Public View — Athlete Results & Performance Charts
 * Shortcode: [xftc_results]
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

if ( ! is_user_logged_in() ) {
    echo '<p>Please <a href="' . esc_url( wp_login_url( get_permalink() ) ) . '">log in</a> to view results.</p>';
    return;
}

$results_mgr = new XFTC_Results();
$user_id     = get_current_user_id();

// TODO: Get athlete_id from URL param or default to first athlete for this parent
$athlete_id    = isset( $_GET['athlete_id'] ) ? (int) $_GET['athlete_id'] : 0;
$selected_event = sanitize_text_field( $_GET['event'] ?? '' );

$all_results   = $athlete_id ? $results_mgr->get_athlete_results( $athlete_id ) : [];
$personal_bests= $athlete_id ? $results_mgr->get_personal_bests( $athlete_id ) : [];
$events        = $athlete_id ? $results_mgr->get_athlete_events( $athlete_id ) : [];
$chart_data    = ( $athlete_id && $selected_event )
    ? $results_mgr->get_progression_chart_data( $athlete_id, $selected_event )
    : null;
?>

<div class="xftc-results-wrap">
    <h2>📊 Athlete Results</h2>

    <!-- Athlete Selector (TODO: populate from parent's athletes) -->
    <form method="get" style="margin-bottom:16px;">
        <label><strong>Athlete:</strong>
            <select name="athlete_id" onchange="this.form.submit()">
                <option value="">— Select Athlete —</option>
                <!-- TODO: Load from XFTC_Members::get_athletes_by_parent() -->
            </select>
        </label>
        <?php if ( ! empty( $events ) ) : ?>
            <label><strong>Event:</strong>
                <select name="event" onchange="this.form.submit()">
                    <option value="">— All Events —</option>
                    <?php foreach ( $events as $evt ) : ?>
                        <option value="<?php echo esc_attr( $evt ); ?>" <?php selected( $selected_event, $evt ); ?>>
                            <?php echo esc_html( $evt ); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </label>
        <?php endif; ?>
    </form>

    <?php if ( $athlete_id ) : ?>

        <!-- Personal Bests -->
        <?php if ( ! empty( $personal_bests ) ) : ?>
        <h3>🏅 Personal Bests</h3>
        <div class="xftc-pb-grid">
            <?php foreach ( $personal_bests as $pb ) : ?>
                <div class="xftc-pb-card">
                    <span class="xftc-pb-event"><?php echo esc_html( $pb['event_category'] ); ?></span>
                    <span class="xftc-pb-value"><?php echo esc_html( $pb['result_value'] ); ?></span>
                    <?php if ( $pb['is_club_record'] ) : ?>
                        <span class="xftc-cr-badge">🏆 Club Record</span>
                    <?php endif; ?>
                </div>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <!-- Performance Chart -->
        <?php if ( $chart_data && ! empty( $chart_data['labels'] ) ) : ?>
        <h3>📈 Performance Progression — <?php echo esc_html( $selected_event ); ?></h3>
        <div class="xftc-chart-wrap" style="max-width:700px;">
            <canvas id="xftcProgressChart"></canvas>
        </div>
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const ctx = document.getElementById('xftcProgressChart');
            if (!ctx || typeof Chart === 'undefined') return;

            const labels = <?php echo wp_json_encode( $chart_data['labels'] ); ?>;
            const values = <?php echo wp_json_encode( $chart_data['values'] ); ?>;
            const isPB   = <?php echo wp_json_encode( $chart_data['is_pb'] ); ?>;

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '<?php echo esc_js( $selected_event ); ?>',
                        data: values,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231,76,60,0.1)',
                        pointBackgroundColor: isPB.map(pb => pb ? '#f39c12' : '#e74c3c'),
                        pointRadius: isPB.map(pb => pb ? 8 : 5),
                        tension: 0.3,
                        fill: true,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: true },
                        tooltip: {
                            callbacks: {
                                afterLabel: (ctx) => isPB[ctx.dataIndex] ? '🏅 Personal Best' : ''
                            }
                        }
                    },
                    scales: {
                        y: { title: { display: true, text: 'Result' } },
                        x: { title: { display: true, text: 'Meet' } }
                    }
                }
            });
        });
        </script>
        <?php endif; ?>

        <!-- Full Results History -->
        <h3>Full Results History</h3>
        <?php if ( empty( $all_results ) ) : ?>
            <p class="xftc-muted"><em>No results on record yet.</em></p>
        <?php else : ?>
        <table class="xftc-results-table">
            <thead>
                <tr><th>Meet</th><th>Date</th><th>Event</th><th>Result</th><th>Place</th><th>Awards</th></tr>
            </thead>
            <tbody>
            <?php foreach ( $all_results as $r ) :
                if ( $selected_event && $r['event_category'] !== $selected_event ) continue;
            ?>
                <tr>
                    <td><?php echo esc_html( $r['meet_name'] ); ?></td>
                    <td><?php echo esc_html( date( 'M j, Y', strtotime( $r['meet_date'] ) ) ); ?></td>
                    <td><?php echo esc_html( $r['event_category'] ); ?></td>
                    <td><strong><?php echo esc_html( $r['result_value'] ); ?></strong></td>
                    <td><?php echo $r['placement'] ? '#' . $r['placement'] : '—'; ?></td>
                    <td>
                        <?php echo $r['is_personal_best'] ? '<span class="xftc-badge xftc-badge-pb">🏅 PB</span>' : ''; ?>
                        <?php echo $r['is_club_record']   ? '<span class="xftc-badge xftc-badge-cr">🏆 CR</span>' : ''; ?>
                    </td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table>
        <?php endif; ?>

    <?php else : ?>
        <div class="xftc-notice xftc-notice-info">
            <p>Select an athlete above to view their results and performance history.</p>
        </div>
    <?php endif; ?>
</div>
