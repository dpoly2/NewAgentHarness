<?php
/**
 * Public view — Results table (used by [TRACKSUITE_results] and [TRACKSUITE_my_results])
 * Variables: $results, $show_pb, $show_cr, $show_chart, $chart_data, $atts
 * @package TRACKSUITE_Membership
 */
defined( 'ABSPATH' ) || exit;

$show_athlete = ! isset( $meet_id ) || ! $meet_id; // show athlete col on multi-meet views
?>

<?php if ( ! empty( $show_chart ) && ! empty( $chart_data ) && ! empty( $chart_data['labels'] ) ) : ?>
<div class="ts-chart-wrap" style="margin-bottom:2rem;">
    <p style="font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;color:#6c757d;margin-bottom:.5rem;">
        📈 Performance Progression — <?php echo esc_html( $chart_data['event'] ?? '' ); ?>
    </p>
    <canvas id="ts-results-chart"
            data-chart-data="<?php echo esc_attr( wp_json_encode( $chart_data ) ); ?>"
            style="max-height:260px;"></canvas>
</div>
<?php endif; ?>

<div class="ts-table-wrap">
    <table class="ts-table ts-results-table">
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
            $pb_html = ( $show_pb && ! empty( $r['is_personal_best'] ) ) ? '<span class="ts-badge ts-badge--pb">PB</span>' : '';
            $cr_html = ( $show_cr && ! empty( $r['is_club_record'] ) )   ? '<span class="ts-badge ts-badge--cr">CR</span>' : '';
            $place   = ! empty( $r['placement'] ) ? '#' . (int) $r['placement'] : '—';
            $place_cls = '';
            if ( ! empty( $r['placement'] ) ) {
                if ( (int) $r['placement'] === 1 ) $place_cls = 'ts-place-1';
                if ( (int) $r['placement'] === 2 ) $place_cls = 'ts-place-2';
                if ( (int) $r['placement'] === 3 ) $place_cls = 'ts-place-3';
            }
        ?>
            <tr class="<?php echo esc_attr( $place_cls ); ?>">
                <?php if ( $show_athlete ) : ?>
                    <td><?php echo esc_html( $r['athlete_name'] ?? ( ( $r['first_name'] ?? '' ) . ' ' . ( $r['last_name'] ?? '' ) ) ); ?></td>
                <?php endif; ?>
                <td><?php echo esc_html( $r['event_category'] ?? '—' ); ?></td>
                <td class="ts-result-val">
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

