<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Email {

    public static function send_confirmation( array $order ) {
        $to      = $order['attendee_email'];
        $subject = sprintf( 'Your PBS Order Confirmation — %s', $order['order_number'] );
        $from    = get_option( 'pbs_email_from', get_bloginfo( 'admin_email' ) );
        $from_name = get_option( 'pbs_email_from_name', 'Psi Beta Sigma 1914' );

        $event_title = get_the_title( $order['event_id'] ) ?: 'PBS Event';
        $is_donation = ( $order['ticket_type'] === 'Donation' );

        $body = self::confirmation_template( $order, $event_title, $is_donation );

        $headers = [
            'Content-Type: text/html; charset=UTF-8',
            "From: {$from_name} <{$from}>",
        ];

        $bcc = get_option( 'pbs_email_bcc', '' );
        if ( $bcc ) $headers[] = "BCC: {$bcc}";

        wp_mail( $to, $subject, $body, $headers );

        // Also notify chapter treasurer for donations
        if ( $is_donation ) {
            $treasurer = get_option( 'pbs_treasurer_email', 'treasurer@psibetasigma1914.org' );
            wp_mail( $treasurer, 'New PBS Donation — ' . $order['order_number'], $body, $headers );
        }
    }

    private static function confirmation_template( array $o, string $event_title, bool $is_donation ) {
        $label  = $is_donation ? 'Donation' : 'Ticket Purchase';
        $token  = substr( md5( $o['order_number'] . get_site_url() ), 0, 12 );
        $link   = add_query_arg( [ 'order_id' => $o['id'], 'token' => $token ], home_url( '/order-confirmation/' ) );
        $date   = date( 'F j, Y g:i A', strtotime( $o['created_at'] ) );
        $amount = '$' . number_format( $o['amount'], 2 );

        return <<<HTML
<!DOCTYPE html><html><head>
<style>
  body { font-family: 'Open Sans', Arial, sans-serif; background:#f5f5f5; margin:0; padding:0; }
  .wrap { max-width:560px; margin:32px auto; background:#fff; border-radius:8px; overflow:hidden; }
  .header { background:#164f90; padding:32px 24px; text-align:center; }
  .header img { height:48px; }
  .header h2 { color:#fff; margin:12px 0 0; font-size:1.3em; }
  .body { padding:28px 32px; color:#333; font-size:15px; line-height:1.6; }
  .order-box { background:#E8EDF4; border-radius:6px; padding:18px 20px; margin:20px 0; }
  .order-box table { width:100%; border-collapse:collapse; }
  .order-box td { padding:4px 0; vertical-align:top; }
  .order-box td:last-child { text-align:right; font-weight:600; }
  .cta { display:block; background:#164f90; color:#fff; text-decoration:none; text-align:center; padding:14px 20px; border-radius:6px; font-weight:700; margin:20px 0; }
  .footer { background:#0B2848; padding:16px 24px; text-align:center; color:#A2B9D3; font-size:12px; }
</style></head>
<body>
<div class="wrap">
  <div class="header">
    <h2>✅ {$label} Confirmed</h2>
  </div>
  <div class="body">
    <p>Dear <strong>{$o['attendee_name']}</strong>,</p>
    <p>Thank you for your {$label} with the <strong>Austin Sigmas Chapter of Phi Beta Sigma Fraternity, Inc.</strong></p>
    <div class="order-box">
      <table>
        <tr><td>Order Number</td><td>{$o['order_number']}</td></tr>
        <tr><td>Event</td><td>{$event_title}</td></tr>
        <tr><td>Item</td><td>{$o['ticket_type']}</td></tr>
        <tr><td>Quantity</td><td>{$o['quantity']}</td></tr>
        <tr><td>Amount Paid</td><td>{$amount}</td></tr>
        <tr><td>Date</td><td>{$date}</td></tr>
        <tr><td>Payment Via</td><td>{$o['payment_method']}</td></tr>
      </table>
    </div>
    <a class="cta" href="{$link}">View Order Confirmation</a>
    <p>If you have any questions, contact us at <a href="mailto:secretary@psibetasigma1914.org">secretary@psibetasigma1914.org</a>.</p>
    <p>Thank you for your continued support of brotherhood, scholarship, and service.</p>
    <p><strong>Psi Beta Sigma 1914 — Austin Sigmas Chapter</strong></p>
  </div>
  <div class="footer">
    Psi Beta Sigma Fraternity, Inc. | Austin, TX | psibetasigma1914.org<br>
    This is an automated confirmation. Please keep for your records.
  </div>
</div>
</body></html>
HTML;
    }
}
