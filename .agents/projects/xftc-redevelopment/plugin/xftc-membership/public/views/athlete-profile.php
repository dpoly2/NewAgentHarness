<?php
/**
 * Public View — Athlete Profile (Results History + Progression Charts)
 * Shortcode: [xftc_athlete_profile id="123"]  OR  ?athlete_id=123
 * Variables: $athlete, $results, $prs, $by_event, $age, $division
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

$initials = strtoupper( substr($athlete->first_name,0,1) . substr($athlete->last_name,0,1) );
$gender_label = $athlete->gender === 'female' ? 'Girls' : 'Boys';
$events_competed = array_keys($by_event);
$total_results   = count($results);
$total_pbs       = count($prs);
$gold_count      = count(array_filter($results, fn($r) => $r->placement == 1));
$cr_count        = count(array_filter($results, fn($r) => $r->is_club_record));
?>

<div class="xftc-profile" id="xftc-athlete-profile">

    <!-- ── Athlete Header ─────────────────────────────────────────────── -->
    <div class="xftc-profile-header">
        <div class="xftc-profile-avatar"><?php echo esc_html($initials); ?></div>
        <div class="xftc-profile-info">
            <h2 class="xftc-profile-name">
                <?php echo esc_html($athlete->first_name . ' ' . $athlete->last_name); ?>
            </h2>
            <div class="xftc-profile-meta">
                <?php if ($age) : ?>
                    <span class="xftc-meta-chip">🎂 Age <?php echo esc_html($age); ?></span>
                <?php endif; ?>
                <span class="xftc-meta-chip"><?php echo esc_html($gender_label); ?> · <?php echo esc_html($division); ?></span>
                <?php if (!empty($athlete->team_level)) : ?>
                    <span class="xftc-meta-chip">⚡ <?php echo esc_html($athlete->team_level); ?></span>
                <?php endif; ?>
                <?php if (!empty($athlete->school)) : ?>
                    <span class="xftc-meta-chip">🏫 <?php echo esc_html($athlete->school); ?></span>
                <?php endif; ?>
            </div>
        </div>
        <a href="<?php echo esc_url( add_query_arg( ['gender' => $athlete->gender ?? '', 'division' => $division], home_url('/top-times/') ) ); ?>"
           class="xftc-btn xftc-btn--outline xftc-btn--sm">
            ← Back to Leaderboard
        </a>
    </div>

    <!-- ── Career Stats Bar ───────────────────────────────────────────── -->
    <div class="xftc-profile-stats-bar">
        <div class="xftc-profile-stat">
            <span class="xftc-profile-stat__num"><?php echo $total_results; ?></span>
            <span class="xftc-profile-stat__lbl">Total Results</span>
        </div>
        <div class="xftc-profile-stat">
            <span class="xftc-profile-stat__num"><?php echo count($events_competed); ?></span>
            <span class="xftc-profile-stat__lbl">Events</span>
        </div>
        <div class="xftc-profile-stat">
            <span class="xftc-profile-stat__num"><?php echo $total_pbs; ?></span>
            <span class="xftc-profile-stat__lbl">Personal Bests</span>
        </div>
        <div class="xftc-profile-stat">
            <span class="xftc-profile-stat__num"><?php echo $gold_count; ?></span>
            <span class="xftc-profile-stat__lbl">🥇 Wins</span>
        </div>
        <?php if ($cr_count) : ?>
        <div class="xftc-profile-stat xftc-profile-stat--record">
            <span class="xftc-profile-stat__num"><?php echo $cr_count; ?></span>
            <span class="xftc-profile-stat__lbl">🏆 Club Records</span>
        </div>
        <?php endif; ?>
    </div>

    <?php if (empty($results)) : ?>
        <div class="xftc-lb-empty">
            <span class="xftc-lb-empty__icon">📋</span>
            <h3>No Results Yet</h3>
            <p>This athlete's results will appear here once meets are completed and recorded.</p>
        </div>
    <?php else : ?>

    <!-- ── Personal Bests Summary ──────────────────────────────────────── -->
    <div class="xftc-profile-section">
        <div class="xftc-profile-section__header">
            <h3>⚡ Personal Bests</h3>
            <span class="xftc-profile-section__sub">Best mark per event — all-time</span>
        </div>
        <div class="xftc-pb-grid">
            <?php foreach ($prs as $ev => $pr) :
                $is_field = XFTC_Results::is_field_event($ev);
                $leaderboard_url = add_query_arg(['event' => $ev, 'division' => $division], home_url('/top-times/'));
            ?>
            <div class="xftc-pb-card <?php echo $pr->is_club_record ? 'xftc-pb-card--cr' : ''; ?>">
                <?php if ($pr->is_club_record) : ?>
                    <div class="xftc-pb-card__record-ribbon">🏆 Club Record</div>
                <?php endif; ?>
                <div class="xftc-pb-card__event"><?php echo esc_html($ev); ?></div>
                <div class="xftc-pb-card__result"><?php echo esc_html($pr->result_value); ?></div>
                <div class="xftc-pb-card__meet">
                    <?php echo esc_html($pr->meet_name ?? ''); ?>
                    <?php if ($pr->meet_date) echo ' · ' . date('M j, Y', strtotime($pr->meet_date)); ?>
                </div>
                <a href="<?php echo esc_url($leaderboard_url); ?>" class="xftc-pb-card__link">View Leaderboard →</a>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- ── Progression Charts ──────────────────────────────────────────── -->
    <div class="xftc-profile-section">
        <div class="xftc-profile-section__header">
            <h3>📈 Progression</h3>
            <span class="xftc-profile-section__sub">Performance over time</span>
        </div>

        <?php if (count($by_event) > 1) : ?>
        <div class="xftc-chart-event-tabs">
            <?php $first = true; foreach ($events_competed as $ev) : ?>
                <button class="xftc-chart-tab <?php echo $first ? 'xftc-chart-tab--active' : ''; ?>"
                    data-chart="chart-ev-<?php echo esc_attr(sanitize_title($ev . '-' . $athlete->id)); ?>">
                    <?php echo esc_html($ev); ?>
                </button>
            <?php $first = false; endforeach; ?>
        </div>
        <?php endif; ?>

        <?php $first = true; foreach ($by_event as $ev => $ev_results) :
            $is_field   = XFTC_Results::is_field_event($ev);
            $chart_id   = 'chart-ev-' . sanitize_title($ev . '-' . $athlete->id);
            $chart_labels = [];
            $chart_values = [];
            foreach ($ev_results as $r) {
                if (empty($r->meet_date)) continue;
                $chart_labels[] = date('M j, Y', strtotime($r->meet_date));
                $chart_values[] = XFTC_Results::result_to_sortable($r->result_value, $is_field ? 'distance' : 'time');
            }
            $pb_val = isset($prs[$ev]) ? XFTC_Results::result_to_sortable($prs[$ev]->result_value, $is_field ? 'distance' : 'time') : null;
        ?>
        <div class="xftc-chart-panel <?php echo $first ? 'xftc-chart-panel--active' : ''; ?>"
             id="<?php echo esc_attr($chart_id); ?>">
            <?php if (count($ev_results) < 2) : ?>
                <p class="xftc-chart-no-data">Only <?php echo count($ev_results); ?> result<?php echo count($ev_results)!==1?'s':''; ?> recorded — chart available after 2+ results.</p>
                <?php if ($ev_results) : $r = $ev_results[0]; ?>
                    <div class="xftc-single-result">
                        <strong><?php echo esc_html($r->result_value); ?></strong>
                        at <?php echo esc_html($r->meet_name ?? ''); ?>
                        <?php if ($r->meet_date) echo ' · ' . date('M j, Y', strtotime($r->meet_date)); ?>
                    </div>
                <?php endif; ?>
            <?php else : ?>
            <div class="xftc-chart-wrap xftc-chart-wrap--tall">
                <canvas id="canvas-<?php echo esc_attr($chart_id); ?>"></canvas>
            </div>
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                var ctx = document.getElementById('canvas-<?php echo esc_attr($chart_id); ?>').getContext('2d');
                var labels = <?php echo json_encode($chart_labels); ?>;
                var values = <?php echo json_encode($chart_values); ?>;
                var isField = <?php echo $is_field ? 'true' : 'false'; ?>;
                var pbVal   = <?php echo json_encode($pb_val); ?>;
                var evName  = <?php echo json_encode($ev); ?>;

                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: evName,
                                data: values,
                                borderColor: '#FF6200',
                                backgroundColor: 'rgba(255,98,0,0.1)',
                                pointBackgroundColor: values.map(function(v) {
                                    if (!pbVal) return '#FF6200';
                                    return isField ? (v >= pbVal ? '#27ae60' : '#FF6200') : (v <= pbVal ? '#27ae60' : '#FF6200');
                                }),
                                pointRadius: 6,
                                pointHoverRadius: 8,
                                tension: 0.35,
                                fill: true,
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        interaction: { intersect: false, mode: 'index' },
                        scales: {
                            x: {
                                ticks: { maxTicksLimit: 8, maxRotation: 30 },
                                grid: { display: false }
                            },
                            y: {
                                title: { display: true, text: isField ? 'Distance (cm)' : 'Time (seconds)' },
                                reverse: !isField,
                                ticks: {
                                    callback: function(val) {
                                        if (isField) {
                                            var inches = val / 2.54;
                                            var ft = Math.floor(inches/12);
                                            var rem = (inches % 12).toFixed(1);
                                            return ft + "'-" + rem + '"';
                                        } else {
                                            if (val >= 60) {
                                                var m = Math.floor(val/60);
                                                var s = (val % 60).toFixed(2);
                                                return m + ':' + (s < 10 ? '0' : '') + s;
                                            }
                                            return val.toFixed(2) + 's';
                                        }
                                    }
                                }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: function(ctx) {
                                        var val = ctx.parsed.y;
                                        if (isField) {
                                            var inches = val / 2.54;
                                            var ft = Math.floor(inches/12);
                                            var rem = (inches % 12).toFixed(1);
                                            return evName + ': ' + ft + "'-" + rem + '"';
                                        } else {
                                            if (val >= 60) {
                                                var m = Math.floor(val/60);
                                                var s = (val % 60).toFixed(2);
                                                return evName + ': ' + m + ':' + (s < 10 ? '0' : '') + s;
                                            }
                                            return evName + ': ' + val.toFixed(2) + 's';
                                        }
                                    }
                                }
                            },
                            annotation: pbVal ? {
                                annotations: {
                                    pbLine: {
                                        type: 'line',
                                        yMin: pbVal, yMax: pbVal,
                                        borderColor: '#27ae60',
                                        borderWidth: 2,
                                        borderDash: [6, 4],
                                        label: {
                                            content: 'PB', enabled: true,
                                            position: 'end',
                                            backgroundColor: '#27ae60',
                                            color: '#fff', font: { size: 10 }
                                        }
                                    }
                                }
                            } : {}
                        }
                    }
                });
            });
            </script>
            <?php endif; ?>
        </div><!-- /.xftc-chart-panel -->
        <?php $first = false; endforeach; ?>
    </div>

    <!-- ── Full Results History Table ─────────────────────────────────── -->
    <div class="xftc-profile-section">
        <div class="xftc-profile-section__header">
            <h3>📋 Complete Results History</h3>
            <div class="xftc-profile-section__controls">
                <input type="text" id="xftc-results-search"
                    placeholder="Filter by event or meet..."
                    class="xftc-search-input"
                    onkeyup="xftcFilterResults(this.value)"/>
            </div>
        </div>

        <div class="xftc-table-wrap">
        <table class="xftc-table xftc-results-history-table" id="xftc-results-table">
            <thead>
                <tr>
                    <th>Event</th>
                    <th>Result</th>
                    <th>Place</th>
                    <th>Meet</th>
                    <th>Date</th>
                    <th>Badges</th>
                </tr>
            </thead>
            <tbody>
            <?php foreach ($results as $res) :
                $is_field   = XFTC_Results::is_field_event($res->event_category);
                $place_icon = $res->placement == 1 ? '🥇' : ($res->placement == 2 ? '🥈' : ($res->placement == 3 ? '🥉' : ($res->placement ? '#'.$res->placement : '—')));
                $row_class  = '';
                if ($res->is_club_record)   $row_class .= ' xftc-row--cr';
                if ($res->is_personal_best) $row_class .= ' xftc-row--pb';
            ?>
                <tr class="xftc-results-row<?php echo $row_class; ?>"
                    data-event="<?php echo esc_attr(strtolower($res->event_category)); ?>"
                    data-meet="<?php echo esc_attr(strtolower($res->meet_name ?? '')); ?>">
                    <td><strong><?php echo esc_html($res->event_category); ?></strong></td>
                    <td>
                        <strong class="xftc-result-val"><?php echo esc_html($res->result_value); ?></strong>
                        <?php if ($is_field) echo '<span class="xftc-result-unit">ft-in</span>'; ?>
                    </td>
                    <td><?php echo $place_icon; ?></td>
                    <td>
                        <span class="xftc-meet-name"><?php echo esc_html($res->meet_name ?? '—'); ?></span>
                        <?php if (!empty($res->location)) echo '<span class="xftc-meet-location"> · ' . esc_html($res->location) . '</span>'; ?>
                    </td>
                    <td><?php echo $res->meet_date ? esc_html(date('M j, Y', strtotime($res->meet_date))) : '—'; ?></td>
                    <td>
                        <?php if ($res->is_personal_best) echo '<span class="xftc-badge xftc-badge--pb">⚡ PB</span> '; ?>
                        <?php if ($res->is_club_record)   echo '<span class="xftc-badge xftc-badge--cr">🏆 CR</span>'; ?>
                    </td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table>
        </div>
    </div>

    <?php endif; // has results ?>

</div><!-- /.xftc-profile -->

<script>
// Chart panel switching
document.querySelectorAll('.xftc-chart-tab').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var targetId = btn.dataset.chart;
        var container = btn.closest('.xftc-profile-section');
        container.querySelectorAll('.xftc-chart-tab').forEach(function(b){ b.classList.remove('xftc-chart-tab--active'); });
        container.querySelectorAll('.xftc-chart-panel').forEach(function(p){ p.classList.remove('xftc-chart-panel--active'); });
        btn.classList.add('xftc-chart-tab--active');
        var target = document.getElementById(targetId);
        if (target) target.classList.add('xftc-chart-panel--active');
    });
});

// Results table filter
function xftcFilterResults(query) {
    var q = query.toLowerCase();
    document.querySelectorAll('#xftc-results-table .xftc-results-row').forEach(function(row) {
        var ev   = row.dataset.event || '';
        var meet = row.dataset.meet  || '';
        row.style.display = (!q || ev.includes(q) || meet.includes(q)) ? '' : 'none';
    });
}
</script>
