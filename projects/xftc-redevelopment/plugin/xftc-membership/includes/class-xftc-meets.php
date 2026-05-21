<?php
/**
 * Class TRACKSUITE_Meets
 *
 * Handles meet creation, management, athlete registration,
 * waiver tracking, and status workflows.
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

class TRACKSUITE_Meets {

    private string $meets_table;
    private string $entries_table;

    public function __construct() {
        global $wpdb;
        $this->meets_table   = $wpdb->prefix . 'TRACKSUITE_meets';
        $this->entries_table = $wpdb->prefix . 'TRACKSUITE_meet_entries';
    }

    /** ─── MEET CRUD ─────────────────────────────────────────── */

    public function create_meet( array $data ): int|false {
        global $wpdb;
        $inserted = $wpdb->insert( $this->meets_table, [
            'name'       => sanitize_text_field( $data['name'] ),
            'meet_date'  => sanitize_text_field( $data['meet_date'] ),
            'meet_time'  => sanitize_text_field( $data['meet_time'] ?? '' ),
            'location'   => sanitize_text_field( $data['location'] ?? '' ),
            'type'       => sanitize_text_field( $data['type'] ?? 'competitive' ),
            'categories' => wp_json_encode( $data['categories'] ?? [] ),
            'status'     => 'upcoming',
            'created_by' => get_current_user_id(),
            'created_at' => current_time( 'mysql' ),
        ] );
        return $inserted ? $wpdb->insert_id : false;
    }

    public function get_meet( int $id ): ?array {
        global $wpdb;
        $row = $wpdb->get_row( $wpdb->prepare(
            "SELECT * FROM {$this->meets_table} WHERE id = %d", $id
        ), ARRAY_A );
        if ( $row ) {
            $row['categories'] = json_decode( $row['categories'] ?? '[]', true );
        }
        return $row ?: null;
    }

    public function get_all_meets( string $status = '' ): array {
        global $wpdb;
        $sql = "SELECT * FROM {$this->meets_table}";
        if ( $status ) {
            $sql .= $wpdb->prepare( " WHERE status = %s", $status );
        }
        $sql .= " ORDER BY meet_date ASC";
        $rows = $wpdb->get_results( $sql, ARRAY_A );
        foreach ( $rows as &$row ) {
            $row['categories'] = json_decode( $row['categories'] ?? '[]', true );
        }
        return $rows ?: [];
    }

    public function get_upcoming_meets(): array {
        global $wpdb;
        $rows = $wpdb->get_results( $wpdb->prepare(
            "SELECT * FROM {$this->meets_table} WHERE meet_date >= %s AND status = 'upcoming' ORDER BY meet_date ASC",
            current_time( 'Y-m-d' )
        ), ARRAY_A );
        foreach ( $rows as &$row ) {
            $row['categories'] = json_decode( $row['categories'] ?? '[]', true );
        }
        return $rows ?: [];
    }

    public function update_meet( int $id, array $data ): bool {
        global $wpdb;
        $update = [];
        if ( isset( $data['name'] ) )       $update['name']       = sanitize_text_field( $data['name'] );
        if ( isset( $data['meet_date'] ) )   $update['meet_date']  = sanitize_text_field( $data['meet_date'] );
        if ( isset( $data['meet_time'] ) )   $update['meet_time']  = sanitize_text_field( $data['meet_time'] );
        if ( isset( $data['location'] ) )    $update['location']   = sanitize_text_field( $data['location'] );
        if ( isset( $data['type'] ) )        $update['type']       = sanitize_text_field( $data['type'] );
        if ( isset( $data['categories'] ) )  $update['categories'] = wp_json_encode( $data['categories'] );
        if ( isset( $data['status'] ) )      $update['status']     = sanitize_text_field( $data['status'] );
        return (bool) $wpdb->update( $this->meets_table, $update, [ 'id' => $id ] );
    }

    public function update_status( int $id, string $status ): bool {
        global $wpdb;
        $allowed = [ 'upcoming', 'active', 'completed', 'cancelled' ];
        if ( ! in_array( $status, $allowed, true ) ) return false;
        return (bool) $wpdb->update( $this->meets_table, [ 'status' => $status ], [ 'id' => $id ] );
    }

    public function delete_meet( int $id ): bool {
        global $wpdb;
        $wpdb->delete( $this->entries_table, [ 'meet_id' => $id ] );
        return (bool) $wpdb->delete( $this->meets_table, [ 'id' => $id ] );
    }

    /** ─── MEET REGISTRATION ─────────────────────────────────── */

    public function register_athlete( int $meet_id, int $athlete_id, array $data = [] ): int|false {
        global $wpdb;
        // Check for duplicate
        $exists = $wpdb->get_var( $wpdb->prepare(
            "SELECT id FROM {$this->entries_table} WHERE meet_id = %d AND athlete_id = %d AND event_category = %s",
            $meet_id, $athlete_id, $data['event_category'] ?? ''
        ) );
        if ( $exists ) return (int) $exists;

        $inserted = $wpdb->insert( $this->entries_table, [
            'meet_id'        => $meet_id,
            'athlete_id'     => $athlete_id,
            'event_category' => sanitize_text_field( $data['event_category'] ?? '' ),
            'division'       => sanitize_text_field( $data['division'] ?? '' ),
            'waiver_uploaded'=> 0,
            'registered_at'  => current_time( 'mysql' ),
        ] );
        return $inserted ? $wpdb->insert_id : false;
    }

    public function update_waiver( int $entry_id, bool $uploaded ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->entries_table,
            [ 'waiver_uploaded' => (int) $uploaded ],
            [ 'id' => $entry_id ]
        );
    }

    public function get_meet_roster( int $meet_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT e.*, a.first_name, a.last_name, a.team_level, a.gender
             FROM {$this->entries_table} e
             JOIN {$wpdb->prefix}TRACKSUITE_athletes a ON e.athlete_id = a.id
             WHERE e.meet_id = %d
             ORDER BY e.event_category, a.last_name",
            $meet_id
        ), ARRAY_A ) ?: [];
    }

    public function get_athlete_meets( int $athlete_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT m.*, e.event_category, e.division, e.waiver_uploaded
             FROM {$this->entries_table} e
             JOIN {$this->meets_table} m ON e.meet_id = m.id
             WHERE e.athlete_id = %d
             ORDER BY m.meet_date DESC",
            $athlete_id
        ), ARRAY_A ) ?: [];
    }

    public function remove_registration( int $meet_id, int $athlete_id ): bool {
        global $wpdb;
        return (bool) $wpdb->delete( $this->entries_table, [
            'meet_id'    => $meet_id,
            'athlete_id' => $athlete_id,
        ] );
    }

    /** ─── EXPORT ────────────────────────────────────────────── */

    public function export_roster_csv( int $meet_id ): void {
        $meet   = $this->get_meet( $meet_id );
        $roster = $this->get_meet_roster( $meet_id );
        $name   = sanitize_file_name( $meet['name'] ?? 'meet' );

        header( 'Content-Type: text/csv' );
        header( "Content-Disposition: attachment; filename=\"{$name}-roster.csv\"" );

        $out = fopen( 'php://output', 'w' );
        fputcsv( $out, [ 'Last Name', 'First Name', 'Event', 'Division', 'Team Level', 'Waiver' ] );
        foreach ( $roster as $entry ) {
            fputcsv( $out, [
                $entry['last_name'],
                $entry['first_name'],
                $entry['event_category'],
                $entry['division'],
                $entry['team_level'],
                $entry['waiver_uploaded'] ? 'Yes' : 'No',
            ] );
        }
        fclose( $out );
        exit;
    }

    /** ─── COUNTS ────────────────────────────────────────────── */

    public function get_upcoming_count(): int {
        global $wpdb;
        return (int) $wpdb->get_var( $wpdb->prepare(
            "SELECT COUNT(*) FROM {$this->meets_table} WHERE meet_date >= %s AND status = 'upcoming'",
            current_time( 'Y-m-d' )
        ) );
    }

    public function get_recent_registrations( int $limit = 10 ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT e.*, a.first_name, a.last_name, m.name AS meet_name
             FROM {$this->entries_table} e
             JOIN {$wpdb->prefix}TRACKSUITE_athletes a ON e.athlete_id = a.id
             JOIN {$this->meets_table} m ON e.meet_id = m.id
             ORDER BY e.registered_at DESC LIMIT %d",
            $limit
        ), ARRAY_A ) ?: [];
    }
}

