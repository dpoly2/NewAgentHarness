<?php
/**
 * Admin View — Results Entry & Management (v2.2.0)
 * Three modes: Single Entry · Roster Bulk Entry · CSV Import
 * Variables injected by class-xftc-admin.php
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

global $wpdb;
$rt  = $wpdb->prefix . 'xftc_results';
$mt  = $wpdb->prefix . 'xftc_meets';
$at  = $wpdb->prefix . 'xftc_athletes';
$met = $wpdb->prefix . 'xftc_meet_entries';

$meets    = $wpdb->get_results( "SELECT * FROM {$mt} ORDER BY meet_date DESC LIMIT 50" );
$athletes = $wpdb->get_results( "SELECT * FROM {$at} ORDER BY last_name, first_name ASC" );

$recent = $wpdb->get_results(
    "SELECT r.*, m.name AS meet_name, m.meet_date, a.first_name, a.last_name
     FROM {$rt} r
     LEFT JOIN {$mt} m ON r.meet_id = m.id
     LEFT JOIN {$at} a ON r.athlete_id = a.id
     ORDER BY r.recorded_at DESC LIMIT 150"
);

$track_events = XFTC_Results::$TRACK_EVENTS;
$field_events = XFTC_Results::$FIELD_EVENTS;
$all_events   = array_merge( $track_events, $field_events );

// Handle CSV import POST
$import_message = '';
if ( isset($_POST['xftc_import_csv']) && check_admin_referer('xftc_import_csv') ) {
    $import_message = XFTC_Results::process_csv_import( $_POST, $_FILES );
}
?>
<div class="wrap xftc-admin-wrap">

    <!-- ── Page Header ──────────────────────────────────────────────── -->
    <div class="xftc-dashboard-header">
        <h1 class="xftc-page-title">
            <span class="dashicons dashicons-chart-line"></span>
            Results Entry &amp; Import
        </h1>
        <div>
            <a href="<?php echo esc_url( home_url('/top-times/') ); ?>" target="_blank" class="button">
                🏆 View Public Leaderboard ↗
            </a>
        </div>
    </div>

    <?php if ($import_message) : ?>
        <div class="notice notice-<?php echo strpos($import_message,'Error') !== false ? 'error' : 'success'; ?> is-dismissible">
            <p><?php echo wp_kses_post($import_message); ?></p>
        </div>
    <?php endif; ?>

    <!-- ── Mode Tabs ────────────────────────────────────────────────── -->
    <div class="xftc-mode-tabs">
        <button class="xftc-mode-tab xftc-mode-tab--active" data-mode="single">
            ✏️ Single Entry
        </button>
        <button class="xftc-mode-tab" data-mode="roster">
            📋 Roster Bulk Entry
        </button>
        <button class="xftc-mode-tab" data-mode="import">
            📥 CSV / Import
        </button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         MODE 1 — SINGLE ENTRY (desktop + mobile-optimized)
         ══════════════════════════════════════════════════════════════ -->
    <div class="xftc-mode-panel xftc-mode-panel--active" id="mode-single">
        <div class="xftc-admin-two-col">

            <!-- Entry Form -->
            <div class="xftc-admin-col">
                <div class="xftc-widget">
                    <div class="xftc-widget__header">
                        <h2>✏️ Enter Single Result</h2>
                        <span class="xftc-mobile-tip">📱 Mobile-friendly</span>
                    </div>
                    <div class="xftc-widget__body">
                        <form id="xftc-single-entry-form" autocomplete="off">
                            <?php wp_nonce_field('xftc_admin_nonce','nonce'); ?>

                            <div class="xftc-form-row">
                                <label>Meet <span class="req">*</span></label>
                                <select name="meet_id" required class="xftc-admin-select" id="se-meet">
                                    <option value="">— Select Meet —</option>
                                    <?php foreach ($meets as $m) : ?>
                                        <option value="<?php echo $m->id; ?>">
                                            <?php echo esc_html($m->name . ' · ' . date('M j, Y', strtotime($m->meet_date))); ?>
                                        </option>
                                    <?php endforeach; ?>
                                </select>
                            </div>

                            <div class="xftc-form-row">
                                <label>Athlete <span class="req">*</span></label>
                                <select name="athlete_id" required class="xftc-admin-select" id="se-athlete">
                                    <option value="">— Select Athlete —</option>
                                    <?php foreach ($athletes as $a) : ?>
                                        <option value="<?php echo $a->id; ?>">
                                            <?php echo esc_html($a->last_name . ', ' . $a->first_name); ?>
                                        </option>
                                    <?php endforeach; ?>
                                </select>
                            </div>

                            <div class="xftc-form-row">
                                <label>Event <span class="req">*</span></label>
                                <select name="event_category" required class="xftc-admin-select"
                                    id="se-event" onchange="xftcUpdateHint(this,'se-hint','se-result')">
                                    <option value="">— Select Event —</option>
                                    <optgroup label="Track">
                                        <?php foreach ($track_events as $ev) : ?>
                                            <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                        <?php endforeach; ?>
                                    </optgroup>
                                    <optgroup label="Field">
                                        <?php foreach ($field_events as $ev) : ?>
                                            <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                        <?php endforeach; ?>
                                    </optgroup>
                                    <option value="Custom">Custom / Other</option>
                                </select>
                            </div>

                            <div class="xftc-form-row" id="se-custom-row" style="display:none;">
                                <label>Custom Event Name</label>
                                <input type="text" name="custom_event" class="xftc-admin-input"
                                    placeholder="e.g. 55m Dash"/>
                            </div>

                            <div class="xftc-form-row">
                                <label>Result <span class="req">*</span></label>
                                <input type="text" name="result_value" required
                                    id="se-result" class="xftc-admin-input xftc-result-input"
                                    placeholder="e.g. 12.34 or 1:45.60 or 25-6.5"
                                    inputmode="decimal" autocomplete="off"/>
                                <p class="xftc-form-hint" id="se-hint">
                                    Track: SS.ss or MM:SS.ss &nbsp;·&nbsp; Field: FT-IN.d
                                </p>
                            </div>

                            <div class="xftc-form-row-group">
                                <div class="xftc-form-row">
                                    <label>Place</label>
                                    <input type="number" name="placement" min="1" max="999"
                                        placeholder="1" class="xftc-admin-input xftc-admin-input--sm"
                                        inputmode="numeric"/>
                                </div>
                                <div class="xftc-form-row">
                                    <label>Wind (m/s)</label>
                                    <input type="text" name="wind"
                                        placeholder="+1.2" class="xftc-admin-input xftc-admin-input--sm"/>
                                </div>
                            </div>

                            <div class="xftc-form-row xftc-form-row--inline">
                                <label class="xftc-checkbox-label">
                                    <input type="checkbox" name="override_pb" value="1"/>
                                    Force PB flag
                                </label>
                                <label class="xftc-checkbox-label">
                                    <input type="checkbox" name="override_cr" value="1"/>
                                    Force CR flag
                                </label>
                            </div>

                            <div class="xftc-form-row">
                                <button type="submit" class="button button-primary xftc-btn-lg">
                                    ✅ Save Result
                                </button>
                                <div class="xftc-form-feedback" id="se-feedback"></div>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Mobile tip card -->
                <div class="xftc-tip-card">
                    <strong>📱 Using on mobile at a meet?</strong><br/>
                    Open <code><?php echo esc_url(admin_url('admin.php?page=xftc-results')); ?></code>
                    in your phone browser. The form is touch-optimized with large inputs and numeric keyboards
                    for result entry.
                </div>
            </div>

            <!-- Recent Results List -->
            <div class="xftc-admin-col">
                <div class="xftc-widget">
                    <div class="xftc-widget__header">
                        <h2>📋 Recent Results</h2>
                        <input type="text" id="results-filter" placeholder="Filter…"
                            onkeyup="xftcFilterTable(this,'results-tbody')"
                            style="font-size:12px;padding:3px 8px;border:1px solid #ddd;border-radius:4px;"/>
                    </div>
                    <div class="xftc-widget__body" style="overflow-x:auto;max-height:600px;overflow-y:auto;">
                        <?php if (empty($recent)) : ?>
                            <p class="xftc-empty">No results yet. Enter the first one →</p>
                        <?php else : ?>
                        <table class="xftc-widget-table">
                            <thead>
                                <tr>
                                    <th>Athlete</th><th>Event</th><th>Result</th>
                                    <th>Place</th><th>Meet</th><th>Badges</th><th></th>
                                </tr>
                            </thead>
                            <tbody id="results-tbody">
                            <?php foreach ($recent as $r) : ?>
                                <tr>
                                    <td><strong><?php echo esc_html($r->last_name.', '.$r->first_name); ?></strong></td>
                                    <td><?php echo esc_html($r->event_category); ?></td>
                                    <td><strong><?php echo esc_html($r->result_value); ?></strong></td>
                                    <td><?php echo $r->placement ? '#'.$r->placement : '—'; ?></td>
                                    <td><?php echo esc_html($r->meet_name ?? '—'); ?></td>
                                    <td>
                                        <?php if ($r->is_personal_best) echo '<span class="xftc-badge xftc-badge--green">⚡ PB</span> '; ?>
                                        <?php if ($r->is_club_record)   echo '<span class="xftc-badge xftc-badge--orange">🏆 CR</span>'; ?>
                                    </td>
                                    <td>
                                        <a href="<?php echo esc_url(admin_url('admin.php?page=xftc-results&action=delete&id='.$r->id.'&_wpnonce='.wp_create_nonce('xftc_delete_result'))); ?>"
                                           onclick="return confirm('Delete this result?');"
                                           style="color:#cc0000;font-size:11px;">✕</a>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>
                        <?php endif; ?>
                    </div>
                </div>
            </div>

        </div>
    </div><!-- /#mode-single -->


    <!-- ══════════════════════════════════════════════════════════════
         MODE 2 — ROSTER BULK ENTRY (one event, all athletes at once)
         ══════════════════════════════════════════════════════════════ -->
    <div class="xftc-mode-panel" id="mode-roster">
        <div class="xftc-widget">
            <div class="xftc-widget__header">
                <h2>📋 Roster Bulk Entry</h2>
                <span class="xftc-tip-inline">Select a meet + event → enter results for all registered athletes at once</span>
            </div>
            <div class="xftc-widget__body">

                <!-- Step 1: Select meet + event -->
                <div class="xftc-bulk-setup">
                    <div class="xftc-form-row-group">
                        <div class="xftc-form-row">
                            <label>Meet <span class="req">*</span></label>
                            <select class="xftc-admin-select" id="bulk-meet" onchange="xftcLoadRoster()">
                                <option value="">— Select Meet —</option>
                                <?php foreach ($meets as $m) : ?>
                                    <option value="<?php echo $m->id; ?>">
                                        <?php echo esc_html($m->name . ' · ' . date('M j, Y', strtotime($m->meet_date))); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <div class="xftc-form-row">
                            <label>Event <span class="req">*</span></label>
                            <select class="xftc-admin-select" id="bulk-event" onchange="xftcLoadRoster()">
                                <option value="">— Select Event —</option>
                                <optgroup label="Track">
                                    <?php foreach ($track_events as $ev) : ?>
                                        <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                    <?php endforeach; ?>
                                </optgroup>
                                <optgroup label="Field">
                                    <?php foreach ($field_events as $ev) : ?>
                                        <option value="<?php echo esc_attr($ev); ?>"><?php echo esc_html($ev); ?></option>
                                    <?php endforeach; ?>
                                </optgroup>
                            </select>
                        </div>
                        <div class="xftc-form-row">
                            <label>Division Filter</label>
                            <select class="xftc-admin-select" id="bulk-division" onchange="xftcLoadRoster()">
                                <option value="">All Divisions</option>
                                <?php foreach (array_keys(XFTC_Results::$DIVISIONS) as $div) : ?>
                                    <option value="<?php echo esc_attr($div); ?>"><?php echo esc_html($div); ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                    </div>
                    <button class="button" onclick="xftcAddAllAthletes()" type="button">
                        ➕ Load All Club Athletes
                    </button>
                </div>

                <!-- Roster entry grid -->
                <div id="xftc-roster-grid" style="display:none;">
                    <div class="xftc-roster-entry-header">
                        <span>Rank</span>
                        <span>Athlete</span>
                        <span>Result</span>
                        <span>Place</span>
                        <span>Wind</span>
                        <span>PB?</span>
                        <span></span>
                    </div>
                    <div id="xftc-roster-rows">
                        <!-- Rows injected by JS -->
                    </div>
                    <div class="xftc-roster-actions">
                        <button type="button" class="button" onclick="xftcAddRosterRow()">
                            ➕ Add Row
                        </button>
                        <button type="button" class="button button-primary" onclick="xftcSaveRoster()" id="bulk-save-btn">
                            ✅ Save All Results
                        </button>
                        <span id="bulk-feedback" class="xftc-form-feedback"></span>
                    </div>
                </div>

                <!-- All athletes fallback (if no meet registration data) -->
                <div id="xftc-all-athletes-data" style="display:none;"
                    data-athletes="<?php echo esc_attr(json_encode(array_map(fn($a) => [
                        'id'   => $a->id,
                        'name' => $a->last_name . ', ' . $a->first_name,
                        'dob'  => $a->dob ?? '',
                    ], $athletes))); ?>">
                </div>

            </div>
        </div>
    </div><!-- /#mode-roster -->


    <!-- ══════════════════════════════════════════════════════════════
         MODE 3 — CSV / IMPORT
         ══════════════════════════════════════════════════════════════ -->
    <div class="xftc-mode-panel" id="mode-import">

        <div class="xftc-import-grid">

            <!-- ── Upload CSV file ──────────────────────────── -->
            <div class="xftc-widget">
                <div class="xftc-widget__header"><h2>📁 Upload CSV File</h2></div>
                <div class="xftc-widget__body">
                    <p class="xftc-import-desc">
                        Upload a CSV exported from your timing system, spreadsheet, or hand entry.
                        <a href="<?php echo esc_url(admin_url('admin.php?page=xftc-results&action=download_template')); ?>">
                            Download template →
                        </a>
                    </p>

                    <form method="POST" enctype="multipart/form-data" id="xftc-csv-upload-form">
                        <?php wp_nonce_field('xftc_import_csv'); ?>
                        <input type="hidden" name="xftc_import_csv" value="1"/>
                        <input type="hidden" name="import_mode" value="file"/>

                        <div class="xftc-form-row">
                            <label>Meet <span class="req">*</span></label>
                            <select name="meet_id" required class="xftc-admin-select">
                                <option value="">— Select Meet —</option>
                                <?php foreach ($meets as $m) : ?>
                                    <option value="<?php echo $m->id; ?>">
                                        <?php echo esc_html($m->name . ' · ' . date('M j, Y', strtotime($m->meet_date))); ?>
                                    </option>
                                <?php endforeach; ?>
                            </select>
                        </div>

                        <div class="xftc-dropzone" id="csv-dropzone">
                            <input type="file" name="csv_file" id="csv-file-input" accept=".csv,.txt"
                                style="display:none;" onchange="xftcPreviewCSV(this)"/>
                            <div class="xftc-dropzone__inner" onclick="document.getElementById('csv-file-input').click()">
                                <span class="xftc-dropzone__icon">📂</span>
                                <p>Drag &amp; drop your CSV here<br/>or <strong>click to browse</strong></p>
                                <p class="xftc-dropzone__types">Accepts .csv or .txt · Max 2MB</p>
                            </div>
                            <div id="csv-file-name" style="display:none;padding:8px 12px;font-size:13px;color:#27ae60;"></div>
                        </div>

                        <div id="csv-preview-wrap" style="display:none;margin:12px 0;">
                            <strong style="font-size:13px;">Preview (first 5 rows):</strong>
                            <div style="overflow-x:auto;margin-top:6px;">
                                <table class="xftc-widget-table" id="csv-preview-table" style="font-size:11px;"></table>
                            </div>
                        </div>

                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="skip_duplicates" value="1" checked/>
                                Skip duplicate results (same athlete + event + meet)
                            </label>
                        </div>
                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="auto_detect_pb" value="1" checked/>
                                Auto-detect Personal Bests &amp; Club Records on import
                            </label>
                        </div>

                        <div class="xftc-form-row">
                            <button type="submit" class="button button-primary">
                                📥 Import CSV
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- ── Paste CSV text ───────────────────────────── -->
            <div class="xftc-widget">
                <div class="xftc-widget__header"><h2>📋 Paste CSV Data</h2></div>
                <div class="xftc-widget__body">
                    <p class="xftc-import-desc">
                        Copy results from a spreadsheet and paste directly below.
                        Columns: <code>athlete_last, athlete_first, event, result, place, wind</code>
                    </p>

                    <form method="POST" id="xftc-paste-form">
                        <?php wp_nonce_field('xftc_import_csv'); ?>
                        <input type="hidden" name="xftc_import_csv" value="1"/>
                        <input type="hidden" name="import_mode" value="paste"/>

                        <div class="xftc-form-row">
                            <label>Meet <span class="req">*</span></label>
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
                            <label>Paste CSV rows</label>
                            <textarea name="csv_paste" rows="10"
                                class="xftc-admin-textarea"
                                placeholder="Smith,John,100m,12.34,1,+1.2
Doe,Jane,200m,26.50,2,0.0
Williams,Marcus,Long Jump,22-6.5,1,+0.8"></textarea>
                            <p class="xftc-form-hint">
                                One row per result. Header row optional. Delimiter: comma or tab.
                            </p>
                        </div>

                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="has_header" value="1"/>
                                First row is a header (skip it)
                            </label>
                        </div>
                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="skip_duplicates" value="1" checked/>
                                Skip duplicates
                            </label>
                        </div>
                        <div class="xftc-form-row">
                            <label class="xftc-checkbox-label">
                                <input type="checkbox" name="auto_detect_pb" value="1" checked/>
                                Auto-detect PBs &amp; Club Records
                            </label>
                        </div>

                        <div class="xftc-form-row">
                            <button type="submit" class="button button-primary">
                                📋 Import Pasted Data
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- ── API / Integration info ───────────────────── -->
            <div class="xftc-widget xftc-widget--full">
                <div class="xftc-widget__header"><h2>🔌 REST API Import</h2></div>
                <div class="xftc-widget__body">
                    <p>Post results programmatically from timing systems, HY-TEK, FinishLynx, or custom scripts.</p>

                    <div class="xftc-api-endpoint-block">
                        <div class="xftc-api-row">
                            <span class="xftc-api-method">POST</span>
                            <code class="xftc-api-url"><?php echo esc_url(rest_url('xftc/v1/results')); ?></code>
                        </div>
                        <div class="xftc-api-row">
                            <span class="xftc-api-method xftc-api-method--get">POST</span>
                            <code class="xftc-api-url"><?php echo esc_url(rest_url('xftc/v1/results/import')); ?></code>
                            <span class="xftc-api-note">Bulk import (array of results)</span>
                        </div>
                    </div>

                    <p><strong>Auth:</strong> WordPress Application Password. Generate one at
                        <a href="<?php echo esc_url(admin_url('profile.php#application-passwords-section')); ?>">
                            Users → Your Profile → Application Passwords
                        </a>
                    </p>

                    <details class="xftc-code-details">
                        <summary>Single result payload example</summary>
                        <pre class="xftc-code">{
  "meet_id": 5,
  "athlete_id": 12,
  "event_category": "100m",
  "result_value": "12.34",
  "placement": 1,
  "wind": "+1.2"
}</pre>
                    </details>

                    <details class="xftc-code-details">
                        <summary>Bulk import payload example (/results/import)</summary>
                        <pre class="xftc-code">{
  "meet_id": 5,
  "results": [
    { "athlete_id": 12, "event_category": "100m", "result_value": "12.34", "placement": 1 },
    { "athlete_id": 14, "event_category": "100m", "result_value": "12.89", "placement": 2 },
    { "athlete_id": 9,  "event_category": "Long Jump", "result_value": "22-6.5", "placement": 1 }
  ]
}</pre>
                    </details>

                    <details class="xftc-code-details">
                        <summary>cURL example</summary>
                        <pre class="xftc-code">curl -X POST <?php echo esc_url(rest_url('xftc/v1/results')); ?> \
  -H "Authorization: Basic BASE64_OF_USER:APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"meet_id":5,"athlete_id":12,"event_category":"100m","result_value":"12.34","placement":1}'</pre>
                    </details>

                    <details class="xftc-code-details">
                        <summary>Supported CSV column formats</summary>
                        <pre class="xftc-code">Format A (match by name):
  athlete_last, athlete_first, event, result, place, wind

Format B (match by athlete_id):
  athlete_id, event, result, place, wind

Format C (HY-TEK style, auto-detected):
  Place, Name, Age, Team, Result, Wind</pre>
                    </details>
                </div>
            </div>

        </div><!-- /.xftc-import-grid -->
    </div><!-- /#mode-import -->

</div><!-- /.wrap -->

<!-- ══════════════════════════════════════════════════════════════
     JAVASCRIPT
     ══════════════════════════════════════════════════════════════ -->
<script>
var XFTC_NONCE  = '<?php echo wp_create_nonce('xftc_admin_nonce'); ?>';
var XFTC_AJAX   = '<?php echo admin_url('admin-ajax.php'); ?>';
var fieldEvents = <?php echo json_encode(array_map('strtolower', $field_events)); ?>;
var allAthletes = JSON.parse(document.getElementById('xftc-all-athletes-data').dataset.athletes || '[]');

/* ── Mode tabs ─────────────────────────────────────────────────── */
document.querySelectorAll('.xftc-mode-tab').forEach(function(btn){
    btn.addEventListener('click', function(){
        document.querySelectorAll('.xftc-mode-tab').forEach(function(b){ b.classList.remove('xftc-mode-tab--active'); });
        document.querySelectorAll('.xftc-mode-panel').forEach(function(p){ p.classList.remove('xftc-mode-panel--active'); });
        btn.classList.add('xftc-mode-tab--active');
        document.getElementById('mode-' + btn.dataset.mode).classList.add('xftc-mode-panel--active');
    });
});

/* ── Event hint helper ─────────────────────────────────────────── */
function xftcIsField(evName) {
    var kw = ['jump','vault','put','throw','discus','javelin','hammer','weight'];
    var lower = evName.toLowerCase();
    return kw.some(function(k){ return lower.indexOf(k) !== -1; });
}
function xftcUpdateHint(sel, hintId, inputId) {
    var val = sel.value;
    var hint  = document.getElementById(hintId);
    var input = document.getElementById(inputId);
    var customRow = document.getElementById('se-custom-row');
    if (customRow) customRow.style.display = val === 'Custom' ? 'block' : 'none';
    if (!hint || !input) return;
    if (xftcIsField(val)) {
        hint.innerHTML  = '<strong>Field Event:</strong> Enter as FT-IN.d &nbsp;·&nbsp; e.g. <code>22-6.5</code>';
        input.placeholder = '22-6.5 (feet-inches)';
    } else {
        hint.innerHTML  = '<strong>Track Event:</strong> SS.ss or MM:SS.ss &nbsp;·&nbsp; e.g. <code>12.34</code> or <code>1:45.60</code>';
        input.placeholder = '12.34 or 1:45.60';
    }
}

/* ── Single entry AJAX submit ──────────────────────────────────── */
document.getElementById('xftc-single-entry-form').addEventListener('submit', function(e){
    e.preventDefault();
    var $form = jQuery(this);
    var $btn  = $form.find('.xftc-btn-lg');
    var $fb   = jQuery('#se-feedback');
    $btn.prop('disabled',true).text('Saving…');
    jQuery.post(XFTC_AJAX, $form.serialize() + '&action=xftc_save_result&nonce='+XFTC_NONCE, function(res){
        if (res.success) {
            $fb.css('color','#27ae60').html('✅ Saved! <strong>' +
                res.data.event + '</strong> · ' + res.data.result +
                (res.data.is_pb ? ' · <span style="color:#27ae60">⚡ PB</span>' : '') +
                (res.data.is_cr ? ' · <span style="color:#856404">🏆 CR</span>' : ''));
            $form[0].reset();
            setTimeout(function(){ location.reload(); }, 2000);
        } else {
            $fb.css('color','#cc0000').text('❌ ' + (res.data.message || 'Error saving.'));
        }
        $btn.prop('disabled',false).text('✅ Save Result');
    },'json').fail(function(){ $fb.css('color','#cc0000').text('❌ Network error.'); $btn.prop('disabled',false).text('✅ Save Result'); });
});

/* ── Roster bulk entry ─────────────────────────────────────────── */
var rosterRowCount = 0;

function xftcLoadRoster() {
    var meetId   = document.getElementById('bulk-meet').value;
    var eventVal = document.getElementById('bulk-event').value;
    var divVal   = document.getElementById('bulk-division').value;
    if (!meetId || !eventVal) return;

    // Load athletes registered for this meet via AJAX
    jQuery.post(XFTC_AJAX, {
        action: 'xftc_get_meet_athletes', nonce: XFTC_NONCE,
        meet_id: meetId, division: divVal
    }, function(res) {
        var athletes = (res.success && res.data.length) ? res.data : allAthletes;
        xftcBuildRosterGrid(athletes, eventVal);
    },'json').fail(function(){ xftcBuildRosterGrid(allAthletes, eventVal); });
}

function xftcBuildRosterGrid(athletes, eventVal) {
    var isField = xftcIsField(eventVal);
    var container = document.getElementById('xftc-roster-rows');
    container.innerHTML = '';
    rosterRowCount = 0;
    athletes.forEach(function(a, i) {
        xftcAddRosterRow(a.id, a.name, isField, i+1);
    });
    document.getElementById('xftc-roster-grid').style.display = 'block';
}

function xftcAddRosterRow(athleteId, athleteName, isField, rank) {
    athleteId   = athleteId   || '';
    athleteName = athleteName || '';
    if (isField === undefined) {
        var evVal = document.getElementById('bulk-event').value;
        isField = xftcIsField(evVal);
    }
    rosterRowCount++;
    var ph = isField ? '22-6.5' : '12.34';
    var html = '<div class="xftc-roster-entry-row" id="roster-row-'+rosterRowCount+'">' +
        '<span class="xftc-roster-rank">' + (rank || rosterRowCount) + '</span>' +
        '<div class="xftc-roster-athlete">' +
            (athleteId
                ? '<span class="xftc-roster-name">' + athleteName + '</span><input type="hidden" name="athlete_id[]" value="' + athleteId + '"/>'
                : '<select name="athlete_id[]" class="xftc-admin-select xftc-admin-select--sm">' +
                    '<option value="">— Athlete —</option>' +
                    allAthletes.map(function(a){ return '<option value="'+a.id+'">'+a.name+'</option>'; }).join('') +
                  '</select>'
            ) +
        '</div>' +
        '<input type="text" name="result_value[]" class="xftc-admin-input xftc-result-input xftc-admin-input--sm" placeholder="' + ph + '" inputmode="decimal"/>' +
        '<input type="number" name="placement[]" class="xftc-admin-input xftc-admin-input--xs" placeholder="' + rosterRowCount + '" min="1" inputmode="numeric"/>' +
        '<input type="text"   name="wind[]"      class="xftc-admin-input xftc-admin-input--xs" placeholder="+0.0"/>' +
        '<label style="display:flex;align-items:center;gap:4px;font-size:12px;"><input type="checkbox" name="pb_flag['+rosterRowCount+']" value="1"/> PB?</label>' +
        '<button type="button" onclick="this.closest(\'.xftc-roster-entry-row\').remove()" style="background:none;border:none;color:#cc0000;cursor:pointer;font-size:16px;" title="Remove">✕</button>' +
    '</div>';
    document.getElementById('xftc-roster-rows').insertAdjacentHTML('beforeend', html);
}

function xftcAddAllAthletes() {
    var evVal = document.getElementById('bulk-event').value;
    var isField = xftcIsField(evVal);
    xftcBuildRosterGrid(allAthletes, evVal);
}

function xftcSaveRoster() {
    var meetId = document.getElementById('bulk-meet').value;
    var evVal  = document.getElementById('bulk-event').value;
    if (!meetId || !evVal) { alert('Please select a meet and event first.'); return; }

    var $btn = jQuery('#bulk-save-btn');
    var $fb  = jQuery('#bulk-feedback');
    $btn.prop('disabled',true).text('Saving…');

    var rows  = document.querySelectorAll('.xftc-roster-entry-row');
    var batch = [];
    rows.forEach(function(row) {
        var aid  = row.querySelector('[name="athlete_id[]"]')?.value;
        var res  = row.querySelector('[name="result_value[]"]')?.value;
        var plc  = row.querySelector('[name="placement[]"]')?.value;
        var wind = row.querySelector('[name="wind[]"]')?.value;
        if (aid && res && res.trim() !== '') {
            batch.push({ athlete_id: aid, result_value: res.trim(), placement: plc||'', wind: wind||'' });
        }
    });

    if (!batch.length) { $btn.prop('disabled',false).text('✅ Save All Results'); alert('No results to save.'); return; }

    jQuery.post(XFTC_AJAX, {
        action: 'xftc_save_roster_results',
        nonce:  XFTC_NONCE,
        meet_id: meetId,
        event_category: evVal,
        results: JSON.stringify(batch)
    }, function(res) {
        if (res.success) {
            $fb.css('color','#27ae60').text('✅ Saved ' + res.data.saved + ' results · ' + res.data.pbs + ' PBs · ' + res.data.crs + ' Club Records');
            setTimeout(function(){ location.reload(); }, 2500);
        } else {
            $fb.css('color','#cc0000').text('❌ ' + (res.data.message || 'Error saving.'));
        }
        $btn.prop('disabled',false).text('✅ Save All Results');
    },'json').fail(function(){ $fb.css('color','#cc0000').text('❌ Network error.'); $btn.prop('disabled',false).text('✅ Save All Results'); });
}

/* ── Table filter ──────────────────────────────────────────────── */
function xftcFilterTable(input, tbodyId) {
    var q = input.value.toLowerCase();
    document.querySelectorAll('#' + tbodyId + ' tr').forEach(function(row){
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

/* ── CSV file preview ──────────────────────────────────────────── */
function xftcPreviewCSV(input) {
    var file = input.files[0];
    if (!file) return;
    document.getElementById('csv-file-name').style.display = 'block';
    document.getElementById('csv-file-name').textContent = '✅ ' + file.name + ' (' + (file.size/1024).toFixed(1) + ' KB)';
    var reader = new FileReader();
    reader.onload = function(e) {
        var lines = e.target.result.split('\n').slice(0,6);
        var table = document.getElementById('csv-preview-table');
        table.innerHTML = lines.map(function(line, i){
            var cells = line.split(',');
            var tag = i === 0 ? 'th' : 'td';
            return '<tr>' + cells.map(function(c){ return '<'+tag+'>' + c.trim() + '</'+tag+'>'; }).join('') + '</tr>';
        }).join('');
        document.getElementById('csv-preview-wrap').style.display = 'block';
    };
    reader.readAsText(file);
}

/* ── Drag & drop ───────────────────────────────────────────────── */
var dropzone = document.getElementById('csv-dropzone');
if (dropzone) {
    dropzone.addEventListener('dragover', function(e){ e.preventDefault(); dropzone.classList.add('xftc-dropzone--over'); });
    dropzone.addEventListener('dragleave', function(){ dropzone.classList.remove('xftc-dropzone--over'); });
    dropzone.addEventListener('drop', function(e){
        e.preventDefault(); dropzone.classList.remove('xftc-dropzone--over');
        var file = e.dataTransfer.files[0];
        if (file) { document.getElementById('csv-file-input').files = e.dataTransfer.files; xftcPreviewCSV(document.getElementById('csv-file-input')); }
    });
}
</script>
