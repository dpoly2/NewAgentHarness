<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="tribe-tickets pbs-ticket-widget" id="pbs-tickets-<?php echo esc_attr($event_id); ?>" data-event="<?php echo esc_attr($event_id); ?>">

  <?php if ( $atts['show_title'] && $event ) : ?>
    <h3 class="tribe-tickets__title">Tickets</h3>
  <?php endif; ?>

  <?php if ( empty($tickets) ) : ?>
    <p class="tribe-tickets__notice">Ticket sales are not yet open. Check back soon.</p>
  <?php else : ?>
  <form class="pbs-checkout-form" id="pbs-form-<?php echo esc_attr($event_id); ?>">
    <?php wp_nonce_field('pbs_ec_nonce','pbs_nonce'); ?>
    <input type="hidden" name="event_id" value="<?php echo esc_attr($event_id); ?>">

    <!-- Ticket List -->
    <div class="tribe-tickets__tickets-list pbs-ticket-list">
      <?php foreach ($tickets as $ticket) :
        $available = max(0, $ticket['capacity'] - $ticket['sold']);
        $sold_out  = ($ticket['capacity'] > 0 && $available === 0);
        $is_free   = ((float)$ticket['price'] === 0.00 && !$ticket['is_donation']);
      ?>
      <div class="tribe-tickets__ticket-item pbs-ticket-item <?php echo $sold_out ? 'sold-out' : ''; ?>"
           data-ticket-id="<?php echo esc_attr($ticket['id']); ?>"
           data-price="<?php echo esc_attr($ticket['price']); ?>"
           data-name="<?php echo esc_attr($ticket['name']); ?>"
           data-is-donation="<?php echo $ticket['is_donation'] ? '1' : '0'; ?>">
        <div class="tribe-tickets__ticket-item-details">
          <h4 class="tribe-tickets__ticket-item-title"><?php echo esc_html($ticket['name']); ?></h4>
          <?php if ($ticket['description']) : ?>
            <p class="tribe-tickets__ticket-item-description"><?php echo esc_html($ticket['description']); ?></p>
          <?php endif; ?>
          <?php if ($ticket['ticket_end']) : ?>
            <span class="pbs-sale-ends">Sale ends <?php echo date('M j', strtotime($ticket['ticket_end'])); ?></span>
          <?php endif; ?>
          <?php if ($ticket['capacity'] > 0) : ?>
            <span class="pbs-ticket-avail <?php echo ($available < 10) ? 'pbs-low-stock' : ''; ?>">
              <?php echo ($available < 10) ? "Only {$available} left!" : "{$available} available"; ?>
            </span>
          <?php endif; ?>
        </div>
        <div class="tribe-tickets__ticket-item-price-wrapper">
          <span class="tribe-tickets__ticket-item-price">
            <?php echo $ticket['price'] > 0 ? '$' . number_format($ticket['price'], 2) : ($ticket['is_donation'] ? 'You choose' : 'Free'); ?>
          </span>
          <?php if (!$sold_out) : ?>
            <?php if (!$ticket['is_donation']) : ?>
            <div class="tribe-tickets__ticket-item-quantity">
              <button type="button" class="pbs-qty-btn pbs-qty-minus" aria-label="Decrease">−</button>
              <input type="number" class="pbs-qty-input" name="qty_<?php echo $ticket['id']; ?>"
                     value="0" min="0" max="<?php echo $available ?: 20; ?>"
                     data-ticket-id="<?php echo $ticket['id']; ?>">
              <button type="button" class="pbs-qty-btn pbs-qty-plus" aria-label="Increase">+</button>
            </div>
            <?php endif; ?>
          <?php else : ?>
            <span class="tribe-tickets__notice--sold-out">Sold Out</span>
            <button type="button" class="pbs-waitlist-btn tribe-tickets__buy"
                    data-event="<?php echo esc_attr($event_id); ?>"
                    data-ticket="<?php echo esc_attr($ticket['name']); ?>">
              Join Waitlist
            </button>
          <?php endif; ?>
        </div>
      </div>
      <?php endforeach; ?>
    </div><!-- /.pbs-ticket-list -->

    <!-- Order Summary + Checkout (hidden until qty > 0) -->
    <div class="tribe-tickets__footer pbs-order-summary" style="display:none;">

      <!-- Promo Code -->
      <div class="pbs-promo-wrap">
        <div class="pbs-promo-row">
          <input type="text" class="pbs-promo-code-input tribe-tickets__input" placeholder="Promo code">
          <button type="button" class="pbs-promo-apply-btn">Apply</button>
        </div>
        <div class="pbs-promo-msg" style="display:none;"></div>
        <input type="hidden" name="promo_code" class="pbs-promo-code-val" value="">
        <input type="hidden" name="discount_amount" class="pbs-discount-amount" value="0">
      </div>

      <!-- Totals -->
      <div class="pbs-total-lines">
        <div class="pbs-total-line pbs-subtotal-line">
          <span>Subtotal</span><span class="pbs-subtotal-display">$0.00</span>
        </div>
        <div class="pbs-total-line pbs-discount-line" style="display:none;">
          <span>Discount</span><span class="pbs-discount-display" style="color:#2e7d32;">−$0.00</span>
        </div>
        <div class="pbs-total-line pbs-grand-total-line">
          <span><strong>Total</strong></span>
          <strong class="pbs-order-total">$0.00</strong>
        </div>
        <input type="hidden" name="amount" class="pbs-amount-input" value="0">
        <input type="hidden" name="ticket_type" class="pbs-ticket-type-input" value="">
        <input type="hidden" name="quantity" class="pbs-quantity-input" value="0">
      </div>

      <!-- Attendee Info -->
      <div class="pbs-attendee-fields">
        <h4>Your Information</h4>
        <input type="text"  name="name"  placeholder="Full Name *"      required class="tribe-tickets__input">
        <input type="email" name="email" placeholder="Email Address *"  required class="tribe-tickets__input">
        <input type="tel"   name="phone" placeholder="Phone Number"              class="tribe-tickets__input">
      </div>

      <!-- Custom Questions -->
      <?php echo PBS_Custom_Questions::render_fields($event_id); ?>

      <!-- Payment Gateways -->
      <?php if (!empty($gateways)) : ?>
      <div class="pbs-gateway-select">
        <h4>Pay With</h4>
        <div class="pbs-gateway-tabs">
          <?php foreach ($gateways as $gw) : ?>
          <button type="button" class="pbs-gateway-tab <?php echo $gw === $gateways[0] ? 'active' : ''; ?>"
                  data-gateway="<?php echo esc_attr($gw); ?>">
            <?php echo esc_html(ucfirst($gw)); ?>
          </button>
          <?php endforeach; ?>
        </div>
        <input type="hidden" name="gateway" class="pbs-gateway-input" value="<?php echo esc_attr($gateways[0] ?? ''); ?>">

        <div class="pbs-payment-panel" data-panel="stripe" <?php echo ((!in_array('stripe',$gateways))||($gateways[0]??'')!=='stripe')?'style="display:none"':''; ?>>
          <div id="pbs-stripe-card-<?php echo $event_id; ?>" class="pbs-stripe-card-element"></div>
          <div id="pbs-stripe-errors-<?php echo $event_id; ?>" class="pbs-card-errors" role="alert"></div>
        </div>
        <div class="pbs-payment-panel" data-panel="square" style="display:none">
          <div id="pbs-square-card-<?php echo $event_id; ?>"></div>
        </div>
        <div class="pbs-payment-panel" data-panel="paypal" style="display:none">
          <div id="pbs-paypal-btn-<?php echo $event_id; ?>"></div>
        </div>
      </div>
      <?php else : ?>
        <p class="pbs-notice pbs-no-gateways">&#x26A0;&#xFE0F; No payment methods configured yet. Visit PBS Commerce → Settings to add Stripe, Square, or PayPal credentials.</p>
      <?php endif; ?>

      <div class="pbs-submit-wrap">
        <button type="submit" class="tribe-tickets__buy pbs-submit-btn">Complete Purchase</button>
        <div class="pbs-spinner" style="display:none;">Processing...</div>
        <div class="pbs-error-msg" role="alert"></div>
      </div>

      <p class="pbs-secure-note">🔒 Secure checkout. Your information is protected.</p>
    </div><!-- /.pbs-order-summary -->
  </form>
  <?php endif; ?>

</div><!-- /.pbs-ticket-widget -->

<!-- Waitlist Modal -->
<div class="pbs-modal-overlay" id="pbs-waitlist-modal-<?php echo $event_id; ?>" style="display:none;">
  <div class="pbs-modal">
    <button class="pbs-modal-close" type="button">&times;</button>
    <h3>Join the Waitlist</h3>
    <p>We'll email you immediately if a spot opens up.</p>
    <input type="text"  class="pbs-wl-name tribe-tickets__input"  placeholder="Your Name *">
    <input type="email" class="pbs-wl-email tribe-tickets__input" placeholder="Email Address *">
    <input type="tel"   class="pbs-wl-phone tribe-tickets__input" placeholder="Phone (optional)">
    <input type="hidden" class="pbs-wl-ticket" value="">
    <button class="tribe-tickets__buy pbs-wl-submit-btn" data-event="<?php echo esc_attr($event_id); ?>">Join Waitlist</button>
    <div class="pbs-wl-msg"></div>
  </div>
</div>
