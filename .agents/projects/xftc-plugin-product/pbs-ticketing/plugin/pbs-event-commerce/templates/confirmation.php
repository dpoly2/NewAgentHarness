<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="tribe-tickets pbs-confirmation">
  <div style="background:#2e7d32;color:#fff;border-radius:8px;padding:24px;text-align:center;margin-bottom:24px;">
    <h2 style="margin:0;color:#fff;">&#x2705; Order Confirmed!</h2>
    <p style="margin:8px 0 0;opacity:.9;">Order #<?php echo esc_html($order['order_number']); ?></p>
  </div>
  <table class="pbs-admin-table" style="margin-bottom:24px;">
    <tr><th>Event</th><td><?php echo esc_html(get_the_title($order['event_id'])); ?></td></tr>
    <tr><th>Ticket</th><td><?php echo esc_html($order['ticket_type']); ?></td></tr>
    <tr><th>Quantity</th><td><?php echo esc_html($order['quantity']); ?></td></tr>
    <tr><th>Amount</th><td><strong>$<?php echo number_format($order['amount'], 2); ?></strong></td></tr>
    <tr><th>Name</th><td><?php echo esc_html($order['attendee_name']); ?></td></tr>
    <tr><th>Email</th><td><?php echo esc_html($order['attendee_email']); ?></td></tr>
    <tr><th>Paid Via</th><td><?php echo esc_html(strtoupper($order['payment_method'])); ?></td></tr>
    <tr><th>Date</th><td><?php echo esc_html(date('F j, Y g:i A', strtotime($order['created_at']))); ?></td></tr>
  </table>
  <p>A confirmation email has been sent to <strong><?php echo esc_html($order['attendee_email']); ?></strong>.</p>
  <p>Questions? Email <a href="mailto:secretary@psibetasigma1914.org">secretary@psibetasigma1914.org</a></p>
</div>
