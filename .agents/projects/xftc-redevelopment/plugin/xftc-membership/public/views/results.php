<?php
/**
 * Public view — Results table (used by [xftc_results] and [xftc_my_results])
 * Variables: $results, $show_pb, $show_cr, $show_chart, $chart_data, $atts
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

$show_athlete = ! isset( $meet_id ) || ! $meet_id; // show athlete col on multi-meet views
?>

<?php if ( ! empty( $show_chart ) && ! empty( $chart_data ) && ! empty( $chart_data['labels'] ) ) : ?>
<div class="xftc-chart-wrap" style="margin-bottom:2rem;">
    <p style="font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;color:#6c757d;margin-bottom:.5rem;">
        📈 Performance Progression — <?php echo esc_html( $chart_data['event'] ?? '' ); ?>
    </p>
    <canvas id="xftc-results-chart"
            data-chart-data="<?php echo esc_attr( wp_json_encode( $chart_data ) ); ?>"
            style="max-height:260px;"></canvas>
</div>
<?php endif; ?>

<div class="xftc-table-wrap">
    <table class="xftc-table xftc-results-table">
        <thead>
            <tr>
                <?php if ( $show_athlete ) : ?><th>Athlete</th><?php endif; ?>
                <th>Event</th>
                <th>Result</th>
                <th>Place</th>
                <th>Meet</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
        <?php foreach ( $results as $r ) :
            $pb_html = ( $show_pb && ! empty( $r['is_personal_best'] ) ) ? '<span class="xftc-badge xftc-badge--pb">PB</span>' : '';
            $cr_html = ( $show_cr && ! empty( $r['is_club_record'] ) )   ? '<span class="xftc-badge xftc-badge--cr">CR</span>' : '';
            $place   = ! empty( $r['placement'] ) ? '#' . (int) $r['placement'] : '—';
            $place_cls = '';
            if ( ! empty( $r['placement'] ) ) {
                if ( (int) $r['placement'] === 1 ) $place_cls = 'xftc-place-1';
                if ( (int) $r['placement'] === 2 ) $place_cls = 'xftc-place-2';
                if ( (int) $r['placement'] === 3 ) $place_cls = 'xftc-place-3';
            }
        ?>
            <tr class="<?php echo esc_attr( $place_cls ); ?>">
                <?php if ( $show_athlete ) : ?>
                    <td><?php echo esc_html( $r['athlete_name'] ?? ( ( $r['first_name'] ?? '' ) . ' ' . ( $r['last_name'] ?? '' ) ) ); ?></td>
                <?php endif; ?>
                <td><?php echo esc_html( $r['event_category'] ?? '—' ); ?></td>
                <td class="xftc-result-val">
                    <?php echo esc_html( $r['result_value'] ?? '—' ); ?>
                    <?php echo wp_kses_post( $pb_html . $cr_html ); ?>
                </td>
                <td><?php echo esc_html( $place ); ?></td>
                <td><?php echo esc_html( $r['meet_name'] ?? '—' ); ?></td>
                <td><?php echo ! empty( $r['meet_date'] ) ? esc_html( date( 'M j, Y', strtotime( $r['meet_date'] ) ) ) : ( ! empty( $r['recorded_at'] ) ? esc_html( date( 'M j, Y', strtotime( $r['recorded_at'] ) ) ) : '—' ); ?></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
</div>
