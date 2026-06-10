<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="tribe-tickets pbs-donate-widget" id="pbs-donate-<?php echo esc_attr( $event_id ); ?>" data-event="<?php echo esc_attr( $event_id ); ?>">
  <h3 class="tribe-tickets__title"><?php echo esc_html( $atts['label'] ); ?></h3>

  <?php if ( $goal > 0 ) :
    $pct = $goal > 0 ? min( 100, round( ( $total_donated / $goal ) * 100 ) ) : 0;
  ?>
  <div class="pbs-goal-bar">
    <div class="pbs-goal-progress" style="width:<?php echo $pct; ?>%"></div>
  </div>
  <p class="pbs-goal-label">
    <strong>$<?php echo number_format( $total_donated, 0 ); ?></strong> raised of
    <strong>$<?php echo number_format( $goal, 0 ); ?></strong> goal
  </p>
  <?php endif; ?>

  <form class="pbs-checkout-form pbs-donate-form" id="pbs-donate-form-<?php echo esc_attr( $event_id ); ?>">
    <?php wp_nonce_field( 'pbs_ec_nonce', 'pbs_nonce' ); ?>
    <input type="hidden" name="event_id" value="<?php echo esc_attr( $event_id ); ?>">
    <input type="hidden" name="ticket_type" value="">
    <input type="hidden" name="is_donation" value="1">
    <input type="hidden" name="quantity" value="1">

    <!-- Preset amounts -->
    <div class="pbs-amount-grid">
      <?php foreach ( $amounts as $amt ) : ?>
      <button type="button" class="tribe-tickets__ticket-item pbs-amount-btn" data-amount="<?php echo esc_attr( $amt ); ?>">
        $<?php echo esc_html( $amt ); ?>
      </button>
      <?php endforeach; ?>
      <button type="button" class="tribe-tickets__ticket-item pbs-amount-btn pbs-amount-custom" data-amount="custom">
        Other
      </button>
    </div>

    <div class="pbs-custom-amount-wrap" style="display:none">
      <label>Enter amount ($)</label>
      <input type="number" class="tribe-tickets__input pbs-custom-amount-input" placeholder="e.g. 75" min="1" step="1">
    </div>

    <div class="pbs-order-summary pbs-donate-summary" style="display:none">
      <div class="pbs-total-line">
        <span>Donation Amount</span>
        <strong class="pbs-order-total">$0.00</strong>
        <input type="hidden" name="amount" class="pbs-amount-input" value="0">
      </div>

      <div class="pbs-attendee-fields">
        <input type="text" name="name" placeholder="Your Name *" required class="tribe-tickets__input">
        <input type="email" name="email" placeholder="Email Address *" required class="tribe-tickets__input">
        <textarea name="message" placeholder="Optional note or dedication" class="tribe-tickets__input" rows="2"></textarea>
      </div>

      <div class="pbs-gateway-select">
        <h4>Pay With</h4>
        <div class="pbs-gateway-tabs">
          <?php foreach ( $gateways as $gw ) : ?>
          <button type="button" class="pbs-gateway-tab <?php echo $gw === $gateways[0] ? 'active' : ''; ?>"
                  data-gateway="<?php echo esc_attr( $gw ); ?>">
            <?php echo esc_html( ucfirst( $gw ) ); ?>
          </button>
          <?php endforeach; ?>
        </div>
        <input type="hidden" name="gateway" class="pbs-gateway-input" value="<?php echo esc_attr( $gateways[0] ?? '' ); ?>">
        <div class="pbs-payment-panel" data-panel="stripe"<?php echo ( $gateways[0] ?? '' ) !== 'stripe' ? ' style="display:none"' : ''; ?>>
          <div id="pbs-stripe-donate-<?php echo $event_id; ?>" class="pbs-stripe-card-element"></div>
        </div>
        <div class="pbs-payment-panel" data-panel="square" style="display:none">
          <div id="pbs-square-donate-<?php echo $event_id; ?>"></div>
        </div>
        <div class="pbs-payment-panel" data-panel="paypal" style="display:none">
          <div id="pbs-paypal-donate-<?php echo $event_id; ?>"></div>
        </div>
      </div>

      <button type="submit" class="tribe-tickets__buy pbs-submit-btn">Donate Now</button>
      <div class="pbs-spinner" style="display:none;">Processing...</div>
      <div class="pbs-error-msg" role="alert"></div>
      <p class="pbs-tax-note">Psi Beta Sigma 1914 is a registered 501(c)(3) nonprofit. Your donation may be tax-deductible.</p>
    </div>
  </form>
</div>
