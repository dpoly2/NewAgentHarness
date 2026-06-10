<?php if ( ! defined( 'ABSPATH' ) ) exit;
if ( ! isset( $orders ) ) {
    $msg           = isset( $_GET['msg'] ) ? sanitize_key( $_GET['msg'] ) : '';
    $event_filter  = isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0;
    $status_filter = sanitize_text_field( $_GET['status'] ?? '' );
    $orders        = PBS_DB::get_orders( array_filter( [ 'event_id' => $event_filter, 'status' => $status_filter ] ) );
}
$msg          = $msg ?? '';
$orders       = is_array( $orders ) ? $orders : [];
?>
<div class="wrap">
  <h1>PBS Commerce — Orders</h1>

  <?php
  $last_order = isset( $_GET['order'] ) ? (int) $_GET['order'] : 0;
  if ( $msg === 'email_sent' ) {
      $o = $last_order ? PBS_DB::get_order( $last_order ) : null;
      $to = $o ? $o['attendee_email'] : 'attendee';
      echo '<div class="notice notice-success is-dismissible"><p>✅ Confirmation email resent to <strong>' . esc_html( $to ) . '</strong>.</p></div>';
  } elseif ( $msg === 'order_not_found' ) {
      echo '<div class="notice notice-error is-dismissible"><p>❌ Order not found.</p></div>';
  }
  ?>

  <table class="pbs-admin-table widefat striped">
    <thead>
      <tr>
        <th>Order #</th><th>Date</th><th>Event</th><th>Ticket</th>
        <th>Qty</th><th>Amount</th><th>Attendee</th><th>Email</th>
        <th>Gateway</th><th>Status</th><th>Actions</th>
      </tr>
    </thead>
    <tbody>
    <?php if ( empty( $orders ) ) : ?>
      <tr><td colspan="11" style="padding:20px;text-align:center;color:#888;">No orders yet.</td></tr>
    <?php else : ?>
      <?php foreach ( $orders as $o ) :
        $event_title  = get_the_title( $o['event_id'] ) ?: '(ID: ' . $o['event_id'] . ')';
        $status_color = [ 'complete' => '#4caf50', 'pending' => '#ff9800', 'failed' => '#f44336', 'refunded' => '#9c27b0' ][ $o['status'] ] ?? '#999';
        $receipt_url  = wp_nonce_url( admin_url( 'admin-post.php?action=pbs_print_receipt&order_id=' . $o['id'] ), 'pbs_print_receipt_' . $o['id'] );
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
        <td><span style="color:<?php echo $status_color; ?>;font-weight:600;"><?php echo esc_html( ucfirst( $o['status'] ) ); ?></span></td>
        <td style="white-space:nowrap;">
          <!-- Resend confirmation email -->
          <form method="post" action="<?php echo esc_url( admin_url('admin-post.php') ); ?>" style="display:inline;">
            <?php wp_nonce_field( 'pbs_resend_confirmation' ); ?>
            <input type="hidden" name="action" value="pbs_resend_confirmation">
            <input type="hidden" name="order_id" value="<?php echo esc_attr( $o['id'] ); ?>">
            <button type="submit" class="button button-small" title="Resend confirmation email to <?php echo esc_attr($o['attendee_email']); ?>">
              📧 Resend
            </button>
          </form>
          <!-- Printable receipt -->
          <a href="<?php echo esc_url( $receipt_url ); ?>" target="_blank" class="button button-small" title="Open printable receipt" style="margin-left:4px;">
            🖨️ Receipt
          </a>
        </td>
      </tr>
      <?php endforeach; ?>
    <?php endif; ?>
    </tbody>
  </table>
</div>
