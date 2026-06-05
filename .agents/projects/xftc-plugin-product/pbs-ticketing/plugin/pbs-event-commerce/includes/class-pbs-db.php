<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_DB {

    public static function install() {
        global $wpdb;
        $charset = $wpdb->get_charset_collate();

        // Orders table
        $orders_sql = "CREATE TABLE IF NOT EXISTS {$wpdb->prefix}pbs_orders (
            id              INT(11) NOT NULL AUTO_INCREMENT,
            order_number    VARCHAR(30)  NOT NULL,
            event_id        INT(11)      NOT NULL DEFAULT 0,
            ticket_type     VARCHAR(150) NOT NULL DEFAULT '',
            quantity        INT(5)       NOT NULL DEFAULT 1,
            amount          DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            attendee_name   VARCHAR(200) NOT NULL DEFAULT '',
            attendee_email  VARCHAR(200) NOT NULL DEFAULT '',
            attendee_phone  VARCHAR(30)  NOT NULL DEFAULT '',
            payment_method  VARCHAR(20)  NOT NULL DEFAULT '',
            payment_id      VARCHAR(250) NOT NULL DEFAULT '',
            status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
            meta            LONGTEXT,
            created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY event_id (event_id),
            KEY status (status),
            KEY attendee_email (attendee_email)
        ) $charset;";

        // Attendees table (for multi-ticket orders)
        $attendees_sql = "CREATE TABLE IF NOT EXISTS {$wpdb->prefix}pbs_attendees (
            id              INT(11) NOT NULL AUTO_INCREMENT,
            order_id        INT(11) NOT NULL,
            name            VARCHAR(200) NOT NULL DEFAULT '',
            email           VARCHAR(200) NOT NULL DEFAULT '',
            phone           VARCHAR(30)  NOT NULL DEFAULT '',
            ticket_type     VARCHAR(150) NOT NULL DEFAULT '',
            PRIMARY KEY (id),
            KEY order_id (order_id)
        ) $charset;";

        // Ticket types table — admin-configurable per event
        $tickets_sql = "CREATE TABLE IF NOT EXISTS {$wpdb->prefix}pbs_ticket_types (
            id              INT(11) NOT NULL AUTO_INCREMENT,
            event_id        INT(11) NOT NULL,
            name            VARCHAR(150) NOT NULL,
            description     TEXT,
            price           DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            capacity        INT(6) NOT NULL DEFAULT 0,
            sold            INT(6) NOT NULL DEFAULT 0,
            ticket_start    DATETIME,
            ticket_end      DATETIME,
            is_donation     TINYINT(1) NOT NULL DEFAULT 0,
            sort_order      INT(3) NOT NULL DEFAULT 0,
            active          TINYINT(1) NOT NULL DEFAULT 1,
            PRIMARY KEY (id),
            KEY event_id (event_id)
        ) $charset;";

        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        dbDelta( $orders_sql );
        dbDelta( $attendees_sql );
        dbDelta( $tickets_sql );

        update_option( 'pbs_ec_db_version', PBS_EC_VERSION );
    }

    /** Generate unique order number: PBS-20260926-0001 */
    public static function generate_order_number() {
        global $wpdb;
        $date   = date( 'Ymd' );
        $prefix = "PBS-{$date}-";
        $last   = $wpdb->get_var(
            $wpdb->prepare(
                "SELECT order_number FROM {$wpdb->prefix}pbs_orders WHERE order_number LIKE %s ORDER BY id DESC LIMIT 1",
                $prefix . '%'
            )
        );
        $seq = $last ? ( (int) substr( $last, -4 ) + 1 ) : 1;
        return $prefix . str_pad( $seq, 4, '0', STR_PAD_LEFT );
    }

    /** Insert a new order, return order ID */
    public static function insert_order( array $data ) {
        global $wpdb;
        $data['order_number'] = self::generate_order_number();
        $data['created_at']   = current_time( 'mysql' );
        if ( isset( $data['meta'] ) && is_array( $data['meta'] ) ) {
            $data['meta'] = json_encode( $data['meta'] );
        }
        $wpdb->insert( "{$wpdb->prefix}pbs_orders", $data );
        return $wpdb->insert_id;
    }

    /** Update order status */
    public static function update_order_status( $order_id, $status, $payment_id = '' ) {
        global $wpdb;
        $update = [ 'status' => $status ];
        if ( $payment_id ) $update['payment_id'] = $payment_id;
        $wpdb->update( "{$wpdb->prefix}pbs_orders", $update, [ 'id' => $order_id ] );
    }

    /** Get order by ID */
    public static function get_order( $order_id ) {
        global $wpdb;
        return $wpdb->get_row(
            $wpdb->prepare( "SELECT * FROM {$wpdb->prefix}pbs_orders WHERE id = %d", $order_id ),
            ARRAY_A
        );
    }

    /** Get ticket types for an event */
    public static function get_ticket_types( $event_id ) {
        global $wpdb;
        return $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM {$wpdb->prefix}pbs_ticket_types WHERE event_id = %d AND active = 1 ORDER BY sort_order ASC",
                $event_id
            ),
            ARRAY_A
        );
    }

    /** Get all orders with optional filters */
    public static function get_orders( $args = [] ) {
        global $wpdb;
        $where  = '1=1';
        $values = [];
        if ( ! empty( $args['event_id'] ) ) {
            $where .= ' AND event_id = %d';
            $values[] = $args['event_id'];
        }
        if ( ! empty( $args['status'] ) ) {
            $where .= ' AND status = %s';
            $values[] = $args['status'];
        }
        $limit  = ! empty( $args['limit'] ) ? (int) $args['limit'] : 200;
        $sql    = "SELECT * FROM {$wpdb->prefix}pbs_orders WHERE $where ORDER BY created_at DESC LIMIT $limit";
        if ( $values ) {
            return $wpdb->get_results( $wpdb->prepare( $sql, ...$values ), ARRAY_A );
        }
        return $wpdb->get_results( $sql, ARRAY_A );
    }
}
