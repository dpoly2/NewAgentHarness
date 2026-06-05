<?php
if ( ! defined( 'ABSPATH' ) ) exit;
class PBS_Waitlist {
    public static function add($data){
        global $wpdb;
        return $wpdb->insert("{$wpdb->prefix}pbs_waitlist",[
            'event_id'=>(int)$data['event_id'],'ticket_type'=>sanitize_text_field($data['ticket_type']??''),
            'name'=>sanitize_text_field($data['name']),'email'=>sanitize_email($data['email']),
            'phone'=>sanitize_text_field($data['phone']??''),'quantity'=>max(1,(int)($data['quantity']??1)),
            'joined_at'=>current_time('mysql'),
        ]);
    }
    public static function notify_next($event_id,$ticket_type,$spots=1){
        global $wpdb;
        $waiting=$wpdb->get_results($wpdb->prepare("SELECT * FROM {$wpdb->prefix}pbs_waitlist WHERE event_id=%d AND ticket_type=%s AND notified=0 ORDER BY joined_at ASC LIMIT %d",$event_id,$ticket_type,$spots),ARRAY_A);
        foreach($waiting as $p){
            $title=get_the_title($event_id);
            wp_mail($p['email'],"Spot opened — {$title}","Hi {$p['name']},\n\nA spot opened for {$ticket_type} at {$title}.\n\nBook now: ".home_url('/tickets/?event_id='.$event_id)."\n\n— Psi Beta Sigma 1914",['From: Psi Beta Sigma 1914 <noreply@psibetasigma1914.org>']);
            $wpdb->update("{$wpdb->prefix}pbs_waitlist",['notified'=>1],['id'=>$p['id']]);
        }
    }
    public static function rest_join(WP_REST_Request $req){
        $data=['event_id'=>(int)$req->get_param('event_id'),'ticket_type'=>sanitize_text_field($req->get_param('ticket_type')),'name'=>sanitize_text_field($req->get_param('name')),'email'=>sanitize_email($req->get_param('email')),'phone'=>sanitize_text_field($req->get_param('phone')),'quantity'=>(int)$req->get_param('quantity')];
        if(!$data['email']||!$data['name']) return new WP_Error('missing','Name and email required.',['status'=>400]);
        if(!self::add($data)) return new WP_Error('db_error','Could not add to waitlist.',['status'=>500]);
        return ['success'=>true,'message'=>"You're on the waitlist! We'll email you if a spot opens."];
    }
}
