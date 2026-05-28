<?php
/**
 * Admin View — Results Entry
 * WP Admin → Xtreme Force → Results
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

$results_mgr = new TRACKSUITE_Results();
$meets_mgr   = new TRACKSUITE_Meets();

if ( isset( $_POST['TRACKSUITE_results_nonce'] ) && wp_verify_nonce( $_POST['TRACKSUITE_results_nonce'], 'TRACKSUITE_save_result' ) ) {
    $id = $results_mgr->add_result( $_POST );
    echo $id
        ? '<div class="notice notice-success"><p>Result saved.' . ( $_POST['is_personal_best'] ?? false ? ' 🏅 Personal Best!' : '' ) . '</p></div>'
        : '<div class="notice notice-error"><p>Failed to save result.</p></div>';
}

$selected_meet = isset( $_GET['meet_id'] ) ? (int) $_GET['meet_id'] : 0;
$meets         = $meets_mgr->get_all_meets( 'completed' );
$meet_results  = $selected_meet ? $results_mgr->get_meet_results( $selected_meet ) : [];
$club_records  = $results_mgr->get_club_records();
?>

<div class="wrap ts-admin-results">
    <h1>📊 Results</h1>

    <!-- Meet Selector -->
    <form method="get" style="margin-bottom:16px;">
        <input type="hidden" name="page" value="ts-results">
        <label><strong>View Results For:</strong>
            <select name="meet_id" onchange="this.form.submit()">
                <option value="">— Select Meet —</option>
                <?php foreach ( $meets as $m ) : ?>
                    <option value="<?php echo $m['id']; ?>" <?php selected( $selected_meet, $m['id'] ); ?>>
                        <?php echo esc_html( $m['name'] . ' — ' . date( 'M j, Y', strtotime( $m['meet_date'] ) ) ); ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </label>
    </form>

    <?php if ( $selected_meet ) : ?>
    <!-- Results Table -->
    <h2>Results: <?php echo esc_html( $meets_mgr->get_meet( $selected_meet )['name'] ?? '' ); ?></h2>
    <table class="wp-list-table widefat fixed striped">
        <thead><tr><th>Athlete</th><th>Event</th><th>Placement</th><th>Result</th><th>PB</th><th>Club Record</th></tr></thead>
        <tbody>
        <?php if ( empty( $meet_results ) ) : ?>
            <tr><td colspan="6" style="text-align:center;"><em>No results entered yet.</em></td></tr>
        <?php else : foreach ( $meet_results as $r ) : ?>
            <tr>
                <td><?php echo esc_html( $r['first_name'] . ' ' . $r['last_name'] ); ?></td>
                <td><?php echo esc_html( $r['event_category'] ); ?></td>
                <td><?php echo $r['placement'] ? '#' . $r['placement'] : '—'; ?></td>
                <td><strong><?php echo esc_html( $r['result_value'] ); ?></strong></td>
                <td><?php echo $r['is_personal_best'] ? '🏅 Yes' : '—'; ?></td>
                <td><?php echo $r['is_club_record'] ? '🏆 Yes' : '—'; ?></td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>
    <?php endif; ?>

    <hr>

    <!-- Add Result Form -->
    <h2>Enter Result</h2>
    <form method="post">
        <?php wp_nonce_field( 'TRACKSUITE_save_result', 'TRACKSUITE_results_nonce' ); ?>
        <table class="form-table">
            <tr>
                <th><label>Meet</label></th>
                <td>
                    <select name="meet_id" required>
                        <option value="">— Select Meet —</option>
                        <?php foreach ( $meets as $m ) : ?>
                            <option value="<?php echo $m['id']; ?>" <?php selected( $selected_meet, $m['id'] ); ?>>
                                <?php echo esc_html( $m['name'] ); ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label>Athlete ID</label></th>
                <td><input type="number" name="athlete_id" required class="small-text" placeholder="Athlete DB ID"></td>
            </tr>
            <tr>
                <th><label>Event Category</label></th>
                <td>
                    <select name="event_category" required>
                        <?php foreach ( ['100m','200m','400m','800m','1500m','3000m','100m Hurdles','110m Hurdles','400m Hurdles','Long Jump','High Jump','Triple Jump','Shot Put','Discus','Javelin','4x100 Relay','4x400 Relay'] as $evt ) : ?>
                            <option value="<?php echo $evt; ?>"><?php echo $evt; ?></option>
                        <?php endforeach; ?>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label>Result Value</label></th>
                <td>
                    <input type="text" name="result_value" required placeholder="e.g. 12.45 or 15'6&quot;" class="regular-text">
                    <select name="result_unit">
                        <option value="time">Time (seconds/MM:SS)</option>
                        <option value="distance">Distance (feet/meters)</option>
                        <option value="points">Points</option>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label>Placement</label></th>
                <td><input type="number" name="placement" min="1" class="small-text" placeholder="1st, 2nd, etc."></td>
            </tr>
        </table>
        <?php submit_button( 'Save Result' ); ?>
    </form>

    <hr>

    <!-- Club Records -->
    <h2>🏆 Club Records</h2>
    <table class="wp-list-table widefat fixed striped">
        <thead><tr><th>Event</th><th>Athlete</th><th>Result</th><th>Meet</th><th>Date</th></tr></thead>
        <tbody>
        <?php if ( empty( $club_records ) ) : ?>
            <tr><td colspan="5" style="text-align:center;"><em>No club records on file yet.</em></td></tr>
        <?php else : foreach ( $club_records as $cr ) : ?>
            <tr>
                <td><?php echo esc_html( $cr['event_category'] ); ?></td>
                <td><?php echo esc_html( $cr['first_name'] . ' ' . $cr['last_name'] ); ?></td>
                <td><strong><?php echo esc_html( $cr['result_value'] ); ?></strong></td>
                <td><?php echo esc_html( $cr['meet_name'] ); ?></td>
                <td><?php echo esc_html( date( 'M j, Y', strtotime( $cr['meet_date'] ) ) ); ?></td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>
</div>

