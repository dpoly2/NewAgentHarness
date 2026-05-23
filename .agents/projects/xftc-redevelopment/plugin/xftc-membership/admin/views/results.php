<?php
/**
 * Admin View — Results Entry & Management
 * Variables: $meets, $athletes, $results (list)
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

global $wpdb;
$rt  = $wpdb->prefix . 'xftc_results';
$mt  = $wpdb->prefix . 'xftc_meets';
$at  = $wpdb->prefix . 'xftc_athletes';

$meets   = $wpdb->get_results( "SELECT * FROM {$mt} ORDER BY meet_date DESC LIMIT 50" );
$athletes = $wpdb->get_results( "SELECT * FROM {$at} ORDER BY last_name, first_name ASC" );

// Recent results list
$results = $wpdb->get_results(
    "SELECT r.*, m.name AS meet_name, m.meet_date, a.first_name, a.last_name
     FROM {$rt} r
     LEFT JOIN {$mt} m ON r.meet_id=m.id
     LEFT JOIN {$at} a ON r.athlete_id=a.id
     ORDER BY r.recorded_at DESC LIMIT 100"
);

// All track events and field events for dropdown
$track_events = XFTC_Results::$TRACK_EVENTS;
$field_events = XFTC_Results::$FIELD_EVENTS;
?>
<div class="wrap xftc-admin-wrap">
    <h1 class="xftc-page-title">
        <span class="dashicons dashicons-chart-line"></span>
        Results Entry & Management
    </h1>

    <div class="xftc-admin-two-col">

        <!-- ── Entry Form ─────────────────────────────────────── -->
        <div class="xftc-admin-col xftc-admin-col--form">
            <div class="xftc-widget">
                <div class="xftc-widget__header">
                    <h2>📝 Enter Result</h2>
                </div>
                <div class="xftc-widget__body">
                    <form id="xftc-result-entry-form">
                        <?php wp_nonce_field( 'xftc_admin_nonce', 'nonce' ); ?>

                        <div class="xftc-form-row">
                            <label>Meet <span class="required">*</span></label>
                            <select name="meet_id" required class="xftc-admin-select">
                                <option value="">— Select Meet —</option>
                                <?php foreach ($meets as $m) : ?>
                                    <option value="<?php echo $m->id; ?>">
                                        <?php echo esc_html($m->name . ' · ' . date('M j, Y', strtotime($m->meet_date))); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="xftc-form-row">
                            <label>Athlete <span class="required">*</span></label>
                            <select name="athlete_id" required class="xftc-admin-select">
                                <option value="">— Select Athlete —</option>
                                <?php foreach ($athletes as $a) : ?>
                                    <option value="<?php echo $a->id; ?>">
                                        <?php echo esc_html($a->first_name . ' ' . $a->last_name); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="xftc-form-row">
                            <label>Event Category <span class="required">*</span></label>
                            <select name="event_category" required class="xftc-admin-select" id="xftc-event-select"
                                onchange="xftcUpdateResultHint(this.value)">
                                <option value="">— Select Event —</option>
                                <optgroup label="Track Events">
                                    <?php foreach ($track_events as $ev) : ?>
                                        <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                    <?php endforeach; ?>
                                </optgroup>
                                <optgroup label="Field Events">
                                    <?php foreach ($field_events as $ev) : ?>
                                        <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                    <?php endforeach; ?>
                                </optgroup>
                                <optgroup label="Other">
                                    <option value="Custom">Custom / Other</option>
                                </optgroup>
                            </select>
                        </div>

                        <div class="xftc-form-row" id="xftc-custom-event-row" style="display:none;">
                            <label>Custom Event Name</label>
                            <input type="text" name="custom_event" placeholder="e.g. 60m Dash" class="xftc-admin-input"/>
                        </div>

                        <div class="xftc-form-row">
                            <label>Result <span class="required">*</span></label>
                            <input type="text" name="result_value" required class="xftc-admin-input"
                                placeholder="e.g. 12.34 or 1:45.60 or 25-6.5"
                                id="xftc-result-input"/>
                            <p class="xftc-form-hint" id="xftc-result-hint">
                                Track: MM:SS.ss or SS.ss &nbsp;·&nbsp; Field: FT-IN.dec (e.g. 25-6.5)
                            </p>
                        </div>

                        <div class="xftc-form-row-group">
                            <div class="xftc-form-row">
                                <label>Place / Finish</label>
                                <input type="number" name="placement" min="1" max="999"
                                    placeholder="e.g. 1" class="xftc-admin-input xftc-admin-input--sm"/>
                            </div>
                            <div class="xftc-form-row">
                                <label>Wind (m/s)</label>
                                <input type="text" name="wind" placeholder="+1.2 or -0.5"
                                    class="xftc-admin-input xftc-admin-input--sm"/>
                            </div>
                        </div>

                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="override_pb" value="1"/>
                                Force Personal Best flag (normally auto-detected)
                            </label>
                        </div>
                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="override_cr" value="1"/>
                                Force Club Record flag (normally auto-detected)
                            </label>
                        </div>

                        <div class="xftc-form-row">
                            <button type="submit" class="button button-primary xftc-btn-submit">
                                ✅ Save Result
                            </button>
                            <span class="xftc-form-feedback" id="xftc-result-feedback"></span>
                        </div>
                    </form>
                </div>
            </div>
        </div><!-- /.xftc-admin-col--form -->

        <!-- ── Recent Results ─────────────────────────────────── -->
        <div class="xftc-admin-col xftc-admin-col--list">
            <div class="xftc-widget">
                <div class="xftc-widget__header">
                    <h2>📋 Recent Results</h2>
                    <a href="<?php echo esc_url( home_url('/top-times/') ); ?>" target="_blank" class="xftc-widget__action">
                        View Public Leaderboard →
                    </a>
                </div>
                <div class="xftc-widget__body" style="overflow-x:auto;">
                    <?php if (empty($results)) : ?>
                        <p class="xftc-empty">No results entered yet. Use the form to add the first result.</p>
                    <?php else : ?>
                    <table class="xftc-widget-table">
                        <thead>
                            <tr>
                                <th>Athlete</th>
                                <th>Event</th>
                                <th>Result</th>
                                <th>Place</th>
                                <th>Meet</th>
                                <th>Date</th>
                                <th>Badges</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                        <?php foreach ($results as $res) : ?>
                            <tr>
                                <td>
                                    <strong><?php echo esc_html($res->first_name . ' ' . $res->last_name); ?></strong>
                                </td>
                                <td><?php echo esc_html($res->event_category); ?></td>
                                <td>
                                    <strong class="xftc-result-val"><?php echo esc_html($res->result_value); ?></strong>
                                </td>
                                <td><?php echo $res->placement ? '#' . $res->placement : '—'; ?></td>
                                <td><?php echo esc_html($res->meet_name ?? '—'); ?></td>
                                <td><?php echo $res->meet_date ? date('M j, Y', strtotime($res->meet_date)) : '—'; ?></td>
                                <td>
                                    <?php if ($res->is_personal_best) echo '<span class="xftc-badge xftc-badge--green">⚡ PB</span> '; ?>
                                    <?php if ($res->is_club_record)   echo '<span class="xftc-badge xftc-badge--orange">🏆 CR</span>'; ?>
                                </td>
                                <td>
                                    <a href="<?php echo esc_url(admin_url('admin.php?page=xftc-results&action=delete&id='.$res->id)); ?>"
                                       onclick="return confirm('Delete this result?');"
                                       class="xftc-delete-link">Delete</a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                    <?php endif; ?>
                </div>
            </div>
        </div><!-- /.xftc-admin-col--list -->

    </div><!-- /.xftc-admin-two-col -->
</div><!-- /.wrap -->

<script>
var fieldEvents = <?php echo json_encode(array_map('strtolower', $field_events)); ?>;

function xftcUpdateResultHint(val) {
    var lower   = val.toLowerCase();
    var isField = fieldEvents.some(function(ev) { return lower.indexOf(ev.split(' ')[0]) !== -1 || lower === ev; });
    var hint    = document.getElementById('xftc-result-hint');
    var input   = document.getElementById('xftc-result-input');
    var customRow = document.getElementById('xftc-custom-event-row');

    if (val === 'Custom') {
        customRow.style.display = 'block';
    } else {
        customRow.style.display = 'none';
    }

    if (isField) {
        hint.innerHTML = '<strong>Field Event:</strong> Enter as FT-IN.dec &nbsp;·&nbsp; e.g. <code>25-6.5</code> or <code>6-2</code>';
        input.placeholder = 'e.g. 25-6.5 (feet-inches)';
    } else {
        hint.innerHTML = '<strong>Track Event:</strong> Enter as MM:SS.ss or SS.ss &nbsp;·&nbsp; e.g. <code>12.34</code> or <code>1:45.60</code>';
        input.placeholder = 'e.g. 12.34 or 1:45.60';
    }
}

// AJAX form submit
document.getElementById('xftc-result-entry-form').addEventListener('submit', function(e) {
    e.preventDefault();
    var $form = jQuery(this);
    var $btn  = $form.find('.xftc-btn-submit');
    var $fb   = jQuery('#xftc-result-feedback');
    $btn.prop('disabled', true).text('Saving...');

    jQuery.post(ajaxurl, $form.serialize() + '&action=xftc_save_result', function(res) {
        if (res.success) {
            $fb.css('color','green').text('✅ Result saved! PB: ' + (res.data.is_pb ? 'Yes' : 'No') + ' · CR: ' + (res.data.is_cr ? 'Yes' : 'No'));
            $form[0].reset();
            setTimeout(function(){ location.reload(); }, 1500);
        } else {
            $fb.css('color','red').text('❌ ' + (res.data.message || 'Error saving result.'));
        }
        $btn.prop('disabled', false).text('✅ Save Result');
    }, 'json');
});
</script>
