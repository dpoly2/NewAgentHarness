<?php
/**
 * Class TRACKSUITE_Results
 *
 * Handles athlete result entry, personal best detection,
 * club record tracking, and performance stats.
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

class TRACKSUITE_Results {

    private string $results_table;
    private string $meets_table;
    private string $athletes_table;

    public function __construct() {
        global $wpdb;
        $this->results_table  = $wpdb->prefix . 'TRACKSUITE_results';
        $this->meets_table    = $wpdb->prefix . 'TRACKSUITE_meets';
        $this->athletes_table = $wpdb->prefix . 'TRACKSUITE_athletes';
    }

    /** ─── RESULT ENTRY ──────────────────────────────────────── */

    public function add_result( array $data ): int|false {
        global $wpdb;

        $is_pb = $this->is_personal_best(
            (int) $data['athlete_id'],
            $data['event_category'],
            $data['result_value'],
            $data['result_unit']
        );
        $is_cr = $this->is_club_record(
            $data['event_category'],
            $data['result_value'],
            $data['result_unit']
        );

        $inserted = $wpdb->insert( $this->results_table, [
            'meet_id'         => (int) $data['meet_id'],
            'athlete_id'      => (int) $data['athlete_id'],
            'event_category'  => sanitize_text_field( $data['event_category'] ),
            'placement'       => isset( $data['placement'] ) ? (int) $data['placement'] : null,
            'result_value'    => sanitize_text_field( $data['result_value'] ),
            'result_unit'     => sanitize_text_field( $data['result_unit'] ?? 'time' ),
            'is_personal_best'=> $is_pb ? 1 : 0,
            'is_club_record'  => $is_cr ? 1 : 0,
            'recorded_by'     => get_current_user_id(),
            'recorded_at'     => current_time( 'mysql' ),
        ] );

        if ( $inserted ) {
            $result_id = $wpdb->insert_id;
            // Clear old PB flag if this is the new PB
            if ( $is_pb ) {
                $wpdb->query( $wpdb->prepare(
                    "UPDATE {$this->results_table} SET is_personal_best = 0
                     WHERE athlete_id = %d AND event_category = %s AND id != %d",
                    $data['athlete_id'], $data['event_category'], $result_id
                ) );
            }
            return $result_id;
        }
        return false;
    }

    public function update_result( int $id, array $data ): bool {
        global $wpdb;
        $update = [];
        if ( isset( $data['placement'] ) )      $update['placement']       = (int) $data['placement'];
        if ( isset( $data['result_value'] ) )   $update['result_value']    = sanitize_text_field( $data['result_value'] );
        if ( isset( $data['is_personal_best'] ) ) $update['is_personal_best'] = (int) $data['is_personal_best'];
        if ( isset( $data['is_club_record'] ) )   $update['is_club_record']   = (int) $data['is_club_record'];
        return (bool) $wpdb->update( $this->results_table, $update, [ 'id' => $id ] );
    }

    public function delete_result( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->delete( $this->results_table, [ 'id' => $id ] );
    }

    /** ─── QUERIES ───────────────────────────────────────────── */

    public function get_meet_results( int $meet_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, a.first_name, a.last_name, a.team_level
             FROM {$this->results_table} r
             JOIN {$this->athletes_table} a ON r.athlete_id = a.id
             WHERE r.meet_id = %d
             ORDER BY r.event_category, r.placement",
            $meet_id
        ), ARRAY_A ) ?: [];
    }

    public function get_athlete_results( int $athlete_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, m.name AS meet_name, m.meet_date
             FROM {$this->results_table} r
             JOIN {$this->meets_table} m ON r.meet_id = m.id
             WHERE r.athlete_id = %d
             ORDER BY m.meet_date DESC",
            $athlete_id
        ), ARRAY_A ) ?: [];
    }

    public function get_athlete_results_by_event( int $athlete_id, string $event ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, m.meet_date
             FROM {$this->results_table} r
             JOIN {$this->meets_table} m ON r.meet_id = m.id
             WHERE r.athlete_id = %d AND r.event_category = %s
             ORDER BY m.meet_date ASC",
            $athlete_id, $event
        ), ARRAY_A ) ?: [];
    }

    public function get_personal_bests( int $athlete_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, m.meet_name, m.meet_date
             FROM {$this->results_table} r
             JOIN {$this->meets_table} m ON r.meet_id = m.id
             WHERE r.athlete_id = %d AND r.is_personal_best = 1
             ORDER BY r.event_category",
            $athlete_id
        ), ARRAY_A ) ?: [];
    }

    public function get_club_records(): array {
        global $wpdb;
        return $wpdb->get_results(
            "SELECT r.*, a.first_name, a.last_name, m.name AS meet_name, m.meet_date
             FROM {$this->results_table} r
             JOIN {$this->athletes_table} a ON r.athlete_id = a.id
             JOIN {$this->meets_table} m ON r.meet_id = m.id
             WHERE r.is_club_record = 1
             ORDER BY r.event_category",
            ARRAY_A
        ) ?: [];
    }

    /** ─── PERSONAL BEST & CLUB RECORD DETECTION ─────────────── */

    /**
     * Determine if a result is a personal best for this athlete+event.
     * For time events: lower is better. For distance/points: higher is better.
     */
    public function is_personal_best( int $athlete_id, string $event, string $value, string $unit ): bool {
        global $wpdb;
        $prev = $wpdb->get_var( $wpdb->prepare(
            "SELECT result_value FROM {$this->results_table}
             WHERE athlete_id = %d AND event_category = %s AND is_personal_best = 1
             LIMIT 1",
            $athlete_id, $event
        ) );
        if ( ! $prev ) return true;
        return $unit === 'time'
            ? $this->compare_time( $value, $prev ) < 0
            : $this->compare_distance( $value, $prev ) > 0;
    }

    /**
     * Determine if a result is a club record for this event.
     */
    public function is_club_record( string $event, string $value, string $unit ): bool {
        global $wpdb;
        $current_record = $wpdb->get_var( $wpdb->prepare(
            "SELECT result_value FROM {$this->results_table}
             WHERE event_category = %s AND is_club_record = 1
             LIMIT 1",
            $event
        ) );
        if ( ! $current_record ) return true;
        return $unit === 'time'
            ? $this->compare_time( $value, $current_record ) < 0
            : $this->compare_distance( $value, $current_record ) > 0;
    }

    /**
     * Compare two time strings (MM:SS.ms or SS.ms).
     * Returns negative if $a < $b (faster), 0 if equal, positive if slower.
     */
    private function compare_time( string $a, string $b ): int {
        return (int) ( ( $this->time_to_seconds( $a ) - $this->time_to_seconds( $b ) ) * 1000 );
    }

    private function time_to_seconds( string $time ): float {
        $parts = explode( ':', $time );
        if ( count( $parts ) === 2 ) {
            return ( (float) $parts[0] * 60 ) + (float) $parts[1];
        }
        return (float) $time;
    }

    /**
     * Compare two distance strings (e.g. "15'6\"" or "4.75m").
     * Returns positive if $a > $b (farther), negative if shorter.
     */
    private function compare_distance( string $a, string $b ): float {
        return $this->distance_to_meters( $a ) - $this->distance_to_meters( $b );
    }

    private function distance_to_meters( string $dist ): float {
        // Handle feet/inches format: 15'6"
        if ( preg_match( "/(\d+)'(\d+)/", $dist, $m ) ) {
            return ( (float) $m[1] * 0.3048 ) + ( (float) $m[2] * 0.0254 );
        }
        // Handle meters format: 4.75m or just 4.75
        return (float) preg_replace( '/[^0-9.]/', '', $dist );
    }

    /** ─── STATS FOR CHART.JS ────────────────────────────────── */

    /**
     * Get performance progression data for a single athlete + event.
     * Returns array suitable for Chart.js line chart.
     */
    public function get_progression_chart_data( int $athlete_id, string $event ): array {
        $results = $this->get_athlete_results_by_event( $athlete_id, $event );
        $labels  = [];
        $values  = [];
        $is_pb   = [];

        foreach ( $results as $r ) {
            $labels[] = date( 'M j', strtotime( $r['meet_date'] ) );
            $values[] = $r['result_value'];
            $is_pb[]  = (bool) $r['is_personal_best'];
        }

        return [
            'labels'   => $labels,
            'values'   => $values,
            'is_pb'    => $is_pb,
            'event'    => $event,
        ];
    }

    /**
     * Get all distinct events an athlete has competed in.
     */
    public function get_athlete_events( int $athlete_id ): array {
        global $wpdb;
        return $wpdb->get_col( $wpdb->prepare(
            "SELECT DISTINCT event_category FROM {$this->results_table} WHERE athlete_id = %d ORDER BY event_category",
            $athlete_id
        ) ) ?: [];
    }
}

