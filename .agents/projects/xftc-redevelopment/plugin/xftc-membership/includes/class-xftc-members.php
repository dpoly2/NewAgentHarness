<?php
/**
 * Handles all athlete member CRUD operations.
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Members {

    /** @var string DB table name */
    private $table;

    public function __construct() {
        global $wpdb;
        $this->table = $wpdb->prefix . 'xftc_athletes';
    }

    /**
     * Create a new athlete profile linked to a parent user.
     *
     * @param array $data {
     *     @type int    $parent_id               WP user ID of parent (required)
     *     @type string $first_name              (required)
     *     @type string $last_name               (required)
     *     @type string $dob                     Date of birth (Y-m-d)
     *     @type string $gender                  male|female|other
     *     @type string $team_level
     *     @type string $school
     *     @type string $emergency_contact_name
     *     @type string $emergency_contact_phone
     * }
     * @return int|WP_Error  Athlete ID on success, WP_Error on failure.
     */
    public function create( array $data ) {
        global $wpdb;

        if ( empty( $data['parent_id'] ) || empty( $data['first_name'] ) || empty( $data['last_name'] ) ) {
            return new WP_Error( 'missing_fields', __( 'parent_id, first_name, and last_name are required.', 'xftc-membership' ) );
        }

        $insert = [
            'parent_id'               => absint( $data['parent_id'] ),
            'first_name'              => sanitize_text_field( $data['first_name'] ),
            'last_name'               => sanitize_text_field( $data['last_name'] ),
            'dob'                     => ! empty( $data['dob'] )                     ? sanitize_text_field( $data['dob'] )                     : null,
            'gender'                  => ! empty( $data['gender'] )                  ? sanitize_text_field( $data['gender'] )                  : null,
            'team_level'              => ! empty( $data['team_level'] )              ? sanitize_text_field( $data['team_level'] )              : null,
            'school'                  => ! empty( $data['school'] )                  ? sanitize_text_field( $data['school'] )                  : null,
            'emergency_contact_name'  => ! empty( $data['emergency_contact_name'] )  ? sanitize_text_field( $data['emergency_contact_name'] )  : null,
            'emergency_contact_phone' => ! empty( $data['emergency_contact_phone'] ) ? sanitize_text_field( $data['emergency_contact_phone'] ) : null,
        ];

        $result = $wpdb->insert( $this->table, $insert );

        if ( false === $result ) {
            return new WP_Error( 'db_error', $wpdb->last_error );
        }

        return (int) $wpdb->insert_id;
    }

    /**
     * Get a single athlete by ID.
     *
     * @param int $id Athlete ID.
     * @return object|null
     */
    public function get( int $id ) {
        global $wpdb;
        return $wpdb->get_row(
            $wpdb->prepare( "SELECT * FROM {$this->table} WHERE id = %d", $id )
        );
    }

    /**
     * Get all athletes belonging to a parent user.
     *
     * @param int $parent_id WP user ID.
     * @return array
     */
    public function get_by_parent( int $parent_id ): array {
        global $wpdb;
        return $wpdb->get_results(
            $wpdb->prepare( "SELECT * FROM {$this->table} WHERE parent_id = %d ORDER BY last_name ASC, first_name ASC", $parent_id )
        );
    }

    /**
     * Get all athletes (admin use).
     *
     * @param array $args Optional. search, limit, offset.
     * @return array
     */
    public function get_all( array $args = [] ): array {
        global $wpdb;

        $limit  = isset( $args['limit'] )  ? absint( $args['limit'] )  : 100;
        $offset = isset( $args['offset'] ) ? absint( $args['offset'] ) : 0;
        $search = ! empty( $args['search'] ) ? '%' . $wpdb->esc_like( sanitize_text_field( $args['search'] ) ) . '%' : null;

        if ( $search ) {
            return $wpdb->get_results(
                $wpdb->prepare(
                    "SELECT * FROM {$this->table}
                     WHERE first_name LIKE %s OR last_name LIKE %s
                     ORDER BY last_name ASC, first_name ASC
                     LIMIT %d OFFSET %d",
                    $search, $search, $limit, $offset
                )
            );
        }

        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM {$this->table} ORDER BY last_name ASC, first_name ASC LIMIT %d OFFSET %d",
                $limit, $offset
            )
        );
    }

    /**
     * Update an athlete record.
     *
     * @param int   $id   Athlete ID.
     * @param array $data Fields to update.
     * @return bool
     */
    public function update( int $id, array $data ): bool {
        global $wpdb;

        $allowed = [ 'first_name', 'last_name', 'dob', 'gender', 'team_level', 'school', 'emergency_contact_name', 'emergency_contact_phone' ];
        $update  = [];

        foreach ( $allowed as $field ) {
            if ( isset( $data[ $field ] ) ) {
                $update[ $field ] = sanitize_text_field( $data[ $field ] );
            }
        }

        if ( empty( $update ) ) {
            return false;
        }

        return (bool) $wpdb->update( $this->table, $update, [ 'id' => $id ] );
    }

    /**
     * Delete an athlete record.
     *
     * @param int $id Athlete ID.
     * @return bool
     */
    public function delete( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->delete( $this->table, [ 'id' => $id ], [ '%d' ] );
    }

    /**
     * Count total athletes.
     *
     * @return int
     */
    public function count(): int {
        global $wpdb;
        return (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$this->table}" );
    }
}
