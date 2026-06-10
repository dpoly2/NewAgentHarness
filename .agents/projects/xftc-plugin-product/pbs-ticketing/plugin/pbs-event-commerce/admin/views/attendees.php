<?php if ( ! defined( 'ABSPATH' ) ) exit;
if ( ! isset( $orders ) ) {
    $event_id  = isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0;
    $status    = isset( $_GET['status'] ) ? sanitize_text_field( $_GET['status'] ) : 'complete';
    $search    = isset( $_GET['s'] ) ? sanitize_text_field( $_GET['s'] ) : '';
    $args      = [ 'status' => $status, 'limit' => 500 ];
    if ( $event_id ) $args['event_id'] = $event_id;
    $orders    = PBS_DB::get_orders( $args ) ?: [];
    if ( $search ) {
        $orders = array_filter( $orders, function( $o ) use ( $search ) {
            return stripos( $o['attendee_name'], $search ) !== false
                || stripos( $o['attendee_email'], $search ) !== false
                || stripos( $o['order_number'], $search ) !== false;
        } );
    }
    global $wpdb;
    $event_ids = $wpdb->get_col( "SELECT DISTINCT event_id FROM {$wpdb->prefix}pbs_orders ORDER BY event_id DESC" );
}
$event_id  = $event_id ?? 0;
$status    = $status ?? 'complete';
$search    = $search ?? '';
$orders    = is_array( $orders ) ? array_values( $orders ) : [];
$event_ids = $event_ids ?? [];
?>
<div class="wrap">
<h1>Attendees<?php echo $event_id ? ' — ' . esc_html( get_the_title( $event_id ) ) : ''; ?></h1>

<form method="get" style="margin-bottom:16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
  <input type="hidden" name="page" value="pbs-attendees">
  <input type="text" name="s" value="<?php echo esc_attr( $search ); ?>" placeholder="Search name, email, order #…" class="regular-text">
  <select name="event_id">
    <option value="">All Events</option>
    <?php foreach ( $event_ids as $eid ) :
      $title = get_the_title( (int) $eid ) ?: "Event #{$eid}"; ?>
      <option value="<?php echo esc_attr( $eid ); ?>" <?php selected( $event_id, (int) $eid ); ?>><?php echo esc_html( $title ); ?></option>
    <?php endforeach; ?>
  </select>
  <select name="status">
    <?php foreach ( [ 'complete' => 'Completed', 'pending' => 'Pending', 'failed' => 'Failed', '' => 'All Statuses' ] as $val => $label ) : ?>
      <option value="<?php echo esc_attr( $val ); ?>" <?php selected( $status, $val ); ?>><?php echo esc_html( $label ); ?></option>
    <?php endforeach; ?>
  </select>
  <?php submit_button( 'Filter', 'secondary', '', false ); ?>
  <?php if ( $search || $event_id || $status !== 'complete' ) : ?>
    <a href="<?php echo esc_url( admin_url('admin.php?page=pbs-attendees') ); ?>" class="button">Reset</a>
  <?php endif; ?>
</form>

<p style="color:#888;font-size:13px;"><?php echo count( $orders ); ?> attendee<?php echo count($orders) !== 1 ? 's' : ''; ?> found.</p>

<table class="pbs-admin-table widefat striped">
  <thead>
    <tr><th>Order #</th><th>Name</th><th>Email</th><th>Phone</th><th>Ticket</th><th>Qty</th><th>Amount</th><th>Gateway</th><th>Date</th></tr>
  </thead>
  <tbody>
  <?php if ( empty( $orders ) ) : ?>
    <tr><td colspan="9" style="text-align:center;padding:24px;color:#888;">No attendees found.</td></tr>
  <?php else : ?>
    <?php foreach ( $orders as $o ) : ?>
    <tr>
      <td><?php echo esc_html( $o['order_number'] ); ?></td>
      <td><?php echo esc_html( $o['attendee_name'] ); ?></td>
      <td><a href="mailto:<?php echo esc_attr( $o['attendee_email'] ); ?>"><?php echo esc_html( $o['attendee_email'] ); ?></a></td>
      <td><?php echo esc_html( $o['attendee_phone'] ); ?></td>
      <td><?php echo esc_html( $o['ticket_type'] ); ?></td>
      <td><?php echo esc_html( $o['quantity'] ); ?></td>
      <td>$<?php echo number_format( (float) $o['amount'], 2 ); ?></td>
      <td><?php echo esc_html( strtoupper( $o['payment_method'] ) ); ?></td>
      <td><?php echo esc_html( date( 'M j, Y g:i A', strtotime( $o['created_at'] ) ) ); ?></td>
    </tr>
    <?php endforeach; ?>
  <?php endif; ?>
  </tbody>
</table>
</div>
