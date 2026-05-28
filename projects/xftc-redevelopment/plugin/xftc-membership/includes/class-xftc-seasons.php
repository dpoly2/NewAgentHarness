<?php
/**
 * Season management — create, read, update, delete seasons.
 *
 * @package TRACKSUITE_Membership
 */

defined( 'ABSPATH' ) || exit;

class TRACKSUITE_Seasons {

    /** @var string */
    private $table;

    public function __construct() {
        global $wpdb;
        $this->table = $wpdb->prefix . 'TRACKSUITE_seasons';
    }

    /**
     * Create a new season.
     *
     * @param array $data
     * @return int|WP_Error Season ID or error.
     */
    public function create( array $data ) {
        global $wpdb;

        if ( empty( $data['name'] ) || empty( $data['type'] ) ) {
            return new WP_Error( 'missing_fields', __( 'Season name and type are required.', 'ts-membership' ) );
        }

        $insert = [
            'name'         => sanitize_text_field( $data['name'] ),
            'type'         => sanitize_text_field( $data['type'] ),
            'start_date'   => ! empty( $data['start_date'] )   ? sanitize_text_field( $data['start_date'] )   : null,
            'end_date'     => ! empty( $data['end_date'] )     ? sanitize_text_field( $data['end_date'] )     : null,
            'reg_open'     => ! empty( $data['reg_open'] )     ? sanitize_text_field( $data['reg_open'] )     : null,
            'reg_close'    => ! empty( $data['reg_close'] )    ? sanitize_text_field( $data['reg_close'] )    : null,
            'fee_standard' => ! empty( $data['fee_standard'] ) ? floatval( $data['fee_standard'] )            : 0.00,
            'fee_premium'  => ! empty( $data['fee_premium'] )  ? floatval( $data['fee_premium'] )             : 0.00,
            'is_active'    => isset( $data['is_active'] )      ? absint( $data['is_active'] )                 : 1,
        ];

        $result = $wpdb->insert( $this->table, $insert );

        return ( false === $result ) ? new WP_Error( 'db_error', $wpdb->last_error ) : (int) $wpdb->insert_id;
    }

    /**
     * Get a single season.
     *
     * @param int $id
     * @return object|null
     */
    public function get( int $id ) {
        global $wpdb;
        return $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$this->table} WHERE id = %d", $id ) );
    }

    /**
     * Get the current active season.
     *
     * @return object|null
     */
    public function get_active() {
        global $wpdb;
        return $wpdb->get_row( "SELECT * FROM {$this->table} WHERE is_active = 1 ORDER BY id DESC LIMIT 1" );
    }

    /**
     * Get all seasons.
     *
     * @return array
     */
    public function get_all(): array {
        global $wpdb;
        return $wpdb->get_results( "SELECT * FROM {$this->table} ORDER BY id DESC" );
    }

    /**
     * Update a season.
     *
     * @param int   $id
     * @param array $data
     * @return bool
     */
    public function update( int $id, array $data ): bool {
        global $wpdb;

        $allowed = [ 'name', 'type', 'start_date', 'end_date', 'reg_open', 'reg_close', 'fee_standard', 'fee_premium', 'is_active' ];
        $update  = [];

        foreach ( $allowed as $field ) {
            if ( isset( $data[ $field ] ) ) {
                $update[ $field ] = in_array( $field, [ 'fee_standard', 'fee_premium' ] )
                    ? floatval( $data[ $field ] )
                    : sanitize_text_field( $data[ $field ] );
            }
        }

        return ! empty( $update ) && (bool) $wpdb->update( $this->table, $update, [ 'id' => $id ] );
    }

    /**
     * Delete a season.
     *
     * @param int $id
     * @return bool
     */
    public function delete( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->delete( $this->table, [ 'id' => $id ], [ '%d' ] );
    }

    /**
     * Set a season as the active season (deactivates all others).
     *
     * @param int $id
     */
    public function set_active( int $id ) {
        global $wpdb;
        $wpdb->query( "UPDATE {$this->table} SET is_active = 0" );
        $wpdb->update( $this->table, [ 'is_active' => 1 ], [ 'id' => $id ] );
    }
}

