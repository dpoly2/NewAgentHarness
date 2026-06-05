<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="wrap">
  <h1>Ticket Types</h1>
  <p>To add ticket types for an event, use this shortcode on the event page or any page:</p>
  <pre style="background:#f1f1f1;padding:12px;border-radius:6px;">
[pbs_tickets event_id="POST_ID"]
[pbs_donate event_id="POST_ID" goal="5000" label="Back to School Donations"]
  </pre>
  <p>Ticket types are managed via <strong>WP Admin → PBS Commerce → Ticket Types</strong>. Each ticket type belongs to a specific event post ID.</p>
  <p>You can add ticket types directly to the <code>wp_pbs_ticket_types</code> database table or via the REST API at <code>/wp-json/pbs-ec/v1/tickets/{event_id}</code>.</p>
</div>
