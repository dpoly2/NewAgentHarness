<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="wrap">
<h1>Ticket Types <?php if ( $event_id ) echo '— ' . esc_html( get_the_title( $event_id ) ); ?></h1>

<?php
$msgs = [ 'added' => '✅ Ticket type added.', 'saved' => '✅ Ticket type updated.', 'deleted' => '🗑 Ticket type deleted.' ];
if ( $msg && isset( $msgs[$msg] ) ) echo '<div class="notice notice-success is-dismissible"><p>' . esc_html( $msgs[$msg] ) . '</p></div>';
?>

<div style="display:grid;grid-template-columns:1fr 380px;gap:24px;align-items:start;">

<!-- ── List ── -->
<div>
  <div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;">
    <form method="get">
      <input type="hidden" name="page" value="pbs-ticket-types">
      <select name="event_id" onchange="this.form.submit()" style="max-width:300px;">
        <option value="">All Events</option>
        <?php foreach ( $tt_event_ids as $eid ) :
          $t = get_the_title( (int)$eid ) ?: "Event #{$eid}"; ?>
          <option value="<?php echo esc_attr($eid); ?>" <?php selected($event_id,(int)$eid); ?>><?php echo esc_html($t); ?></option>
        <?php endforeach; ?>
      </select>
    </form>
    <a href="<?php echo esc_url( add_query_arg(['page'=>'pbs-ticket-types','event_id'=>$event_id], admin_url('admin.php')) ); ?>#pbs-tt-form" class="button button-primary">+ Add Ticket Type</a>
  </div>

  <table class="widefat striped pbs-admin-table">
    <thead><tr><th>Name</th><th>Event</th><th>Price</th><th>Capacity</th><th>Sold</th><th>Type</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>
    <?php if ( empty($ticket_types) ) : ?>
      <tr><td colspan="8" style="text-align:center;padding:24px;color:#888;">No ticket types found. Add one using the form →</td></tr>
    <?php else : ?>
      <?php foreach ( $ticket_types as $tt ) :
        $cap_pct = $tt['capacity'] > 0 ? round( $tt['sold'] / $tt['capacity'] * 100 ) : 0;
      ?>
      <tr style="<?php echo ! $tt['active'] ? 'opacity:.55;' : ''; ?>">
        <td>
          <strong><?php echo esc_html($tt['name']); ?></strong>
          <?php if ($tt['description']) echo '<br><small style="color:#888;">' . esc_html(substr($tt['description'],0,60)) . '</small>'; ?>
        </td>
        <td><?php echo esc_html( get_the_title((int)$tt['event_id']) ?: 'Event #'.$tt['event_id'] ); ?></td>
        <td><?php echo $tt['is_donation'] ? '<em>Donation</em>' : '$' . number_format((float)$tt['price'],2); ?></td>
        <td><?php echo $tt['capacity'] > 0 ? esc_html($tt['capacity']) : '∞'; ?></td>
        <td>
          <?php echo esc_html($tt['sold']); ?>
          <?php if ($tt['capacity'] > 0) echo '<br><small>' . $cap_pct . '%</small>'; ?>
        </td>
        <td><?php echo $tt['is_donation'] ? '💝 Donation' : '🎟 Ticket'; ?></td>
        <td>
          <form method="post" style="display:inline;">
            <?php wp_nonce_field('pbs_ticket_types'); ?>
            <input type="hidden" name="pbs_tt_action" value="toggle">
            <input type="hidden" name="tt_id" value="<?php echo esc_attr($tt['id']); ?>">
            <button type="submit" class="button button-small" style="color:<?php echo $tt['active'] ? '#4caf50' : '#aaa'; ?>">
              <?php echo $tt['active'] ? '✅ Active' : '⏸ Inactive'; ?>
            </button>
          </form>
        </td>
        <td>
          <a href="<?php echo esc_url( add_query_arg(['page'=>'pbs-ticket-types','edit'=>$tt['id'],'event_id'=>$tt['event_id']], admin_url('admin.php')) . '#pbs-tt-form' ); ?>" class="button button-small">Edit</a>
          <form method="post" style="display:inline;" onsubmit="return confirm('Delete this ticket type?');">
            <?php wp_nonce_field('pbs_ticket_types'); ?>
            <input type="hidden" name="pbs_tt_action" value="delete">
            <input type="hidden" name="tt_id" value="<?php echo esc_attr($tt['id']); ?>">
            <button type="submit" class="button button-small" style="color:#c62828;">Delete</button>
          </form>
        </td>
      </tr>
      <?php endforeach; ?>
    <?php endif; ?>
    </tbody>
  </table>
</div>

<!-- ── Add / Edit Form ── -->
<div id="pbs-tt-form" style="background:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;">
  <h3 style="margin-top:0;"><?php echo $edit_tt ? '✏️ Edit Ticket Type' : '➕ Add Ticket Type'; ?></h3>
  <form method="post">
    <?php wp_nonce_field('pbs_ticket_types'); ?>
    <input type="hidden" name="pbs_tt_action" value="<?php echo $edit_tt ? 'save' : 'add'; ?>">
    <?php if ($edit_tt) : ?>
    <input type="hidden" name="tt_id" value="<?php echo esc_attr($edit_tt['id']); ?>">
    <?php endif; ?>

    <table class="form-table" style="margin:0;">
      <tr>
        <th style="width:120px;padding:6px 0;">Event Post ID</th>
        <td style="padding:4px 0;">
          <input type="number" name="tt_event_id" value="<?php echo esc_attr($edit_tt['event_id'] ?? $event_id); ?>" class="small-text" required min="1">
          <p class="description">The WordPress post/page ID for this event.</p>
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Name</th>
        <td style="padding:4px 0;">
          <input type="text" name="tt_name" value="<?php echo esc_attr($edit_tt['name'] ?? ''); ?>" class="regular-text" required placeholder="e.g. General Admission">
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Description</th>
        <td style="padding:4px 0;">
          <textarea name="tt_description" class="regular-text" rows="2" placeholder="Optional details shown at checkout"><?php echo esc_textarea($edit_tt['description'] ?? ''); ?></textarea>
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Type</th>
        <td style="padding:4px 0;">
          <label><input type="checkbox" name="tt_is_donation" value="1" <?php checked(!empty($edit_tt['is_donation'])); ?>> Donation (user sets amount)</label>
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Price ($)</th>
        <td style="padding:4px 0;">
          <input type="number" name="tt_price" value="<?php echo esc_attr($edit_tt['price'] ?? '0.00'); ?>" step="0.01" min="0" class="small-text">
          <p class="description">Set to 0 for free. Ignored if donation type.</p>
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Capacity</th>
        <td style="padding:4px 0;">
          <input type="number" name="tt_capacity" value="<?php echo esc_attr($edit_tt['capacity'] ?? '0'); ?>" min="0" class="small-text">
          <p class="description">0 = unlimited.</p>
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Sale Start</th>
        <td style="padding:4px 0;">
          <input type="datetime-local" name="tt_start" value="<?php echo esc_attr($edit_tt['ticket_start'] ? date('Y-m-d\TH:i', strtotime($edit_tt['ticket_start'])) : ''); ?>">
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Sale End</th>
        <td style="padding:4px 0;">
          <input type="datetime-local" name="tt_end" value="<?php echo esc_attr($edit_tt['ticket_end'] ? date('Y-m-d\TH:i', strtotime($edit_tt['ticket_end'])) : ''); ?>">
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Sort Order</th>
        <td style="padding:4px 0;">
          <input type="number" name="tt_sort_order" value="<?php echo esc_attr($edit_tt['sort_order'] ?? '0'); ?>" min="0" class="small-text">
        </td>
      </tr>
      <tr>
        <th style="padding:6px 0;">Active</th>
        <td style="padding:4px 0;">
          <label><input type="checkbox" name="tt_active" value="1" <?php checked(isset($edit_tt) ? (bool)$edit_tt['active'] : true); ?>> Visible at checkout</label>
        </td>
      </tr>
    </table>
    <div style="margin-top:16px;display:flex;gap:8px;">
      <?php submit_button( $edit_tt ? 'Save Changes' : 'Add Ticket Type', 'primary', '', false ); ?>
      <?php if ($edit_tt) : ?>
        <a href="<?php echo esc_url( add_query_arg(['page'=>'pbs-ticket-types','event_id'=>$event_id], admin_url('admin.php')) ); ?>" class="button">Cancel</a>
      <?php endif; ?>
    </div>
  </form>
</div>

</div><!-- grid -->

<div style="margin-top:24px;padding:12px 16px;background:#f8f9fa;border-radius:6px;font-size:12px;color:#666;">
  <strong>Shortcodes:</strong>
  <code>[pbs_tickets event_id="<em>POST_ID</em>"]</code> — ticket checkout widget &nbsp;|&nbsp;
  <code>[pbs_donate event_id="<em>POST_ID</em>" goal="5000"]</code> — donation widget
</div>
</div>
