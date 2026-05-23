<?php
/**
 * Public View — Leaderboard (Top Times & Marks)
 * Mimics Athletic.net / MileSplit structure
 * Variables: $data (grouped results), $events, $seasons, $atts
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

// Canonical event order
$track_events = XFTC_Results::$TRACK_EVENTS;
$field_events = XFTC_Results::$FIELD_EVENTS;
$all_events   = array_merge( $track_events, $field_events );

// Sort $data by canonical event order
$sorted_data = [];
foreach ( $all_events as $ev ) {
    if ( isset( $data[$ev] ) ) $sorted_data[$ev] = $data[$ev];
}
// Append any non-canonical events at end
foreach ( $data as $ev => $divs ) {
    if ( ! isset( $sorted_data[$ev] ) ) $sorted_data[$ev] = $divs;
}

// Division order
$division_order = array_keys( XFTC_Results::$DIVISIONS );
$current_gender   = sanitize_text_field( $_GET['gender']   ?? $atts['gender']   ?? '' );
$current_division = sanitize_text_field( $_GET['division'] ?? $atts['division'] ?? '' );
$current_event    = sanitize_text_field( $_GET['event']    ?? $atts['event']    ?? '' );
$current_limit    = intval( $_GET['limit'] ?? $atts['limit'] ?? 20 );
?>

<div class="xftc-leaderboard" id="xftc-leaderboard">

    <!-- ── Page Header ─────────────────────────────────────────────────── -->
    <div class="xftc-lb-header">
        <div class="xftc-lb-header__title">
            <h2>🏃 Top Times & Marks</h2>
            <p>Xtreme Force Track Club — All-Time Club Leaderboard</p>
        </div>
    </div>

    <!-- ── Filter Bar ──────────────────────────────────────────────────── -->
    <form class="xftc-lb-filters" id="xftc-lb-filter-form" method="GET">
        <div class="xftc-lb-filters__group">
            <label>Gender</label>
            <div class="xftc-filter-pills" role="group">
                <button type="submit" name="gender" value="" class="xftc-pill <?php echo $current_gender === '' ? 'xftc-pill--active' : ''; ?>">All</button>
                <button type="submit" name="gender" value="male"   class="xftc-pill <?php echo $current_gender === 'male'   ? 'xftc-pill--active' : ''; ?>">Boys</button>
                <button type="submit" name="gender" value="female" class="xftc-pill <?php echo $current_gender === 'female' ? 'xftc-pill--active' : ''; ?>">Girls</button>
            </div>
        </div>
        <div class="xftc-lb-filters__group">
            <label>Division</label>
            <div class="xftc-filter-pills" role="group">
                <button type="submit" name="division" value="" class="xftc-pill <?php echo $current_division === '' ? 'xftc-pill--active' : ''; ?>">All Divisions</button>
                <?php foreach ( $division_order as $div ) : ?>
                    <button type="submit" name="division" value="<?php echo esc_attr($div); ?>"
                        class="xftc-pill <?php echo $current_division === $div ? 'xftc-pill--active' : ''; ?>">
                        <?php echo esc_html($div); ?>
                    </button>
                <?php endforeach; ?>
            </div>
        </div>
        <div class="xftc-lb-filters__group">
            <label>Event</label>
            <select name="event" onchange="this.form.submit()" class="xftc-select">
                <option value="">All Events</option>
                <optgroup label="Track">
                    <?php foreach ( $track_events as $ev ) : ?>
                        <option value="<?php echo esc_attr($ev); ?>" <?php selected( $current_event, $ev ); ?>><?php echo esc_html($ev); ?></option>
                    <?php endforeach; ?>
                </optgroup>
                <optgroup label="Field">
                    <?php foreach ( $field_events as $ev ) : ?>
                        <option value="<?php echo esc_attr($ev); ?>" <?php selected( $current_event, $ev ); ?>><?php echo esc_html($ev); ?></option>
                    <?php endforeach; ?>
                </optgroup>
            </select>
        </div>
        <div class="xftc-lb-filters__group">
            <label>Show Top</label>
            <div class="xftc-filter-pills" role="group">
                <?php foreach ([10, 15, 20] as $n) : ?>
                    <button type="submit" name="limit" value="<?php echo $n; ?>"
                        class="xftc-pill <?php echo $current_limit == $n ? 'xftc-pill--active' : ''; ?>">
                        Top <?php echo $n; ?>
                    </button>
                <?php endforeach; ?>
            </div>
        </div>
        <?php
        // Preserve other GET params as hidden fields
        foreach (['gender','division','event','limit'] as $param) {
            // passed via buttons/selects above — skip
        } ?>
    </form>

    <!-- ── Results Count ────────────────────────────────────────────────── -->
    <?php
    $total_entries = 0;
    foreach ($sorted_data as $divs) foreach ($divs as $rows) $total_entries += count($rows);
    ?>
    <div class="xftc-lb-summary">
        <?php if ($total_entries) : ?>
            Showing <strong><?php echo $total_entries; ?></strong> results across
            <strong><?php echo count($sorted_data); ?></strong> events
            <?php if ($current_division) echo '· <strong>' . esc_html($current_division) . '</strong>'; ?>
            <?php if ($current_gender === 'male') echo '· <strong>Boys</strong>'; elseif ($current_gender === 'female') echo '· <strong>Girls</strong>'; ?>
        <?php else : ?>
            <em>No results found. Check back after meets are recorded.</em>
        <?php endif; ?>
    </div>

    <?php if ( empty( $sorted_data ) ) : ?>
        <div class="xftc-lb-empty">
            <span class="xftc-lb-empty__icon">🏆</span>
            <h3>No Results Yet</h3>
            <p>Results will appear here once meets are completed and recorded by a coach.</p>
        </div>
    <?php endif; ?>

    <!-- ── Event Tables ─────────────────────────────────────────────────── -->
    <?php foreach ( $sorted_data as $event => $divisions ) :
        $is_field = XFTC_Results::is_field_event( $event );
        $is_relay = strpos( strtolower($event), 'relay' ) !== false || strpos( strtolower($event), '4x' ) !== false;

        // Sort divisions in canonical order
        $sorted_divs = [];
        foreach ( $division_order as $d ) {
            if ( isset($divisions[$d]) ) $sorted_divs[$d] = $divisions[$d];
        }
        if ( isset($divisions['Open']) ) $sorted_divs['Open'] = $divisions['Open'];
    ?>
    <div class="xftc-lb-event-section" id="event-<?php echo esc_attr( sanitize_title($event) ); ?>">

        <!-- Event Header -->
        <div class="xftc-lb-event-header">
            <div class="xftc-lb-event-header__left">
                <span class="xftc-lb-event-icon"><?php echo $is_field ? '🎽' : '⏱️'; ?></span>
                <h3 class="xftc-lb-event-name"><?php echo esc_html($event); ?></h3>
                <span class="xftc-lb-event-type"><?php echo $is_field ? 'Field' : 'Track'; ?></span>
            </div>
            <div class="xftc-lb-event-header__right">
                <a href="#event-<?php echo esc_attr( sanitize_title($event) ); ?>" class="xftc-lb-event-link">All <?php echo esc_html($event); ?> results ↗</a>
            </div>
        </div>

        <!-- Division sub-tabs if multiple divisions -->
        <?php if ( count($sorted_divs) > 1 ) : ?>
        <div class="xftc-lb-div-nav" data-event="<?php echo esc_attr(sanitize_title($event)); ?>">
            <?php $first_div = true; foreach ($sorted_divs as $div => $rows) : ?>
                <button class="xftc-div-tab <?php echo $first_div ? 'xftc-div-tab--active' : ''; ?>"
                    data-div="div-<?php echo esc_attr(sanitize_title($event.'-'.$div)); ?>">
                    <?php echo esc_html($div); ?>
                    <span class="xftc-div-tab-count"><?php echo count($rows); ?></span>
                </button>
            <?php $first_div = false; endforeach; ?>
        </div>
        <?php endif; ?>

        <!-- Division tables -->
        <?php $first_div = true; foreach ($sorted_divs as $div => $rows) : ?>
        <div class="xftc-lb-div-table <?php echo ($first_div || count($sorted_divs) === 1) ? 'xftc-lb-div-table--active' : ''; ?>"
             id="div-<?php echo esc_attr(sanitize_title($event.'-'.$div)); ?>">

            <?php if ( count($sorted_divs) === 1 ) : ?>
                <div class="xftc-lb-single-div-label"><?php echo esc_html($div); ?> Division</div>
            <?php endif; ?>

            <div class="xftc-table-wrap">
            <table class="xftc-table xftc-lb-table">
                <thead>
                    <tr>
                        <th class="xftc-lb-rank">Rank</th>
                        <th class="xftc-lb-result"><?php echo $is_field ? 'Mark' : 'Time'; ?></th>
                        <th class="xftc-lb-athlete">Athlete</th>
                        <th class="xftc-lb-age">Age/Div</th>
                        <th class="xftc-lb-meet">Meet</th>
                        <th class="xftc-lb-date">Date</th>
                        <th class="xftc-lb-badges"></th>
                    </tr>
                </thead>
                <tbody>
                <?php foreach ( $rows as $entry ) :
                    $row   = $entry['row'];
                    $rank  = $entry['rank'];
                    $age   = XFTC_Results::calc_age( $row->dob );
                    $row_class = $rank === 1 ? 'xftc-rank-gold' : ($rank === 2 ? 'xftc-rank-silver' : ($rank === 3 ? 'xftc-rank-bronze' : ''));
                    $rank_icon = $rank === 1 ? '🥇' : ($rank === 2 ? '🥈' : ($rank === 3 ? '🥉' : "#{$rank}"));
                    $profile_url = add_query_arg( 'athlete_id', $row->athlete_id, home_url('/athlete-profile/') );
                ?>
                    <tr class="xftc-lb-row <?php echo $row_class; ?>">
                        <td class="xftc-lb-rank">
                            <span class="xftc-rank-badge"><?php echo $rank_icon; ?></span>
                        </td>
                        <td class="xftc-lb-result">
                            <strong class="xftc-result-val"><?php echo esc_html($row->result_value); ?></strong>
                        </td>
                        <td class="xftc-lb-athlete">
                            <a href="<?php echo esc_url($profile_url); ?>" class="xftc-athlete-link">
                                <span class="xftc-athlete-avatar-sm">
                                    <?php echo strtoupper( substr($row->first_name,0,1) . substr($row->last_name,0,1) ); ?>
                                </span>
                                <span><?php echo esc_html( $row->first_name . ' ' . $row->last_name ); ?></span>
                            </a>
                        </td>
                        <td class="xftc-lb-age">
                            <?php echo $age ? esc_html("Age {$age}") : '—'; ?>
                            <span class="xftc-div-pill"><?php echo esc_html($div); ?></span>
                        </td>
                        <td class="xftc-lb-meet">
                            <span class="xftc-meet-name"><?php echo esc_html( $row->meet_name ?? '—' ); ?></span>
                        </td>
                        <td class="xftc-lb-date">
                            <?php echo $row->meet_date ? esc_html( date('M j, Y', strtotime($row->meet_date)) ) : '—'; ?>
                        </td>
                        <td class="xftc-lb-badges">
                            <?php if ($row->is_personal_best) echo '<span class="xftc-badge xftc-badge--pb" title="Personal Best">⚡ PB</span> '; ?>
                            <?php if ($row->is_club_record)   echo '<span class="xftc-badge xftc-badge--cr" title="Club Record">🏆 CR</span>'; ?>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
            </div>
        </div><!-- /.xftc-lb-div-table -->
        <?php $first_div = false; endforeach; ?>

    </div><!-- /.xftc-lb-event-section -->
    <?php endforeach; ?>

</div><!-- /.xftc-leaderboard -->

<script>
(function(){
    // Division tab switching inside event sections
    document.querySelectorAll('.xftc-lb-div-nav').forEach(function(nav) {
        nav.querySelectorAll('.xftc-div-tab').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var targetId = btn.dataset.div;
                var section  = btn.closest('.xftc-lb-event-section');
                // Deactivate all
                nav.querySelectorAll('.xftc-div-tab').forEach(function(b){ b.classList.remove('xftc-div-tab--active'); });
                section.querySelectorAll('.xftc-lb-div-table').forEach(function(t){ t.classList.remove('xftc-lb-div-table--active'); });
                // Activate selected
                btn.classList.add('xftc-div-tab--active');
                var target = document.getElementById(targetId);
                if (target) target.classList.add('xftc-lb-div-table--active');
            });
        });
    });
})();
</script>
