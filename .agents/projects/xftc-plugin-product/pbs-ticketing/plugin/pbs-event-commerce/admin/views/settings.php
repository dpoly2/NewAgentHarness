<?php if ( ! defined( 'ABSPATH' ) ) exit; ?>
<div class="wrap">
  <h1>PBS Commerce — Settings</h1>
  <form method="post" action="options.php">
    <?php settings_fields( 'pbs_commerce_settings' ); ?>
    <table class="form-table">
      <tr><th colspan="2"><h2 style="color:#164f90">💳 Stripe</h2></th></tr>
      <tr><th>Publishable Key</th><td><input type="text" name="pbs_stripe_publishable_key" value="<?php echo esc_attr(get_option('pbs_stripe_publishable_key')); ?>" class="regular-text"></td></tr>
      <tr><th>Secret Key</th><td><input type="password" name="pbs_stripe_secret_key" value="<?php echo esc_attr(get_option('pbs_stripe_secret_key')); ?>" class="regular-text"></td></tr>

      <tr><th colspan="2"><h2 style="color:#164f90">⬛ Square</h2></th></tr>
      <tr><th>App ID</th><td><input type="text" name="pbs_square_app_id" value="<?php echo esc_attr(get_option('pbs_square_app_id')); ?>" class="regular-text"></td></tr>
      <tr><th>Location ID</th><td><input type="text" name="pbs_square_location_id" value="<?php echo esc_attr(get_option('pbs_square_location_id')); ?>" class="regular-text"></td></tr>
      <tr><th>Access Token</th><td><input type="password" name="pbs_square_access_token" value="<?php echo esc_attr(get_option('pbs_square_access_token')); ?>" class="regular-text"></td></tr>
      <tr><th>Environment</th><td><select name="pbs_square_env"><option value="sandbox" <?php selected(get_option('pbs_square_env'),'sandbox'); ?>>Sandbox</option><option value="production" <?php selected(get_option('pbs_square_env'),'production'); ?>>Production</option></select></td></tr>

      <tr><th colspan="2"><h2 style="color:#164f90">🅿️ PayPal</h2></th></tr>
      <tr><th>Client ID</th><td><input type="text" name="pbs_paypal_client_id" value="<?php echo esc_attr(get_option('pbs_paypal_client_id')); ?>" class="regular-text"></td></tr>
      <tr><th>Secret</th><td><input type="password" name="pbs_paypal_secret" value="<?php echo esc_attr(get_option('pbs_paypal_secret')); ?>" class="regular-text"></td></tr>
      <tr><th>Mode</th><td><select name="pbs_paypal_mode"><option value="sandbox" <?php selected(get_option('pbs_paypal_mode'),'sandbox'); ?>>Sandbox</option><option value="live" <?php selected(get_option('pbs_paypal_mode'),'live'); ?>>Live</option></select></td></tr>

      <tr><th colspan="2"><h2 style="color:#164f90">📧 Email</h2></th></tr>
      <tr><th>From Name</th><td><input type="text" name="pbs_email_from_name" value="<?php echo esc_attr(get_option('pbs_email_from_name','Psi Beta Sigma 1914')); ?>" class="regular-text"></td></tr>
      <tr><th>From Email</th><td><input type="email" name="pbs_email_from" value="<?php echo esc_attr(get_option('pbs_email_from','secretary@psibetasigma1914.org')); ?>" class="regular-text"></td></tr>
      <tr><th>BCC (notifications)</th><td><input type="email" name="pbs_email_bcc" value="<?php echo esc_attr(get_option('pbs_email_bcc','')); ?>" class="regular-text" placeholder="treasurer@psibetasigma1914.org"></td></tr>
      <tr><th>Treasurer Email</th><td><input type="email" name="pbs_treasurer_email" value="<?php echo esc_attr(get_option('pbs_treasurer_email','treasurer@psibetasigma1914.org')); ?>" class="regular-text"></td></tr>
    </table>
    <?php submit_button( 'Save Settings' ); ?>
  </form>
</div>
