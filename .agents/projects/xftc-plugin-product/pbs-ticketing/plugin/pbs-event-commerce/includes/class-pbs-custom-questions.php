<?php
if ( ! defined( 'ABSPATH' ) ) exit;
class PBS_Custom_Questions {
    public static function get_for_event($event_id){
        global $wpdb;
        return $wpdb->get_results($wpdb->prepare("SELECT * FROM {$wpdb->prefix}pbs_questions WHERE (event_id=%d OR event_id=0) AND active=1 ORDER BY sort_order ASC",$event_id),ARRAY_A);
    }
    public static function save_answers($order_id,$answers){
        global $wpdb;
        foreach($answers as $qid=>$ans) $wpdb->insert("{$wpdb->prefix}pbs_answers",['order_id'=>(int)$order_id,'question_id'=>(int)$qid,'answer'=>sanitize_textarea_field($ans)]);
    }
    public static function get_answers($order_id){
        global $wpdb;
        return $wpdb->get_results($wpdb->prepare("SELECT q.label,a.answer FROM {$wpdb->prefix}pbs_answers a JOIN {$wpdb->prefix}pbs_questions q ON q.id=a.question_id WHERE a.order_id=%d",$order_id),ARRAY_A);
    }
    public static function render_fields($event_id){
        $questions=self::get_for_event($event_id);
        if(empty($questions)) return '';
        ob_start();
        echo '<div class="pbs-custom-questions"><h4>Additional Information</h4>';
        foreach($questions as $q){
            $req=$q['required']?'required':''; $rl=$q['required']?' <span class="pbs-req">*</span>':''; $name='pbs_q_'.$q['id'];
            echo "<div class='pbs-question-field'><label for='{$name}'>".esc_html($q['label']).$rl."</label>";
            switch($q['type']){
                case 'textarea': echo "<textarea name='{$name}' id='{$name}' class='tribe-tickets__input' {$req} rows='3'></textarea>"; break;
                case 'select':
                    $opts=array_map('trim',explode("\n",$q['options']??''));
                    echo "<select name='{$name}' id='{$name}' class='tribe-tickets__input' {$req}><option value=''>— Select —</option>";
                    foreach($opts as $o) echo "<option value='".esc_attr($o)."'>".esc_html($o)."</option>";
                    echo "</select>"; break;
                case 'checkbox': echo "<label class='pbs-checkbox-label'><input type='checkbox' name='{$name}' value='1' {$req}> ".esc_html($q['label'])."</label>"; break;
                default: echo "<input type='text' name='{$name}' id='{$name}' class='tribe-tickets__input' {$req}>";
            }
            echo "</div>";
        }
        echo '</div>';
        return ob_get_clean();
    }
    public static function rest_get(WP_REST_Request $req){ return self::get_for_event((int)$req['event_id']); }
}
