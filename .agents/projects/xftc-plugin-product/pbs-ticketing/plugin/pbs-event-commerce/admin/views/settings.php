<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="wrap pbs-settings-wrap">
<h1 style="margin-bottom:4px;">PBS Commerce — Settings</h1>
<p style="color:#666;margin-top:0;">Configure payment gateways, email notifications, and checkout behavior.</p>

<style>
.pbs-settings-wrap { max-width: 900px; }
.pbs-gateway-card {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-bottom: 20px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.pbs-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #eee;
    background: #fafafa;
}
.pbs-card-header-left { display: flex; align-items: center; gap: 12px; }
.pbs-card-title { font-size: 15px; font-weight: 600; margin: 0; }
.pbs-card-body { padding: 20px; }
.pbs-card-body table { width: 100%; border-collapse: collapse; }
.pbs-card-body table tr th { width: 200px; padding: 10px 0; font-weight: 500; color: #444; vertical-align: middle; }
.pbs-card-body table tr td { padding: 8px 0; vertical-align: middle; }
.pbs-card-body input.regular-text { width: 360px; }
.pbs-card-body select { min-width: 160px; }

/* Toggle switch */
.pbs-toggle-wrap { display: flex; align-items: center; gap: 10px; }
.pbs-toggle { position: relative; display: inline-block; width: 46px; height: 26px; }
.pbs-toggle input { opacity: 0; width: 0; height: 0; }
.pbs-toggle-slider {
    position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
    background-color: #ccc; transition: .3s; border-radius: 26px;
}
.pbs-toggle-slider:before {
    position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px;
    background-color: white; transition: .3s; border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.pbs-toggle input:checked + .pbs-toggle-slider { background-color: #2196F3; }
.pbs-toggle input:checked + .pbs-toggle-slider:before { transform: translateX(20px); }
.pbs-toggle-label { font-size: 13px; font-weight: 500; color: #444; }
.pbs-enabled-badge { font-size: 11px; padding: 3px 8px; border-radius: 12px; font-weight: 600; }
.pbs-enabled-badge.on  { background: #e8f5e9; color: #2e7d32; }
.pbs-enabled-badge.off { background: #fafafa; color: #999; border: 1px solid #ddd; }

/* Status indicator */
.pbs-status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.pbs-status-dot.connected    { background: #4caf50; }
.pbs-status-dot.disconnected { background: #e0e0e0; }
.pbs-status-dot.error        { background: #f44336; }
.pbs-status-text { font-size: 12px; color: #888; }

/* OAuth button */
.pbs-oauth-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 5px; border: 1px solid #ddd;
    background: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
    text-decoration: none; color: #333; transition: background .2s;
}
.pbs-oauth-btn:hover { background: #f5f5f5; }
.pbs-oauth-btn.stripe-btn  { border-color: #635bff; color: #635bff; }
.pbs-oauth-btn.square-btn  { border-color: #333; color: #333; }
.pbs-oauth-btn.paypal-btn  { border-color: #003087; color: #003087; }

/* Key reveal toggle */
.pbs-key-wrap { display: flex; align-items: center; gap: 8px; }
.pbs-reveal-btn { background: none; border: none; cursor: pointer; color: #888; padding: 4px; font-size: 12px; }
.pbs-reveal-btn:hover { color: #333; }
.pbs-key-set-indicator { font-size: 12px; color: #4caf50; font-weight: 500; }

/* Section cards */
.pbs-section-card {
    background: #fff; border: 1px solid #ddd; border-radius: 8px;
    margin-bottom: 20px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.pbs-section-header {
    padding: 14px 20px; border-bottom: 1px solid #eee; background: #fafafa;
    font-size: 15px; font-weight: 600;
}
.pbs-section-body { padding: 20px; }

.pbs-save-bar {
    position: sticky; bottom: 0; background: #fff; border-top: 1px solid #e0e0e0;
    padding: 14px 20px; display: flex; gap: 12px; align-items: center; z-index: 10;
}
</style>

<form method="post" action="options.php" id="pbs-settings-form">
<?php settings_fields( 'pbs_commerce_settings' ); ?>

<?php
// Helper: check if a key is configured
function pbs_key_set( $option ) {
    $val = get_option( $option, '' );
    return ! empty( trim( $val ) );
}
function pbs_enabled( $option ) {
    return (bool) get_option( $option, 0 );
}
?>

<!-- ═══════════════════════════════════════════════════════ STRIPE ═══ -->
<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">💳</span>
      <span class="pbs-card-title">Stripe</span>
      <span class="pbs-status-dot <?php echo (pbs_key_set('pbs_stripe_secret_key') && pbs_enabled('pbs_stripe_enabled')) ? 'connected' : (pbs_key_set('pbs_stripe_secret_key') ? 'disconnected' : 'disconnected'); ?>"></span>
      <span class="pbs-status-text">
        <?php if (pbs_key_set('pbs_stripe_secret_key') && pbs_enabled('pbs_stripe_enabled')): ?>Active<?php
        elseif (pbs_key_set('pbs_stripe_secret_key')): ?>Configured (disabled)<?php
        else: ?>Not configured<?php endif; ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_stripe_enabled" value="1" <?php checked(get_option('pbs_stripe_enabled',0), 1); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo pbs_enabled('pbs_stripe_enabled') ? 'Enabled' : 'Disabled'; ?></span>
      <span class="pbs-enabled-badge <?php echo pbs_enabled('pbs_stripe_enabled') ? 'on' : 'off'; ?>">
        <?php echo pbs_enabled('pbs_stripe_enabled') ? 'ON' : 'OFF'; ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept credit/debit cards via Stripe. 
      <a href="https://dashboard.stripe.com/apikeys" target="_blank">Get API keys ↗</a> &nbsp;|&nbsp;
      <a href="https://dashboard.stripe.com/test/apikeys" target="_blank">Test keys ↗</a>
    </p>

    <!-- OAuth Connect Button -->
    <div style="margin-bottom:16px;">
      <?php
      $stripe_connected = pbs_key_set('pbs_stripe_secret_key');
      $stripe_oauth_url = 'https://connect.stripe.com/oauth/authorize?response_type=code&client_id=' . urlencode(get_option('pbs_stripe_connect_client_id','')) . '&scope=read_write&redirect_uri=' . urlencode(admin_url('admin.php?page=pbs-commerce-settings&stripe_oauth=1'));
      ?>
      <?php if ($stripe_connected): ?>
        <span style="color:#4caf50;font-weight:600;">✅ API Keys Configured</span> &nbsp;
        <button type="button" class="pbs-oauth-btn stripe-btn" onclick="if(confirm('Remove Stripe keys?')){document.getElementById('pbs_stripe_secret_key').value='';document.getElementById('pbs_stripe_pub_key').value='';document.getElementById('pbs-settings-form').submit();}">Disconnect</button>
      <?php else: ?>
        <a href="<?php echo esc_url($stripe_oauth_url); ?>" class="pbs-oauth-btn stripe-btn" <?php echo empty(get_option('pbs_stripe_connect_client_id')) ? 'style="opacity:.5;pointer-events:none;"' : ''; ?>>
          🔗 Connect with Stripe OAuth
        </a>
        <span style="margin-left:8px;color:#888;font-size:12px;">— or enter keys manually below</span>
      <?php endif; ?>
    </div>

    <table>
      <tr>
        <th>Publishable Key</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="text" id="pbs_stripe_pub_key" name="pbs_stripe_publishable_key"
                   value="<?php echo esc_attr(get_option('pbs_stripe_publishable_key','')); ?>"
                   class="regular-text" placeholder="pk_live_..." autocomplete="off">
            <?php if (pbs_key_set('pbs_stripe_publishable_key')): ?>
              <span class="pbs-key-set-indicator">✓ Set</span>
            <?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Secret Key</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" id="pbs_stripe_secret_key" name="pbs_stripe_secret_key"
                   value="<?php echo esc_attr(get_option('pbs_stripe_secret_key','')); ?>"
                   class="regular-text" placeholder="sk_live_..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=document.getElementById('pbs_stripe_secret_key');f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if (pbs_key_set('pbs_stripe_secret_key')): ?>
              <span class="pbs-key-set-indicator">✓ Set</span>
            <?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Webhook Secret</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" name="pbs_stripe_webhook_secret"
                   value="<?php echo esc_attr(get_option('pbs_stripe_webhook_secret','')); ?>"
                   class="regular-text" placeholder="whsec_..." autocomplete="new-password">
            <?php if (pbs_key_set('pbs_stripe_webhook_secret')): ?>
              <span class="pbs-key-set-indicator">✓ Set</span>
            <?php endif; ?>
          </div>
          <p class="description">Webhook URL: <code><?php echo esc_url(rest_url('pbs-ec/v1/stripe-webhook')); ?></code></p>
        </td>
      </tr>
      <tr>
        <th>Connect Client ID <span style="font-weight:400;color:#888;">(OAuth)</span></th>
        <td>
          <input type="text" name="pbs_stripe_connect_client_id"
                 value="<?php echo esc_attr(get_option('pbs_stripe_connect_client_id','')); ?>"
                 class="regular-text" placeholder="ca_...">
          <p class="description">From Stripe Dashboard → Connect → Settings. Enables one-click OAuth connect.</p>
        </td>
      </tr>
      <tr>
        <th>Mode</th>
        <td>
          <select name="pbs_stripe_mode">
            <option value="test" <?php selected(get_option('pbs_stripe_mode','test'),'test'); ?>>🧪 Test / Sandbox</option>
            <option value="live" <?php selected(get_option('pbs_stripe_mode','test'),'live'); ?>>🟢 Live</option>
          </select>
        </td>
      </tr>
    </table>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════ SQUARE ═══ -->
<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">⬛</span>
      <span class="pbs-card-title">Square</span>
      <span class="pbs-status-dot <?php echo (pbs_key_set('pbs_square_access_token') && pbs_enabled('pbs_square_enabled')) ? 'connected' : 'disconnected'; ?>"></span>
      <span class="pbs-status-text">
        <?php if (pbs_key_set('pbs_square_access_token') && pbs_enabled('pbs_square_enabled')): ?>Active<?php
        elseif (pbs_key_set('pbs_square_access_token')): ?>Configured (disabled)<?php
        else: ?>Not configured<?php endif; ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_square_enabled" value="1" <?php checked(get_option('pbs_square_enabled',0), 1); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo pbs_enabled('pbs_square_enabled') ? 'Enabled' : 'Disabled'; ?></span>
      <span class="pbs-enabled-badge <?php echo pbs_enabled('pbs_square_enabled') ? 'on' : 'off'; ?>">
        <?php echo pbs_enabled('pbs_square_enabled') ? 'ON' : 'OFF'; ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept cards via Square's Web Payments SDK. 
      <a href="https://developer.squareup.com/apps" target="_blank">Square Developer Dashboard ↗</a>
    </p>

    <?php
    $sq_oauth_url = 'https://connect.squareup.com/oauth2/authorize?client_id=' . urlencode(get_option('pbs_square_app_id','')) . '&scope=PAYMENTS_WRITE+PAYMENTS_READ+ORDERS_WRITE&session=false&state=pbs_square_oauth&redirect_uri=' . urlencode(admin_url('admin.php?page=pbs-commerce-settings&square_oauth=1'));
    $sq_connected = pbs_key_set('pbs_square_access_token');
    ?>
    <div style="margin-bottom:16px;">
      <?php if ($sq_connected): ?>
        <span style="color:#4caf50;font-weight:600;">✅ Access Token Configured</span> &nbsp;
        <button type="button" class="pbs-oauth-btn square-btn" onclick="if(confirm('Remove Square credentials?')){document.getElementsByName('pbs_square_access_token')[0].value='';document.getElementById('pbs-settings-form').submit();}">Disconnect</button>
      <?php else: ?>
        <a href="<?php echo esc_url($sq_oauth_url); ?>" class="pbs-oauth-btn square-btn" <?php echo empty(get_option('pbs_square_app_id')) ? 'style="opacity:.5;pointer-events:none;" title="Enter App ID first"' : ''; ?>>
          🔗 Connect with Square OAuth
        </a>
        <span style="margin-left:8px;color:#888;font-size:12px;">— or enter access token manually below</span>
      <?php endif; ?>
    </div>

    <table>
      <tr>
        <th>App ID</th>
        <td>
          <input type="text" name="pbs_square_app_id"
                 value="<?php echo esc_attr(get_option('pbs_square_app_id','')); ?>"
                 class="regular-text" placeholder="sq0idp-...">
          <p class="description">From your Square app → Credentials tab.</p>
        </td>
      </tr>
      <tr>
        <th>Location ID</th>
        <td>
          <input type="text" name="pbs_square_location_id"
                 value="<?php echo esc_attr(get_option('pbs_square_location_id','')); ?>"
                 class="regular-text" placeholder="L...">
        </td>
      </tr>
      <tr>
        <th>Access Token</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" name="pbs_square_access_token"
                   value="<?php echo esc_attr(get_option('pbs_square_access_token','')); ?>"
                   class="regular-text" placeholder="EAAAl..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=this.previousElementSibling;f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if ($sq_connected): ?><span class="pbs-key-set-indicator">✓ Set</span><?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Environment</th>
        <td>
          <select name="pbs_square_env">
            <option value="sandbox"    <?php selected(get_option('pbs_square_env','sandbox'),'sandbox'); ?>>🧪 Sandbox</option>
            <option value="production" <?php selected(get_option('pbs_square_env','sandbox'),'production'); ?>>🟢 Production</option>
          </select>
        </td>
      </tr>
    </table>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════ PAYPAL ═══ -->
<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">🅿️</span>
      <span class="pbs-card-title">PayPal</span>
      <span class="pbs-status-dot <?php echo (pbs_key_set('pbs_paypal_secret') && pbs_enabled('pbs_paypal_enabled')) ? 'connected' : 'disconnected'; ?>"></span>
      <span class="pbs-status-text">
        <?php if (pbs_key_set('pbs_paypal_secret') && pbs_enabled('pbs_paypal_enabled')): ?>Active<?php
        elseif (pbs_key_set('pbs_paypal_secret')): ?>Configured (disabled)<?php
        else: ?>Not configured<?php endif; ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_paypal_enabled" value="1" <?php checked(get_option('pbs_paypal_enabled',0), 1); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo pbs_enabled('pbs_paypal_enabled') ? 'Enabled' : 'Disabled'; ?></span>
      <span class="pbs-enabled-badge <?php echo pbs_enabled('pbs_paypal_enabled') ? 'on' : 'off'; ?>">
        <?php echo pbs_enabled('pbs_paypal_enabled') ? 'ON' : 'OFF'; ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept PayPal & Venmo via PayPal JS SDK. 
      <a href="https://developer.paypal.com/dashboard/applications" target="_blank">PayPal Developer Dashboard ↗</a>
    </p>

    <?php
    $pp_connected = pbs_key_set('pbs_paypal_secret');
    $pp_oauth_url = 'https://www.paypal.com/signin/authorize?client_id=' . urlencode(get_option('pbs_paypal_client_id','')) . '&response_type=code&scope=openid+email&redirect_uri=' . urlencode(admin_url('admin.php?page=pbs-commerce-settings&paypal_oauth=1'));
    ?>
    <div style="margin-bottom:16px;">
      <?php if ($pp_connected): ?>
        <span style="color:#4caf50;font-weight:600;">✅ Client Secret Configured</span> &nbsp;
        <button type="button" class="pbs-oauth-btn paypal-btn" onclick="if(confirm('Remove PayPal credentials?')){document.getElementsByName('pbs_paypal_secret')[0].value='';document.getElementById('pbs-settings-form').submit();}">Disconnect</button>
      <?php else: ?>
        <a href="<?php echo esc_url($pp_oauth_url); ?>" class="pbs-oauth-btn paypal-btn" <?php echo empty(get_option('pbs_paypal_client_id')) ? 'style="opacity:.5;pointer-events:none;" title="Enter Client ID first"' : ''; ?>>
          🔗 Connect with PayPal OAuth
        </a>
        <span style="margin-left:8px;color:#888;font-size:12px;">— or enter credentials manually below</span>
      <?php endif; ?>
    </div>

    <table>
      <tr>
        <th>Client ID</th>
        <td>
          <input type="text" name="pbs_paypal_client_id"
                 value="<?php echo esc_attr(get_option('pbs_paypal_client_id','')); ?>"
                 class="regular-text" placeholder="AY...">
          <?php if (pbs_key_set('pbs_paypal_client_id')): ?><span class="pbs-key-set-indicator">✓ Set</span><?php endif; ?>
        </td>
      </tr>
      <tr>
        <th>Secret</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" name="pbs_paypal_secret"
                   value="<?php echo esc_attr(get_option('pbs_paypal_secret','')); ?>"
                   class="regular-text" placeholder="EL..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=this.previousElementSibling;f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if ($pp_connected): ?><span class="pbs-key-set-indicator">✓ Set</span><?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Mode</th>
        <td>
          <select name="pbs_paypal_mode">
            <option value="sandbox" <?php selected(get_option('pbs_paypal_mode','sandbox'),'sandbox'); ?>>🧪 Sandbox</option>
            <option value="live"    <?php selected(get_option('pbs_paypal_mode','sandbox'),'live'); ?>>🟢 Live</option>
          </select>
        </td>
      </tr>
      <tr>
        <th>Enable Venmo</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_paypal_venmo" value="1" <?php checked(get_option('pbs_paypal_venmo',0),1); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Show Venmo button (US only)</span>
        </td>
      </tr>
    </table>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════ EMAIL SETTINGS ═══ -->
<div class="pbs-section-card">
  <div class="pbs-section-header">📧 Email Notifications</div>
  <div class="pbs-section-body">
    <table class="form-table" style="margin:0;">
      <tr>
        <th style="width:200px;">From Name</th>
        <td><input type="text" name="pbs_email_from_name" value="<?php echo esc_attr(get_option('pbs_email_from_name','Psi Beta Sigma 1914')); ?>" class="regular-text"></td>
      </tr>
      <tr>
        <th>From Email</th>
        <td><input type="email" name="pbs_email_from" value="<?php echo esc_attr(get_option('pbs_email_from','secretary@psibetasigma1914.org')); ?>" class="regular-text"></td>
      </tr>
      <tr>
        <th>BCC (all orders)</th>
        <td>
          <input type="email" name="pbs_email_bcc" value="<?php echo esc_attr(get_option('pbs_email_bcc','')); ?>" class="regular-text" placeholder="treasurer@psibetasigma1914.org">
          <p class="description">Blind copy every confirmation to this address.</p>
        </td>
      </tr>
      <tr>
        <th>Treasurer Email</th>
        <td>
          <input type="email" name="pbs_treasurer_email" value="<?php echo esc_attr(get_option('pbs_treasurer_email','treasurer@psibetasigma1914.org')); ?>" class="regular-text">
          <p class="description">Receives a notification for every new order.</p>
        </td>
      </tr>
      <tr>
        <th>Send Event Reminders</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_email_reminders" value="1" <?php checked(get_option('pbs_email_reminders',1),1); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Email attendees 3 days before the event with their QR ticket</span>
        </td>
      </tr>
    </table>
  </div>
</div>

<!-- ═══════════════════════════════════════════════ CHECKOUT SETTINGS ═══ -->
<div class="pbs-section-card">
  <div class="pbs-section-header">🛒 Checkout Behavior</div>
  <div class="pbs-section-body">
    <table class="form-table" style="margin:0;">
      <tr>
        <th style="width:200px;">Cover Processing Fees</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_donor_covers_fees" value="1" <?php checked(get_option('pbs_donor_covers_fees',0),1); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Show "Cover the processing fee?" checkbox at checkout (Zeffy model)</span>
        </td>
      </tr>
      <tr>
        <th>Tax-Deductible Receipts</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_tax_receipts" value="1" <?php checked(get_option('pbs_tax_receipts',1),1); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Include tax-deductible language in donation confirmation emails</span>
        </td>
      </tr>
      <tr>
        <th>Max Tickets Per Order</th>
        <td>
          <input type="number" name="pbs_max_tickets" value="<?php echo esc_attr(get_option('pbs_max_tickets',10)); ?>" style="width:80px;" min="1" max="100">
        </td>
      </tr>
      <tr>
        <th>EIN (for receipts)</th>
        <td>
          <input type="text" name="pbs_org_ein" value="<?php echo esc_attr(get_option('pbs_org_ein','')); ?>" class="regular-text" placeholder="XX-XXXXXXX">
          <p class="description">Shown on tax-deductible donation receipts.</p>
        </td>
      </tr>
    </table>
  </div>
</div>

<!-- Sticky save bar -->
<div class="pbs-save-bar">
  <?php submit_button( 'Save Settings', 'primary', 'submit', false ); ?>
  <span id="pbs-save-status" style="font-size:13px;color:#888;"></span>
</div>

</form>

<script>
// Live toggle label update
document.querySelectorAll('.pbs-toggle input[type=checkbox]').forEach(function(cb) {
    cb.addEventListener('change', function() {
        var wrap = this.closest('.pbs-toggle-wrap');
        if (!wrap) return;
        var label = wrap.querySelector('.pbs-toggle-label');
        var badge = wrap.querySelector('.pbs-enabled-badge');
        if (label) label.textContent = this.checked ? 'Enabled' : 'Disabled';
        if (badge) {
            badge.textContent = this.checked ? 'ON' : 'OFF';
            badge.className = 'pbs-enabled-badge ' + (this.checked ? 'on' : 'off');
        }
    });
});
// Save feedback
document.getElementById('pbs-settings-form').addEventListener('submit', function() {
    document.getElementById('pbs-save-status').textContent = 'Saving…';
});
</script>
