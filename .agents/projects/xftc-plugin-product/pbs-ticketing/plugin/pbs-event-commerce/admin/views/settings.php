<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<?php
$pbs_key_set = function( $option ) {
    $value = get_option( $option, '' );
    return ! empty( trim( (string) $value ) );
};

$pbs_enabled = function( $option ) {
    return (bool) get_option( $option, 0 );
};

$square_status = class_exists( 'PBS_Square_OAuth' )
    ? PBS_Square_OAuth::connection_status()
    : [ 'connected' => false, 'expired' => false, 'merchant_id' => '', 'location_id' => '', 'expires_at' => '' ];

$stripe_status = class_exists( 'PBS_Stripe_OAuth' )
    ? PBS_Stripe_OAuth::connection_status()
    : [ 'connected' => false, 'account_name' => '', 'email' => '', 'stripe_user_id' => '', 'mode' => '' ];

$stripe_secret_key      = get_option( 'pbs_stripe_secret_key', '' );
$stripe_publishable_key = get_option( 'pbs_stripe_publishable_key', '' );
$stripe_mode_detected   = '';
if ( 0 === strpos( $stripe_secret_key, 'sk_live_' ) || 0 === strpos( $stripe_publishable_key, 'pk_live_' ) ) {
    $stripe_mode_detected = 'live';
} elseif ( 0 === strpos( $stripe_secret_key, 'sk_test_' ) || 0 === strpos( $stripe_publishable_key, 'pk_test_' ) ) {
    $stripe_mode_detected = 'test';
}

$square_can_connect = $pbs_key_set( 'pbs_square_app_id' ) && $pbs_key_set( 'pbs_square_app_secret' );
$stripe_can_connect = $pbs_key_set( 'pbs_stripe_connect_client_id' );
$paypal_verified    = get_option( 'pbs_paypal_merchant_email', '' );
?>
<div class="wrap pbs-settings-wrap">
<h1 style="margin-bottom:4px;">PBS Commerce — Settings</h1>
<p style="color:#666;margin-top:0;">Configure payment gateways, email notifications, and checkout behavior.</p>

<?php
foreach ( [ 'pbs_square_oauth_notice', 'pbs_stripe_oauth_notice' ] as $t_key ) {
    $notice = get_transient( $t_key );
    if ( $notice ) {
        delete_transient( $t_key );
        $class = 'notice-info';
        if ( isset( $notice['type'] ) && 'success' === $notice['type'] ) {
            $class = 'notice-success';
        } elseif ( isset( $notice['type'] ) && 'error' === $notice['type'] ) {
            $class = 'notice-error';
        }
        echo '<div class="notice ' . esc_attr( $class ) . ' is-dismissible"><p>' . esc_html( $notice['message'] ?? '' ) . '</p></div>';
    }
}
?>

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
.pbs-status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.pbs-status-dot.connected { background: #4caf50; }
.pbs-status-dot.disconnected { background: #e0e0e0; }
.pbs-status-dot.error { background: #f44336; }
.pbs-status-text { font-size: 12px; color: #888; }
.pbs-oauth-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 14px; border-radius: 5px; border: 1px solid #ddd;
    background: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
    text-decoration: none; color: #333; transition: background .2s;
}
.pbs-oauth-btn:hover { background: #f5f5f5; }
.pbs-oauth-btn.stripe-btn { border-color: #635bff; color: #635bff; }
.pbs-oauth-btn.square-btn { border-color: #333; color: #333; }
.pbs-oauth-btn.paypal-btn { border-color: #003087; color: #003087; }
.pbs-key-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pbs-reveal-btn { background: none; border: none; cursor: pointer; color: #888; padding: 4px; font-size: 12px; }
.pbs-reveal-btn:hover { color: #333; }
.pbs-key-set-indicator { font-size: 12px; color: #4caf50; font-weight: 500; }
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
.pbs-inline-status { margin-top: 8px; font-size: 13px; color: #555; }
.pbs-inline-status.success { color: #2e7d32; }
.pbs-inline-status.error { color: #c62828; }
.pbs-meta-list { margin: 8px 0 0; padding-left: 18px; color: #555; }
.pbs-badge {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    background: #eef6ff;
    color: #1967d2;
}
.pbs-badge.success { background: #e8f5e9; color: #2e7d32; }
.pbs-badge.error { background: #ffebee; color: #c62828; }
</style>

<form id="pbs-square-disconnect-form" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" style="display:none;">
    <input type="hidden" name="action" value="pbs_square_disconnect">
    <?php wp_nonce_field( 'pbs_square_disconnect' ); ?>
</form>

<form id="pbs-stripe-disconnect-form" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" style="display:none;">
    <input type="hidden" name="action" value="pbs_stripe_disconnect">
    <?php wp_nonce_field( 'pbs_stripe_disconnect' ); ?>
</form>

<form method="post" action="options.php" id="pbs-settings-form">
<?php settings_fields( 'pbs_commerce_settings' ); ?>

<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">💳</span>
      <span class="pbs-card-title">Stripe</span>
      <span class="pbs-status-dot <?php echo $stripe_status['connected'] ? 'connected' : ( $pbs_key_set( 'pbs_stripe_secret_key' ) ? 'error' : 'disconnected' ); ?>"></span>
      <span class="pbs-status-text">
        <?php
        if ( $stripe_status['connected'] && $pbs_enabled( 'pbs_stripe_enabled' ) ) {
            echo esc_html( 'Active' );
        } elseif ( $pbs_key_set( 'pbs_stripe_secret_key' ) ) {
            echo esc_html( 'Configured (disabled)' );
        } else {
            echo esc_html( 'Not configured' );
        }
        ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_stripe_enabled" value="1" <?php checked( get_option( 'pbs_stripe_enabled', 0 ), 1 ); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo $pbs_enabled( 'pbs_stripe_enabled' ) ? esc_html( 'Enabled' ) : esc_html( 'Disabled' ); ?></span>
      <span class="pbs-enabled-badge <?php echo $pbs_enabled( 'pbs_stripe_enabled' ) ? 'on' : 'off'; ?>">
        <?php echo $pbs_enabled( 'pbs_stripe_enabled' ) ? esc_html( 'ON' ) : esc_html( 'OFF' ); ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept credit/debit cards via Stripe.
      <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer">Get API keys ↗</a>
      &nbsp;|&nbsp;
      <a href="https://dashboard.stripe.com/test/apikeys" target="_blank" rel="noopener noreferrer">Test keys ↗</a>
    </p>

    <div style="margin-bottom:16px;">
      <?php if ( $pbs_key_set( 'pbs_stripe_secret_key' ) ) : ?>
        <span style="color:#4caf50;font-weight:600;"><?php echo esc_html( '✅ Stripe connected' ); ?></span>
        <button type="submit" class="pbs-oauth-btn stripe-btn" form="pbs-stripe-disconnect-form"><?php echo esc_html( 'Disconnect' ); ?></button>
      <?php else : ?>
        <a href="<?php echo esc_url( PBS_Stripe_OAuth::get_auth_url() ); ?>" class="pbs-oauth-btn stripe-btn" <?php echo $stripe_can_connect ? '' : 'style="opacity:.5;pointer-events:none;" title="Enter Connect Client ID first"'; ?>>
          <?php echo esc_html( '🔗 Connect with Stripe OAuth' ); ?>
        </a>
        <span style="margin-left:8px;color:#888;font-size:12px;"><?php echo esc_html( '— or enter keys manually below' ); ?></span>
      <?php endif; ?>
      <?php if ( ! empty( $stripe_status['stripe_user_id'] ) ) : ?>
        <div class="pbs-inline-status success"><?php echo esc_html( 'Stripe User ID: ' . $stripe_status['stripe_user_id'] ); ?></div>
      <?php endif; ?>
      <?php if ( ! empty( $stripe_status['account_name'] ) || ! empty( $stripe_status['email'] ) ) : ?>
        <div class="pbs-inline-status success">
          <?php echo esc_html( trim( $stripe_status['account_name'] . ( $stripe_status['email'] ? ' — ' . $stripe_status['email'] : '' ) ) ); ?>
        </div>
      <?php endif; ?>
    </div>

    <table>
      <tr>
        <th>Publishable Key</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="text" id="pbs_stripe_pub_key" name="pbs_stripe_publishable_key"
                   value="<?php echo esc_attr( get_option( 'pbs_stripe_publishable_key', '' ) ); ?>"
                   class="regular-text" placeholder="pk_live_..." autocomplete="off">
            <?php if ( $pbs_key_set( 'pbs_stripe_publishable_key' ) ) : ?>
              <span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span>
            <?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Secret Key</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" id="pbs_stripe_secret_key" name="pbs_stripe_secret_key"
                   value="<?php echo esc_attr( get_option( 'pbs_stripe_secret_key', '' ) ); ?>"
                   class="regular-text" placeholder="sk_live_..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=document.getElementById('pbs_stripe_secret_key');f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <button type="button" class="button" id="pbs-validate-stripe"><?php echo esc_html( '🔍 Validate Keys' ); ?></button>
            <?php if ( $pbs_key_set( 'pbs_stripe_secret_key' ) ) : ?>
              <span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span>
            <?php endif; ?>
          </div>
          <div id="pbs-stripe-validation-result" class="pbs-inline-status"></div>
        </td>
      </tr>
      <tr>
        <th>Webhook Secret</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" name="pbs_stripe_webhook_secret"
                   value="<?php echo esc_attr( get_option( 'pbs_stripe_webhook_secret', '' ) ); ?>"
                   class="regular-text" placeholder="whsec_..." autocomplete="new-password">
            <?php if ( $pbs_key_set( 'pbs_stripe_webhook_secret' ) ) : ?>
              <span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span>
            <?php endif; ?>
          </div>
          <p class="description">Webhook URL: <code><?php echo esc_html( rest_url( 'pbs-ec/v1/stripe-webhook' ) ); ?></code></p>
        </td>
      </tr>
      <tr>
        <th>Connect Client ID <span style="font-weight:400;color:#888;">(OAuth)</span></th>
        <td>
          <input type="text" name="pbs_stripe_connect_client_id"
                 value="<?php echo esc_attr( get_option( 'pbs_stripe_connect_client_id', '' ) ); ?>"
                 class="regular-text" placeholder="ca_...">
          <p class="description">From Stripe Dashboard → Connect → Settings. Enables one-click OAuth connect.</p>
        </td>
      </tr>
      <tr>
        <th>Mode</th>
        <td>
          <select name="pbs_stripe_mode">
            <option value="test" <?php selected( get_option( 'pbs_stripe_mode', 'test' ), 'test' ); ?>>🧪 Test / Sandbox</option>
            <option value="live" <?php selected( get_option( 'pbs_stripe_mode', 'test' ), 'live' ); ?>>🟢 Live</option>
          </select>
          <?php if ( 'test' === $stripe_mode_detected ) : ?>
            <span class="pbs-badge"><?php echo esc_html( 'Test Mode detected' ); ?></span>
          <?php elseif ( 'live' === $stripe_mode_detected ) : ?>
            <span class="pbs-badge success"><?php echo esc_html( 'Live Mode detected' ); ?></span>
          <?php endif; ?>
        </td>
      </tr>
    </table>
  </div>
</div>

<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">⬛</span>
      <span class="pbs-card-title">Square</span>
      <span class="pbs-status-dot <?php echo $square_status['expired'] ? 'error' : ( $square_status['connected'] ? 'connected' : 'disconnected' ); ?>"></span>
      <span class="pbs-status-text">
        <?php
        if ( ! empty( $square_status['expired'] ) ) {
            echo esc_html( 'Token expired' );
        } elseif ( ! empty( $square_status['connected'] ) && $pbs_enabled( 'pbs_square_enabled' ) ) {
            echo esc_html( 'Active' );
        } elseif ( $pbs_key_set( 'pbs_square_access_token' ) ) {
            echo esc_html( 'Configured (disabled)' );
        } else {
            echo esc_html( 'Not configured' );
        }
        ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_square_enabled" value="1" <?php checked( get_option( 'pbs_square_enabled', 0 ), 1 ); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo $pbs_enabled( 'pbs_square_enabled' ) ? esc_html( 'Enabled' ) : esc_html( 'Disabled' ); ?></span>
      <span class="pbs-enabled-badge <?php echo $pbs_enabled( 'pbs_square_enabled' ) ? 'on' : 'off'; ?>">
        <?php echo $pbs_enabled( 'pbs_square_enabled' ) ? esc_html( 'ON' ) : esc_html( 'OFF' ); ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept cards via Square's Web Payments SDK.
      <a href="https://developer.squareup.com/apps" target="_blank" rel="noopener noreferrer">Square Developer Dashboard ↗</a>
    </p>

    <div style="margin-bottom:16px;">
      <?php if ( $pbs_key_set( 'pbs_square_access_token' ) ) : ?>
        <span style="font-weight:600;color:<?php echo ! empty( $square_status['expired'] ) ? '#c62828' : '#4caf50'; ?>;">
            <?php echo ! empty( $square_status['expired'] ) ? esc_html( 'Token Expired — Reconnect' ) : esc_html( '✅ Square connected' ); ?>
        </span>
        <button type="submit" class="pbs-oauth-btn square-btn" form="pbs-square-disconnect-form"><?php echo esc_html( 'Disconnect' ); ?></button>
      <?php else : ?>
        <a href="<?php echo esc_url( PBS_Square_OAuth::get_auth_url() ); ?>" class="pbs-oauth-btn square-btn" <?php echo $square_can_connect ? '' : 'style="opacity:.5;pointer-events:none;" title="Enter App ID and App Secret first"'; ?>>
          <?php echo esc_html( '🔗 Connect with Square OAuth' ); ?>
        </a>
        <span style="margin-left:8px;color:#888;font-size:12px;"><?php echo esc_html( '— or enter access token manually below' ); ?></span>
      <?php endif; ?>

      <?php if ( $pbs_key_set( 'pbs_square_refresh_token' ) ) : ?>
        <span class="pbs-badge"><?php echo esc_html( '🔄 Auto-refresh' ); ?></span>
      <?php endif; ?>

      <?php if ( $pbs_key_set( 'pbs_square_access_token' ) ) : ?>
        <ul class="pbs-meta-list">
          <?php if ( ! empty( $square_status['merchant_id'] ) ) : ?>
            <li><?php echo esc_html( 'Merchant ID: ' . $square_status['merchant_id'] ); ?></li>
          <?php endif; ?>
          <?php if ( ! empty( $square_status['location_id'] ) ) : ?>
            <li><?php echo esc_html( 'Location ID: ' . $square_status['location_id'] ); ?></li>
          <?php endif; ?>
          <?php if ( ! empty( $square_status['expires_at'] ) ) : ?>
            <li><?php echo esc_html( 'Token Expires: ' . $square_status['expires_at'] ); ?></li>
          <?php endif; ?>
        </ul>
      <?php endif; ?>
    </div>

    <table>
      <tr>
        <th>App ID</th>
        <td>
          <input type="text" name="pbs_square_app_id"
                 value="<?php echo esc_attr( get_option( 'pbs_square_app_id', '' ) ); ?>"
                 class="regular-text" placeholder="sq0idp-...">
          <p class="description">From your Square app → Credentials tab.</p>
        </td>
      </tr>
      <tr>
        <th>App Secret</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" id="pbs_square_app_secret" name="pbs_square_app_secret"
                   value="<?php echo esc_attr( get_option( 'pbs_square_app_secret', '' ) ); ?>"
                   class="regular-text" placeholder="sq0csp-..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=document.getElementById('pbs_square_app_secret');f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if ( $pbs_key_set( 'pbs_square_app_secret' ) ) : ?>
              <span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span>
            <?php endif; ?>
          </div>
          <p class="description">Required for OAuth. From Square Developer → Your App → OAuth.</p>
        </td>
      </tr>
      <tr>
        <th>Location ID</th>
        <td>
          <input type="text" name="pbs_square_location_id"
                 value="<?php echo esc_attr( get_option( 'pbs_square_location_id', '' ) ); ?>"
                 class="regular-text" placeholder="L...">
        </td>
      </tr>
      <tr>
        <th>Access Token</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" name="pbs_square_access_token"
                   value="<?php echo esc_attr( get_option( 'pbs_square_access_token', '' ) ); ?>"
                   class="regular-text" placeholder="EAAAl..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=this.previousElementSibling;f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if ( $pbs_key_set( 'pbs_square_access_token' ) ) : ?>
              <span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span>
            <?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Environment</th>
        <td>
          <select name="pbs_square_env">
            <option value="sandbox" <?php selected( get_option( 'pbs_square_env', 'sandbox' ), 'sandbox' ); ?>>🧪 Sandbox</option>
            <option value="production" <?php selected( get_option( 'pbs_square_env', 'sandbox' ), 'production' ); ?>>🟢 Production</option>
          </select>
        </td>
      </tr>
    </table>
  </div>
</div>

<div class="pbs-gateway-card">
  <div class="pbs-card-header">
    <div class="pbs-card-header-left">
      <span style="font-size:22px;">🅿️</span>
      <span class="pbs-card-title">PayPal</span>
      <span class="pbs-status-dot <?php echo ( $pbs_key_set( 'pbs_paypal_secret' ) && $pbs_enabled( 'pbs_paypal_enabled' ) ) ? 'connected' : 'disconnected'; ?>"></span>
      <span class="pbs-status-text">
        <?php
        if ( $pbs_key_set( 'pbs_paypal_secret' ) && $pbs_enabled( 'pbs_paypal_enabled' ) ) {
            echo esc_html( 'Active' );
        } elseif ( $pbs_key_set( 'pbs_paypal_secret' ) ) {
            echo esc_html( 'Configured (disabled)' );
        } else {
            echo esc_html( 'Not configured' );
        }
        ?>
      </span>
    </div>
    <div class="pbs-toggle-wrap">
      <label class="pbs-toggle">
        <input type="checkbox" name="pbs_paypal_enabled" value="1" <?php checked( get_option( 'pbs_paypal_enabled', 0 ), 1 ); ?>>
        <span class="pbs-toggle-slider"></span>
      </label>
      <span class="pbs-toggle-label"><?php echo $pbs_enabled( 'pbs_paypal_enabled' ) ? esc_html( 'Enabled' ) : esc_html( 'Disabled' ); ?></span>
      <span class="pbs-enabled-badge <?php echo $pbs_enabled( 'pbs_paypal_enabled' ) ? 'on' : 'off'; ?>">
        <?php echo $pbs_enabled( 'pbs_paypal_enabled' ) ? esc_html( 'ON' ) : esc_html( 'OFF' ); ?>
      </span>
    </div>
  </div>
  <div class="pbs-card-body">
    <p style="margin:0 0 16px;font-size:13px;color:#666;">
      Accept PayPal & Venmo via PayPal JS SDK.
      <a href="https://developer.paypal.com/dashboard/applications" target="_blank" rel="noopener noreferrer">PayPal Developer Dashboard ↗</a>
    </p>

    <div style="margin-bottom:16px;">
      <button type="button" class="pbs-oauth-btn paypal-btn" id="pbs-test-paypal"><?php echo esc_html( '🔍 Test Connection' ); ?></button>
      <span style="margin-left:8px;color:#888;font-size:12px;"><?php echo esc_html( 'PayPal business account credentials — Client ID and Secret from developer.paypal.com → My Apps & Credentials' ); ?></span>
      <?php if ( ! empty( $paypal_verified ) ) : ?>
        <div class="pbs-inline-status success"><?php echo esc_html( '✅ Verified: ' . $paypal_verified ); ?></div>
      <?php endif; ?>
      <div id="pbs-paypal-test-result" class="pbs-inline-status"></div>
    </div>

    <table>
      <tr>
        <th>Client ID</th>
        <td>
          <input type="text" id="pbs_paypal_client_id" name="pbs_paypal_client_id"
                 value="<?php echo esc_attr( get_option( 'pbs_paypal_client_id', '' ) ); ?>"
                 class="regular-text" placeholder="AY...">
          <?php if ( $pbs_key_set( 'pbs_paypal_client_id' ) ) : ?><span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span><?php endif; ?>
        </td>
      </tr>
      <tr>
        <th>Secret</th>
        <td>
          <div class="pbs-key-wrap">
            <input type="password" id="pbs_paypal_secret" name="pbs_paypal_secret"
                   value="<?php echo esc_attr( get_option( 'pbs_paypal_secret', '' ) ); ?>"
                   class="regular-text" placeholder="EL..." autocomplete="new-password">
            <button type="button" class="pbs-reveal-btn" onclick="var f=document.getElementById('pbs_paypal_secret');f.type=f.type==='password'?'text':'password';this.textContent=f.type==='password'?'👁 Show':'🙈 Hide';">👁 Show</button>
            <?php if ( $pbs_key_set( 'pbs_paypal_secret' ) ) : ?><span class="pbs-key-set-indicator"><?php echo esc_html( '✓ Set' ); ?></span><?php endif; ?>
          </div>
        </td>
      </tr>
      <tr>
        <th>Mode</th>
        <td>
          <select id="pbs_paypal_mode" name="pbs_paypal_mode">
            <option value="sandbox" <?php selected( get_option( 'pbs_paypal_mode', 'sandbox' ), 'sandbox' ); ?>>🧪 Sandbox</option>
            <option value="live" <?php selected( get_option( 'pbs_paypal_mode', 'sandbox' ), 'live' ); ?>>🟢 Live</option>
          </select>
        </td>
      </tr>
      <tr>
        <th>Enable Venmo</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_paypal_venmo" value="1" <?php checked( get_option( 'pbs_paypal_venmo', 0 ), 1 ); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Show Venmo button (US only)</span>
        </td>
      </tr>
    </table>
  </div>
</div>

<div class="pbs-section-card">
  <div class="pbs-section-header">📧 Email Notifications</div>
  <div class="pbs-section-body">
    <table class="form-table" style="margin:0;">
      <tr>
        <th style="width:200px;">From Name</th>
        <td><input type="text" name="pbs_email_from_name" value="<?php echo esc_attr( get_option( 'pbs_email_from_name', 'Psi Beta Sigma 1914' ) ); ?>" class="regular-text"></td>
      </tr>
      <tr>
        <th>From Email</th>
        <td><input type="email" name="pbs_email_from" value="<?php echo esc_attr( get_option( 'pbs_email_from', 'secretary@psibetasigma1914.org' ) ); ?>" class="regular-text"></td>
      </tr>
      <tr>
        <th>BCC (all orders)</th>
        <td>
          <input type="email" name="pbs_email_bcc" value="<?php echo esc_attr( get_option( 'pbs_email_bcc', '' ) ); ?>" class="regular-text" placeholder="treasurer@psibetasigma1914.org">
          <p class="description">Blind copy every confirmation to this address.</p>
        </td>
      </tr>
      <tr>
        <th>Treasurer Email</th>
        <td>
          <input type="email" name="pbs_treasurer_email" value="<?php echo esc_attr( get_option( 'pbs_treasurer_email', 'treasurer@psibetasigma1914.org' ) ); ?>" class="regular-text">
          <p class="description">Receives a notification for every new order.</p>
        </td>
      </tr>
      <tr>
        <th>Send Event Reminders</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_email_reminders" value="1" <?php checked( get_option( 'pbs_email_reminders', 1 ), 1 ); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Email attendees 3 days before the event with their QR ticket</span>
        </td>
      </tr>
    </table>
  </div>
</div>

<div class="pbs-section-card">
  <div class="pbs-section-header">🛒 Checkout Behavior</div>
  <div class="pbs-section-body">
    <table class="form-table" style="margin:0;">
      <tr>
        <th style="width:200px;">Cover Processing Fees</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_donor_covers_fees" value="1" <?php checked( get_option( 'pbs_donor_covers_fees', 0 ), 1 ); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Show "Cover the processing fee?" checkbox at checkout (Zeffy model)</span>
        </td>
      </tr>
      <tr>
        <th>Tax-Deductible Receipts</th>
        <td>
          <label class="pbs-toggle" style="vertical-align:middle;">
            <input type="checkbox" name="pbs_tax_receipts" value="1" <?php checked( get_option( 'pbs_tax_receipts', 1 ), 1 ); ?>>
            <span class="pbs-toggle-slider"></span>
          </label>
          <span style="margin-left:8px;font-size:13px;color:#555;">Include tax-deductible language in donation confirmation emails</span>
        </td>
      </tr>
      <tr>
        <th>Max Tickets Per Order</th>
        <td>
          <input type="number" name="pbs_max_tickets" value="<?php echo esc_attr( get_option( 'pbs_max_tickets', 10 ) ); ?>" style="width:80px;" min="1" max="100">
        </td>
      </tr>
      <tr>
        <th>EIN (for receipts)</th>
        <td>
          <input type="text" name="pbs_org_ein" value="<?php echo esc_attr( get_option( 'pbs_org_ein', '' ) ); ?>" class="regular-text" placeholder="XX-XXXXXXX">
          <p class="description">Shown on tax-deductible donation receipts.</p>
        </td>
      </tr>
    </table>
  </div>
</div>

<div class="pbs-save-bar">
  <?php submit_button( 'Save Settings', 'primary', 'submit', false ); ?>
  <span id="pbs-save-status" style="font-size:13px;color:#888;"></span>
</div>

</form>

<script>
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

document.getElementById('pbs-settings-form').addEventListener('submit', function() {
    document.getElementById('pbs-save-status').textContent = 'Saving…';
});

(function() {
    var stripeButton = document.getElementById('pbs-validate-stripe');
    var stripeResult = document.getElementById('pbs-stripe-validation-result');
    if (stripeButton && window.PBS_Admin) {
        stripeButton.addEventListener('click', function() {
            stripeResult.className = 'pbs-inline-status';
            stripeResult.textContent = 'Validating Stripe keys…';

            var body = new URLSearchParams({
                action: 'pbs_validate_stripe_keys',
                nonce: PBS_Admin.nonce,
                secret_key: document.getElementById('pbs_stripe_secret_key').value,
                publishable_key: document.getElementById('pbs_stripe_pub_key').value
            });

            fetch(PBS_Admin.ajax_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                body: body.toString()
            }).then(function(res) {
                return res.json();
            }).then(function(data) {
                if (data.success) {
                    stripeResult.className = 'pbs-inline-status success';
                    stripeResult.textContent = data.data.message + ' ' + [data.data.account_name, data.data.email].filter(Boolean).join(' — ');
                } else {
                    stripeResult.className = 'pbs-inline-status error';
                    stripeResult.textContent = (data.data && data.data.message) ? data.data.message : 'Stripe validation failed.';
                }
            }).catch(function() {
                stripeResult.className = 'pbs-inline-status error';
                stripeResult.textContent = 'Stripe validation failed.';
            });
        });
    }

    var paypalButton = document.getElementById('pbs-test-paypal');
    var paypalResult = document.getElementById('pbs-paypal-test-result');
    if (paypalButton && window.PBS_Admin) {
        paypalButton.addEventListener('click', function() {
            paypalResult.className = 'pbs-inline-status';
            paypalResult.textContent = 'Testing PayPal connection…';

            var body = new URLSearchParams({
                action: 'pbs_test_paypal',
                nonce: PBS_Admin.nonce,
                client_id: document.getElementById('pbs_paypal_client_id').value,
                secret: document.getElementById('pbs_paypal_secret').value,
                mode: document.getElementById('pbs_paypal_mode').value
            });

            fetch(PBS_Admin.ajax_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                body: body.toString()
            }).then(function(res) {
                return res.json();
            }).then(function(data) {
                if (data.success) {
                    paypalResult.className = 'pbs-inline-status success';
                    paypalResult.textContent = data.data.message + ' ' + [data.data.name, data.data.email, data.data.payer_id].filter(Boolean).join(' — ');
                } else {
                    paypalResult.className = 'pbs-inline-status error';
                    paypalResult.textContent = (data.data && data.data.message) ? data.data.message : 'PayPal connection test failed.';
                }
            }).catch(function() {
                paypalResult.className = 'pbs-inline-status error';
                paypalResult.textContent = 'PayPal connection test failed.';
            });
        });
    }
})();
</script>
</div>
