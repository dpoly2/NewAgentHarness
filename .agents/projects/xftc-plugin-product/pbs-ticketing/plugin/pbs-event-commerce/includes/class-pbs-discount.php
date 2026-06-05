<?php
if ( ! defined( 'ABSPATH' ) ) exit;
class PBS_Discount {
    public static function validate( $code, $event_id, $subtotal ) {
        global $wpdb;
        $code  = strtoupper(sanitize_text_field($code));
        $promo = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}pbs_promo_codes WHERE code=%s AND active=1 AND (event_id=0 OR event_id=%d) AND (expires_at IS NULL OR expires_at>NOW()) AND (max_uses=0 OR used_count<max_uses)",
            $code,$event_id
        ),ARRAY_A);
        if(!$promo) return new WP_Error('invalid_code','Promo code is invalid or expired.');
        $discount = 0.00;
        if($promo['type']==='percent') $discount=round($subtotal*($promo['value']/100),2);
        elseif($promo['type']==='flat') $discount=min($promo['value'],$subtotal);
        elseif($promo['type']==='free') $discount=$subtotal;
        return ['id'=>$promo['id'],'code'=>$promo['code'],'type'=>$promo['type'],'value'=>$promo['value'],'discount_amount'=>$discount,'new_total'=>max(0,$subtotal-$discount)];
    }
    public static function increment_usage($promo_id){
        global $wpdb;
        $wpdb->query($wpdb->prepare("UPDATE {$wpdb->prefix}pbs_promo_codes SET used_count=used_count+1 WHERE id=%d",$promo_id));
    }
    public static function rest_validate(WP_REST_Request $req){
        $result=self::validate(sanitize_text_field($req->get_param('code')),(int)$req->get_param('event_id'),(float)$req->get_param('subtotal'));
        if(is_wp_error($result)) return ['valid'=>false,'message'=>$result->get_error_message()];
        return array_merge(['valid'=>true],$result);
    }
}
