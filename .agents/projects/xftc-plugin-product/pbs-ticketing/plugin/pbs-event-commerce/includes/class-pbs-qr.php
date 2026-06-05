<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_QR {
    public static function generate_token( $order_id, $order_number ) {
        return hash_hmac( 'sha256', $order_id . '|' . $order_number, wp_salt('auth') );
    }
    public static function verify_token( $order_id, $order_number, $token ) {
        return hash_equals( self::generate_token( $order_id, $order_number ), $token );
    }
    public static function qr_img( $order_id, $order_number, $size = 200 ) {
        $token   = self::generate_token( $order_id, $order_number );
        $payload = urlencode( json_encode(['id'=>$order_id,'num'=>$order_number,'tok'=>$token]) );
        $url = "https://chart.googleapis.com/chart?chs={$size}x{$size}&cht=qr&chl={$payload}&choe=UTF-8";
        return '<img src="' . esc_url($url) . '" alt="QR Code" class="pbs-qr-code" width="' . $size . '" height="' . $size . '">';
    }
    public static function checkin( WP_REST_Request $req ) {
        $order_id     = (int) $req->get_param('order_id');
        $order_number = sanitize_text_field( $req->get_param('order_number') );
        $token        = sanitize_text_field( $req->get_param('token') );
        if ( ! self::verify_token( $order_id, $order_number, $token ) )
            return new WP_Error('invalid_token','Invalid QR code.',['status'=>403]);
        $order = PBS_DB::get_order( $order_id );
        if ( ! $order ) return new WP_Error('not_found','Order not found.',['status'=>404]);
        if ( $order['status'] !== 'complete' ) return new WP_Error('not_complete','Order not completed.',['status'=>400]);
        global $wpdb;
        $already = $wpdb->get_var($wpdb->prepare("SELECT checked_in FROM {$wpdb->prefix}pbs_orders WHERE id=%d",$order_id));
        if ($already) return ['success'=>false,'message'=>'Already checked in.','order'=>$order,'duplicate'=>true];
        $wpdb->update("{$wpdb->prefix}pbs_orders",['checked_in'=>1,'checked_in_at'=>current_time('mysql')],['id'=>$order_id]);
        return ['success'=>true,'message'=>'Check-in successful!','order'=>$order,'duplicate'=>false];
    }
    public static function checkin_list( WP_REST_Request $req ) {
        global $wpdb;
        $event_id = (int) $req['event_id'];
        $rows = $wpdb->get_results($wpdb->prepare(
            "SELECT id,order_number,attendee_name,attendee_email,ticket_type,quantity,checked_in,checked_in_at FROM {$wpdb->prefix}pbs_orders WHERE event_id=%d AND status='complete' ORDER BY attendee_name ASC",
            $event_id
        ),ARRAY_A);
        $total=$count($rows); $checked=count(array_filter($rows,fn($r)=>$r['checked_in']));
        return ['total'=>$total,'checked_in'=>$checked,'remaining'=>$total-$checked,'attendees'=>$rows];
    }
}
