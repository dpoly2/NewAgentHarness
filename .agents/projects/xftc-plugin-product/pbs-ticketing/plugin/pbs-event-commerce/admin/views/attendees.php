<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<h3>Attendees<?php echo $event_id ? ' — ' . get_the_title($event_id) : ''; ?></h3>
<table class="pbs-admin-table widefat">
  <thead><tr><th>Order #</th><th>Name</th><th>Email</th><th>Phone</th><th>Ticket</th><th>Qty</th><th>Date</th></tr></thead>
  <tbody>
  <?php foreach ($orders as $o) : ?>
  <tr>
    <td><?php echo esc_html($o['order_number']); ?></td>
    <td><?php echo esc_html($o['attendee_name']); ?></td>
    <td><?php echo esc_html($o['attendee_email']); ?></td>
    <td><?php echo esc_html($o['attendee_phone']); ?></td>
    <td><?php echo esc_html($o['ticket_type']); ?></td>
    <td><?php echo esc_html($o['quantity']); ?></td>
    <td><?php echo esc_html(date('M j, Y', strtotime($o['created_at']))); ?></td>
  </tr>
  <?php endforeach; ?>
  </tbody>
</table>
