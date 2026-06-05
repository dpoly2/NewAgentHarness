<?php
/**
 * PBS_Reports — Event analytics & CSV export
 * Like Eventbrite/Zeffy's participant reports + financial summaries.
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Reports {

    /** Get full financial + attendance summary for an event */
    public static function event_summary( $event_id ) {
        global $wpdb;

        $orders = $wpdb->get_results( $wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}pbs_orders WHERE event_id = %d AND status IN('complete','partial_refund') ORDER BY created_at DESC",
            $event_id
        ), ARRAY_A );

        $total_revenue   = 0;
        $total_tickets   = 0;
        $by_ticket_type  = [];
        $by_gateway      = [];
        $checked_in      = 0;
        $daily_sales     = [];

        foreach ( $orders as $o ) {
            $total_revenue  += (float) $o['amount'];
            $total_tickets  += (int) $o['quantity'];
            if ( $o['checked_in'] ) $checked_in++;

            $type = $o['ticket_type'];
            if ( ! isset($by_ticket_type[$type]) ) $by_ticket_type[$type] = ['count'=>0,'revenue'=>0];
            $by_ticket_type[$type]['count']   += (int) $o['quantity'];
            $by_ticket_type[$type]['revenue'] += (float) $o['amount'];

            $gw = $o['payment_method'];
            if ( ! isset($by_gateway[$gw]) ) $by_gateway[$gw] = ['count'=>0,'revenue'=>0];
            $by_gateway[$gw]['count']++;
            $by_gateway[$gw]['revenue'] += (float) $o['amount'];

            $day = substr($o['created_at'], 0, 10);
            if ( ! isset($daily_sales[$day]) ) $daily_sales[$day] = ['orders'=>0,'revenue'=>0];
            $daily_sales[$day]['orders']++;
            $daily_sales[$day]['revenue'] += (float) $o['amount'];
        }

        // Capacity info
        $capacity_rows = $wpdb->get_results( $wpdb->prepare(
            "SELECT name, capacity, sold FROM {$wpdb->prefix}pbs_ticket_types WHERE event_id = %d AND active = 1",
            $event_id
        ), ARRAY_A );
        $total_capacity = array_sum( array_column($capacity_rows, 'capacity') );

        return [
            'event_id'       => $event_id,
            'event_title'    => get_the_title($event_id),
            'total_orders'   => count($orders),
            'total_tickets'  => $total_tickets,
            'total_revenue'  => round($total_revenue, 2),
            'total_capacity' => $total_capacity,
            'checked_in'     => $checked_in,
            'by_ticket_type' => $by_ticket_type,
            'by_gateway'     => $by_gateway,
            'daily_sales'    => $daily_sales,
        ];
    }

    /** Generate and output a CSV of all attendees for an event */
    public static function export_csv( $event_id ) {
        global $wpdb;

        $event_title = get_the_title($event_id);
        $filename    = 'pbs-attendees-' . sanitize_title($event_title) . '-' . date('Ymd') . '.csv';

        $orders = $wpdb->get_results( $wpdb->prepare(
            "SELECT o.*, GROUP_CONCAT(CONCAT(q.label, ': ', a.answer) SEPARATOR ' | ') as custom_answers
             FROM {$wpdb->prefix}pbs_orders o
             LEFT JOIN {$wpdb->prefix}pbs_answers a ON a.order_id = o.id
             LEFT JOIN {$wpdb->prefix}pbs_questions q ON q.id = a.question_id
             WHERE o.event_id = %d AND o.status IN('complete','partial_refund')
             GROUP BY o.id
             ORDER BY o.attendee_name ASC",
            $event_id
        ), ARRAY_A );

        header('Content-Type: text/csv; charset=utf-8');
        header("Content-Disposition: attachment; filename=\"{$filename}\"");
        $out = fopen('php://output', 'w');

        fputcsv($out, ['Order #','Name','Email','Phone','Ticket Type','Qty','Amount','Payment','Checked In','Check-in Time','Date','Custom Answers']);
        foreach ( $orders as $o ) {
            fputcsv($out, [
                $o['order_number'],
                $o['attendee_name'],
                $o['attendee_email'],
                $o['attendee_phone'],
                $o['ticket_type'],
                $o['quantity'],
                '$' . number_format($o['amount'], 2),
                strtoupper($o['payment_method']),
                $o['checked_in'] ? 'Yes' : 'No',
                $o['checked_in_at'] ?? '',
                $o['created_at'],
                $o['custom_answers'] ?? '',
            ]);
        }
        fclose($out);
        exit;
    }

    /** REST: get event summary (admin) */
    public static function rest_summary( WP_REST_Request $req ) {
        return self::event_summary( (int) $req['event_id'] );
    }

    /** REST: export CSV (admin, triggers download) */
    public static function rest_export( WP_REST_Request $req ) {
        self::export_csv( (int) $req['event_id'] );
    }
}
