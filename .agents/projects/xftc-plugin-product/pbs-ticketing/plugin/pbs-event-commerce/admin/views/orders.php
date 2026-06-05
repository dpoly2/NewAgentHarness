<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="wrap">
  <h1>PBS Commerce — Orders</h1>
  <table class="pbs-admin-table widefat">
    <thead>
      <tr>
        <th>Order #</th><th>Date</th><th>Event</th><th>Ticket</th>
        <th>Qty</th><th>Amount</th><th>Attendee</th><th>Email</th>
        <th>Gateway</th><th>Status</th><th>Transaction ID</th>
      </tr>
    </thead>
    <tbody>
    <?php if ( empty( $orders ) ) : ?>
      <tr><td colspan="11" style="padding:20px;text-align:center;">No orders yet.</td></tr>
    <?php else : ?>
      <?php foreach ( $orders as $o ) :
        $event_title = get_the_title( $o['event_id'] ) ?: '(ID: ' . $o['event_id'] . ')';
        $status_class = 'pbs-status-' . $o['status'];
      ?>
      <tr>
        <td><strong><?php echo esc_html( $o['order_number'] ); ?></strong></td>
        <td><?php echo esc_html( date( 'M j, Y', strtotime( $o['created_at'] ) ) ); ?></td>
        <td><?php echo esc_html( $event_title ); ?></td>
        <td><?php echo esc_html( $o['ticket_type'] ); ?></td>
        <td><?php echo esc_html( $o['quantity'] ); ?></td>
        <td><strong>$<?php echo number_format( $o['amount'], 2 ); ?></strong></td>
        <td><?php echo esc_html( $o['attendee_name'] ); ?></td>
        <td><a href="mailto:<?php echo esc_attr( $o['attendee_email'] ); ?>"><?php echo esc_html( $o['attendee_email'] ); ?></a></td>
        <td><?php echo esc_html( strtoupper( $o['payment_method'] ) ); ?></td>
        <td><span class="<?php echo esc_attr( $status_class ); ?>"><?php echo esc_html( ucfirst( $o['status'] ) ); ?></span></td>
        <td style="font-size:11px;"><?php echo esc_html( $o['payment_id'] ); ?></td>
      </tr>
      <?php endforeach; ?>
    <?php endif; ?>
    </tbody>
  </table>
</div>
