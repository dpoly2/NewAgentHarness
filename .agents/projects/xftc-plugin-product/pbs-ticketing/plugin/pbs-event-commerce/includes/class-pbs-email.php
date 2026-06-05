<?php
/**
 * PBS_Email — All transactional emails with QR e-tickets, refunds, transfers, reminders
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Email {

    private static function headers() {
        $from_name  = get_option('pbs_email_from_name', 'Psi Beta Sigma 1914');
        $from_email = get_option('pbs_email_from', 'noreply@psibetasigma1914.org');
        $headers    = ["From: {$from_name} <{$from_email}>", 'Content-Type: text/html; charset=UTF-8'];
        $bcc        = get_option('pbs_email_bcc', '');
        if ($bcc) $headers[] = "Bcc: {$bcc}";
        return $headers;
    }

    private static function wrap( $body, $title = 'Psi Beta Sigma 1914' ) {
        return '<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#333;">
        <div style="background:#164f90;padding:20px;text-align:center;border-radius:8px 8px 0 0;">
          <h2 style="color:#fff;margin:0;">Psi Beta Sigma 1914</h2>
          <p style="color:rgba(255,255,255,0.8);margin:4px 0 0;font-size:14px;">Austin, Texas Chapter</p>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;padding:28px;border-radius:0 0 8px 8px;">'
        . $body .
        '</div>
        <p style="text-align:center;font-size:12px;color:#999;margin-top:16px;">
          Questions? <a href="mailto:secretary@psibetasigma1914.org" style="color:#164f90;">secretary@psibetasigma1914.org</a>
        </p></body></html>';
    }

    /** Order confirmation + e-ticket with QR code */
    public static function send_confirmation( $order ) {
        $event_title = get_the_title($order['event_id']);
        $event       = tribe_get_event($order['event_id']);
        $event_date  = $event ? tribe_get_start_date($order['event_id'], false, 'F j, Y g:i A') : '';
        $event_venue = $event ? tribe_get_venue($order['event_id']) : '';

        // QR code
        $qr_token = PBS_QR::generate_token($order['id'], $order['order_number']);
        $qr_img   = PBS_QR::qr_img($order['id'], $order['order_number'], 180);

        // Custom question answers
        $answers_html = '';
        if (class_exists('PBS_Custom_Questions')) {
            $answers = PBS_Custom_Questions::get_answers($order['id']);
            foreach ($answers as $a) {
                $answers_html .= '<tr><td style="padding:6px 12px;color:#666;">' . esc_html($a['label']) . '</td><td style="padding:6px 12px;">' . esc_html($a['answer']) . '</td></tr>';
            }
        }

        $body = '
        <h3 style="color:#2e7d32;">✅ Order Confirmed!</h3>
        <p>Hi <strong>' . esc_html($order['attendee_name']) . '</strong>, your order is confirmed. Please bring this e-ticket to the event.</p>

        <div style="border:2px dashed #164f90;border-radius:8px;padding:20px;margin:20px 0;text-align:center;">
          <h4 style="margin:0 0 4px;color:#164f90;">' . esc_html($event_title) . '</h4>
          ' . ($event_date ? '<p style="margin:4px 0;color:#555;">' . $event_date . '</p>' : '') . '
          ' . ($event_venue ? '<p style="margin:4px 0;color:#555;">📍 ' . $event_venue . '</p>' : '') . '
          <hr style="border:none;border-top:1px solid #e0e0e0;margin:16px 0;">
          <p style="font-size:18px;font-weight:bold;margin:0 0 4px;">Order #' . esc_html($order['order_number']) . '</p>
          <p style="margin:0 0 16px;color:#555;">' . esc_html($order['ticket_type']) . ' × ' . (int)$order['quantity'] . '</p>
          ' . $qr_img . '
          <p style="font-size:11px;color:#999;margin:8px 0 0;">Scan at the door for entry</p>
        </div>

        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr style="background:#f5f5f5;"><td style="padding:8px 12px;font-weight:bold;" colspan="2">Order Details</td></tr>
          <tr><td style="padding:6px 12px;color:#666;">Order Number</td><td style="padding:6px 12px;"><strong>' . esc_html($order['order_number']) . '</strong></td></tr>
          <tr style="background:#f9f9f9;"><td style="padding:6px 12px;color:#666;">Amount Paid</td><td style="padding:6px 12px;"><strong>$' . number_format($order['amount'],2) . '</strong></td></tr>
          ' . ($order['promo_code'] ? '<tr><td style="padding:6px 12px;color:#666;">Promo Code</td><td style="padding:6px 12px;">' . esc_html($order['promo_code']) . ' (−$' . number_format($order['discount_amount'],2) . ')</td></tr>' : '') . '
          <tr><td style="padding:6px 12px;color:#666;">Payment Method</td><td style="padding:6px 12px;">' . strtoupper($order['payment_method']) . '</td></tr>
          ' . $answers_html . '
        </table>';

        $to      = $order['attendee_email'];
        $subject = "Your Ticket — {$event_title} | #{$order['order_number']}";
        wp_mail($to, $subject, self::wrap($body, $event_title), self::headers());

        // Also notify treasurer
        $treasurer = get_option('pbs_treasurer_email', '');
        if ($treasurer) {
            $admin_body = '<h3>New Order Received</h3>' . '<p><strong>' . esc_html($order['attendee_name']) . '</strong> purchased ' . esc_html($order['ticket_type']) . ' × ' . (int)$order['quantity'] . ' for <strong>$' . number_format($order['amount'],2) . '</strong> via ' . strtoupper($order['payment_method']) . '.</p><p>Order: ' . esc_html($order['order_number']) . '</p>';
            wp_mail($treasurer, "New Order #{$order['order_number']} — {$event_title}", self::wrap($admin_body), self::headers());
        }
    }

    /** Refund confirmation email */
    public static function send_refund_notice( $order, $refund_amount, $reason = '' ) {
        $event_title = get_the_title($order['event_id']);
        $body = '
        <h3 style="color:#e65100;">Refund Processed</h3>
        <p>Hi <strong>' . esc_html($order['attendee_name']) . '</strong>, a refund has been issued for your order.</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:6px 12px;color:#666;">Order</td><td style="padding:6px 12px;">' . esc_html($order['order_number']) . '</td></tr>
          <tr style="background:#f9f9f9;"><td style="padding:6px 12px;color:#666;">Event</td><td style="padding:6px 12px;">' . esc_html($event_title) . '</td></tr>
          <tr><td style="padding:6px 12px;color:#666;">Refund Amount</td><td style="padding:6px 12px;"><strong>$' . number_format($refund_amount,2) . '</strong></td></tr>
          ' . ($reason ? '<tr style="background:#f9f9f9;"><td style="padding:6px 12px;color:#666;">Reason</td><td style="padding:6px 12px;">' . esc_html($reason) . '</td></tr>' : '') . '
        </table>
        <p style="font-size:13px;color:#666;margin-top:16px;">Refunds typically appear in 3–5 business days depending on your bank.</p>';

        wp_mail($order['attendee_email'], "Refund — Order #{$order['order_number']}", self::wrap($body), self::headers());
    }

    /** Ticket transfer confirmation email */
    public static function send_transfer_notice( $order, $new_name, $new_email ) {
        $event_title = get_the_title($order['event_id']);

        // Notify original purchaser
        $body_original = '<h3>Ticket Transfer Confirmed</h3><p>Your ticket for <strong>' . esc_html($event_title) . '</strong> (Order #' . esc_html($order['order_number']) . ') has been transferred to <strong>' . esc_html($new_name) . '</strong> (' . esc_html($new_email) . ').</p>';
        wp_mail($order['attendee_email'], "Ticket Transferred — #{$order['order_number']}", self::wrap($body_original), self::headers());

        // Send new e-ticket to new attendee
        $qr_img = PBS_QR::qr_img($order['id'], $order['order_number'], 180);
        $body_new = '
        <h3 style="color:#2e7d32;">🎟️ Ticket Transferred to You!</h3>
        <p>Hi <strong>' . esc_html($new_name) . '</strong>, a ticket for <strong>' . esc_html($event_title) . '</strong> has been transferred to you.</p>
        <div style="border:2px dashed #164f90;border-radius:8px;padding:20px;margin:20px 0;text-align:center;">
          <p style="font-size:18px;font-weight:bold;margin:0 0 4px;">Order #' . esc_html($order['order_number']) . '</p>
          <p style="margin:0 0 16px;">' . esc_html($order['ticket_type']) . '</p>
          ' . $qr_img . '
          <p style="font-size:11px;color:#999;margin:8px 0 0;">Scan at the door for entry</p>
        </div>';
        wp_mail($new_email, "Your Ticket — {$event_title}", self::wrap($body_new), self::headers());
    }

    /** Event reminder email (called by a scheduled hook) */
    public static function send_reminder( $event_id, $days_before = 3 ) {
        global $wpdb;
        $event_title = get_the_title($event_id);
        $event_date  = tribe_get_start_date($event_id, false, 'F j, Y g:i A');
        $event_venue = tribe_get_venue($event_id);

        $orders = $wpdb->get_results( $wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}pbs_orders WHERE event_id = %d AND status = 'complete'",
            $event_id
        ), ARRAY_A );

        foreach ($orders as $order) {
            $qr_img = PBS_QR::qr_img($order['id'], $order['order_number'], 150);
            $body = '
            <h3>📅 Event Reminder — ' . esc_html($event_title) . '</h3>
            <p>Hi <strong>' . esc_html($order['attendee_name']) . '</strong>, your event is coming up in <strong>' . $days_before . ' days</strong>!</p>
            <p><strong>Date:</strong> ' . $event_date . '<br>' . ($event_venue ? '<strong>Location:</strong> ' . $event_venue : '') . '</p>
            <div style="text-align:center;margin:20px 0;">
              <p><strong>Your E-Ticket (Order #' . esc_html($order['order_number']) . ')</strong></p>
              ' . $qr_img . '
              <p style="font-size:11px;color:#999;">Screenshot this for quick check-in at the door.</p>
            </div>';
            wp_mail($order['attendee_email'], "Reminder: {$event_title} in {$days_before} days!", self::wrap($body), self::headers());
        }
    }
}
