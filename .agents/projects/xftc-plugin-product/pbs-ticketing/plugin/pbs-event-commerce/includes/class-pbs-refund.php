<?php
if ( ! defined( 'ABSPATH' ) ) exit;
class PBS_Refund {
    public static function refund($order_id,$amount=null,$reason=''){
        $order=PBS_DB::get_order($order_id);
        if(!$order) return new WP_Error('not_found','Order not found.');
        if($order['status']==='refunded') return new WP_Error('already_refunded','Already refunded.');
        if($order['status']!=='complete') return new WP_Error('not_complete','Only completed orders can be refunded.');
        $amt=$amount?:(float)$order['amount'];
        $result=false;
        if($order['payment_method']==='stripe') $result=PBS_Stripe::refund($order['payment_id'],$amt);
        elseif($order['payment_method']==='paypal') $result=PBS_PayPal::refund($order['payment_id'],$amt);
        if(is_wp_error($result)) return $result;
        $new_status=($amt>=(float)$order['amount'])?'refunded':'partial_refund';
        PBS_DB::update_order_status($order_id,$new_status);
        global $wpdb;
        $meta=json_decode($order['meta']??'{}',true)?:[];
        $meta['refunds'][]=['amount'=>$amt,'reason'=>sanitize_text_field($reason),'refunded'=>current_time('mysql')];
        $wpdb->update("{$wpdb->prefix}pbs_orders",['meta'=>json_encode($meta)],['id'=>$order_id]);
        $wpdb->query($wpdb->prepare("UPDATE {$wpdb->prefix}pbs_ticket_types SET sold=GREATEST(0,sold-%d) WHERE event_id=%d AND name=%s LIMIT 1",$order['quantity'],$order['event_id'],$order['ticket_type']));
        if(class_exists('PBS_Waitlist')) PBS_Waitlist::notify_next($order['event_id'],$order['ticket_type'],$order['quantity']);
        PBS_Email::send_refund_notice($order,$amt,$reason);
        return ['success'=>true,'refunded'=>$amt,'status'=>$new_status];
    }
    public static function transfer($order_id,$new_name,$new_email,$new_phone=''){
        $order=PBS_DB::get_order($order_id);
        if(!$order) return new WP_Error('not_found','Order not found.');
        global $wpdb;
        $wpdb->update("{$wpdb->prefix}pbs_orders",['attendee_name'=>sanitize_text_field($new_name),'attendee_email'=>sanitize_email($new_email),'attendee_phone'=>sanitize_text_field($new_phone)],['id'=>$order_id]);
        PBS_Email::send_transfer_notice($order,$new_name,$new_email);
        return ['success'=>true,'message'=>'Ticket transferred successfully.'];
    }
    public static function rest_refund(WP_REST_Request $req){
        $r=self::refund((int)$req->get_param('order_id'),$req->get_param('amount')?(float)$req->get_param('amount'):null,sanitize_text_field($req->get_param('reason')??''));
        return is_wp_error($r)?new WP_REST_Response(['error'=>$r->get_error_message()],400):$r;
    }
    public static function rest_transfer(WP_REST_Request $req){
        $r=self::transfer((int)$req->get_param('order_id'),sanitize_text_field($req->get_param('new_name')),sanitize_email($req->get_param('new_email')),sanitize_text_field($req->get_param('new_phone')??''));
        return is_wp_error($r)?new WP_REST_Response(['error'=>$r->get_error_message()],400):$r;
    }
}
