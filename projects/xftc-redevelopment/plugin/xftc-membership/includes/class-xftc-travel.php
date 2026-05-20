<?php
/**
 * Class XFTC_Travel
 *
 * Manages bus/hotel travel bookings per meet,
 * seat/room assignments, fees, and CSV manifest export.
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

class XFTC_Travel {

    private string $travel_table;
    private string $meets_table;
    private string $athletes_table;

    public function __construct() {
        global $wpdb;
        $this->travel_table   = $wpdb->prefix . 'xftc_travel';
        $this->meets_table    = $wpdb->prefix . 'xftc_meets';
        $this->athletes_table = $wpdb->prefix . 'xftc_athletes';
    }

    /** ─── BOOKING CRUD ──────────────────────────────────────── */

    public function create_booking( array $data ): int|false {
        global $wpdb;

        // Prevent duplicate bookings
        $exists = $wpdb->get_var( $wpdb->prepare(
            "SELECT id FROM {$this->travel_table} WHERE meet_id = %d AND athlete_id = %d",
            $data['meet_id'], $data['athlete_id']
        ) );
        if ( $exists ) return (int) $exists;

        $fee = $this->calculate_fee(
            $data['travel_type'],
            (int) $data['meet_id']
        );

        $inserted = $wpdb->insert( $this->travel_table, [
            'meet_id'        => (int) $data['meet_id'],
            'athlete_id'     => (int) $data['athlete_id'],
            'travel_type'    => sanitize_text_field( $data['travel_type'] ?? 'bus' ),
            'bus_seat'       => sanitize_text_field( $data['bus_seat'] ?? '' ),
            'hotel_room'     => sanitize_text_field( $data['hotel_room'] ?? '' ),
            'travel_fee'     => $fee,
            'payment_status' => 'unpaid',
            'notes'          => sanitize_textarea_field( $data['notes'] ?? '' ),
            'registered_at'  => current_time( 'mysql' ),
        ] );
        return $inserted ? $wpdb->insert_id : false;
    }

    public function get_booking( int $id ): ?array {
        global $wpdb;
        return $wpdb->get_row( $wpdb->prepare(
            "SELECT * FROM {$this->travel_table} WHERE id = %d", $id
        ), ARRAY_A ) ?: null;
    }

    public function update_booking( int $id, array $data ): bool {
        global $wpdb;
        $update = [];
        if ( isset( $data['travel_type'] ) )    $update['travel_type']    = sanitize_text_field( $data['travel_type'] );
        if ( isset( $data['bus_seat'] ) )        $update['bus_seat']       = sanitize_text_field( $data['bus_seat'] );
        if ( isset( $data['hotel_room'] ) )      $update['hotel_room']     = sanitize_text_field( $data['hotel_room'] );
        if ( isset( $data['travel_fee'] ) )      $update['travel_fee']     = (float) $data['travel_fee'];
        if ( isset( $data['payment_status'] ) )  $update['payment_status'] = sanitize_text_field( $data['payment_status'] );
        if ( isset( $data['notes'] ) )           $update['notes']          = sanitize_textarea_field( $data['notes'] );
        return (bool) $wpdb->update( $this->travel_table, $update, [ 'id' => $id ] );
    }

    public function delete_booking( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->delete( $this->travel_table, [ 'id' => $id ] );
    }

    public function mark_paid( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->travel_table,
            [ 'payment_status' => 'paid' ],
            [ 'id' => $id ]
        );
    }

    /** ─── QUERIES ───────────────────────────────────────────── */

    public function get_meet_travel( int $meet_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, a.first_name, a.last_name, a.team_level
             FROM {$this->travel_table} t
             JOIN {$this->athletes_table} a ON t.athlete_id = a.id
             WHERE t.meet_id = %d
             ORDER BY t.travel_type, a.last_name",
            $meet_id
        ), ARRAY_A ) ?: [];
    }

    public function get_athlete_travel( int $athlete_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, m.name AS meet_name, m.meet_date, m.location
             FROM {$this->travel_table} t
             JOIN {$this->meets_table} m ON t.meet_id = m.id
             WHERE t.athlete_id = %d
             ORDER BY m.meet_date DESC",
            $athlete_id
        ), ARRAY_A ) ?: [];
    }

    public function get_unpaid_by_meet( int $meet_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT t.*, a.first_name, a.last_name
             FROM {$this->travel_table} t
             JOIN {$this->athletes_table} a ON t.athlete_id = a.id
             WHERE t.meet_id = %d AND t.payment_status = 'unpaid'",
            $meet_id
        ), ARRAY_A ) ?: [];
    }

    /** ─── SEAT & ROOM ASSIGNMENT ────────────────────────────── */

    public function assign_seat( int $booking_id, string $seat ): bool {
        global $wpdb;
        // Check seat isn't already taken for this meet
        $booking   = $this->get_booking( $booking_id );
        $taken = $wpdb->get_var( $wpdb->prepare(
            "SELECT id FROM {$this->travel_table} WHERE meet_id = %d AND bus_seat = %s AND id != %d",
            $booking['meet_id'], $seat, $booking_id
        ) );
        if ( $taken ) return false;
        return (bool) $wpdb->update( $this->travel_table, [ 'bus_seat' => $seat ], [ 'id' => $booking_id ] );
    }

    public function assign_room( int $booking_id, string $room ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->travel_table, [ 'hotel_room' => $room ], [ 'id' => $booking_id ] );
    }

    public function get_taken_seats( int $meet_id ): array {
        global $wpdb;
        return $wpdb->get_col( $wpdb->prepare(
            "SELECT bus_seat FROM {$this->travel_table} WHERE meet_id = %d AND bus_seat != '' AND bus_seat IS NOT NULL",
            $meet_id
        ) ) ?: [];
    }

    /** ─── FEE CALCULATION ───────────────────────────────────── */

    /**
     * Calculate travel fee based on type.
     * Fees are configurable via WP options; defaults shown below.
     */
    public function calculate_fee( string $type, int $meet_id = 0 ): float {
        $bus_fee   = (float) get_option( 'xftc_travel_fee_bus', 25.00 );
        $hotel_fee = (float) get_option( 'xftc_travel_fee_hotel', 75.00 );
        return match ( $type ) {
            'bus'   => $bus_fee,
            'hotel' => $hotel_fee,
            'both'  => $bus_fee + $hotel_fee,
            default => 0.00,
        };
    }

    /** ─── TOTALS ────────────────────────────────────────────── */

    public function get_meet_travel_totals( int $meet_id ): array {
        global $wpdb;
        $rows = $this->get_meet_travel( $meet_id );
        $total_due  = array_sum( array_column( $rows, 'travel_fee' ) );
        $total_paid = array_sum( array_map(
            fn( $r ) => $r['payment_status'] === 'paid' ? $r['travel_fee'] : 0,
            $rows
        ) );
        return [
            'total_bookings' => count( $rows ),
            'total_due'      => $total_due,
            'total_paid'     => $total_paid,
            'total_unpaid'   => $total_due - $total_paid,
        ];
    }

    /** ─── CSV MANIFEST EXPORT ───────────────────────────────── */

    public function export_manifest_csv( int $meet_id ): void {
        global $wpdb;
        $meet    = $wpdb->get_row( $wpdb->prepare(
            "SELECT name FROM {$this->meets_table} WHERE id = %d", $meet_id
        ) );
        $bookings = $this->get_meet_travel( $meet_id );
        $filename = sanitize_file_name( ( $meet->name ?? 'meet' ) . '-travel-manifest.csv' );

        header( 'Content-Type: text/csv' );
        header( "Content-Disposition: attachment; filename=\"{$filename}\"" );

        $out = fopen( 'php://output', 'w' );
        fputcsv( $out, [ 'Last Name', 'First Name', 'Team Level', 'Travel Type', 'Bus Seat', 'Hotel Room', 'Fee', 'Payment Status' ] );
        foreach ( $bookings as $b ) {
            fputcsv( $out, [
                $b['last_name'],
                $b['first_name'],
                $b['team_level'],
                strtoupper( $b['travel_type'] ),
                $b['bus_seat'] ?: '—',
                $b['hotel_room'] ?: '—',
                '$' . number_format( $b['travel_fee'], 2 ),
                ucfirst( $b['payment_status'] ),
            ] );
        }
        fclose( $out );
        exit;
    }
}
