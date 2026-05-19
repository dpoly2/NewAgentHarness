<?php defined( 'ABSPATH' ) || exit; ?>
<div class="xftc-form-wrap" id="xftc-register-wrap">
    <h2 class="xftc-form-title"><?php esc_html_e( 'Create Your Parent Account', 'xftc-membership' ); ?></h2>
    <p class="xftc-form-subtitle"><?php esc_html_e( 'Register once — then add all your athletes and manage everything from your portal.', 'xftc-membership' ); ?></p>

    <div id="xftc-register-message" class="xftc-message" style="display:none;"></div>

    <form id="xftc-register-form" novalidate>
        <div class="xftc-form-row xftc-two-col">
            <div class="xftc-form-group">
                <label for="xftc_first_name"><?php esc_html_e( 'First Name', 'xftc-membership' ); ?> <span class="xftc-required">*</span></label>
                <input type="text" id="xftc_first_name" name="first_name" required placeholder="<?php esc_attr_e( 'Jane', 'xftc-membership' ); ?>">
            </div>
            <div class="xftc-form-group">
                <label for="xftc_last_name"><?php esc_html_e( 'Last Name', 'xftc-membership' ); ?> <span class="xftc-required">*</span></label>
                <input type="text" id="xftc_last_name" name="last_name" required placeholder="<?php esc_attr_e( 'Smith', 'xftc-membership' ); ?>">
            </div>
        </div>
        <div class="xftc-form-group">
            <label for="xftc_email"><?php esc_html_e( 'Email Address', 'xftc-membership' ); ?> <span class="xftc-required">*</span></label>
            <input type="email" id="xftc_email" name="email" required placeholder="<?php esc_attr_e( 'jane@example.com', 'xftc-membership' ); ?>">
        </div>
        <div class="xftc-form-group">
            <label for="xftc_phone"><?php esc_html_e( 'Phone Number', 'xftc-membership' ); ?></label>
            <input type="tel" id="xftc_phone" name="phone" placeholder="<?php esc_attr_e( '(555) 555-5555', 'xftc-membership' ); ?>">
        </div>
        <div class="xftc-form-row xftc-two-col">
            <div class="xftc-form-group">
                <label for="xftc_password"><?php esc_html_e( 'Password', 'xftc-membership' ); ?> <span class="xftc-required">*</span></label>
                <input type="password" id="xftc_password" name="password" required minlength="8" placeholder="<?php esc_attr_e( 'Min. 8 characters', 'xftc-membership' ); ?>">
            </div>
            <div class="xftc-form-group">
                <label for="xftc_password_confirm"><?php esc_html_e( 'Confirm Password', 'xftc-membership' ); ?> <span class="xftc-required">*</span></label>
                <input type="password" id="xftc_password_confirm" name="password_confirm" required placeholder="<?php esc_attr_e( 'Repeat password', 'xftc-membership' ); ?>">
            </div>
        </div>
        <div class="xftc-form-submit">
            <button type="submit" class="xftc-btn xftc-btn-primary" id="xftc-register-btn">
                <?php esc_html_e( 'Create Account', 'xftc-membership' ); ?>
            </button>
        </div>
        <p class="xftc-login-link">
            <?php echo wp_kses_post( sprintf(
                __( 'Already have an account? <a href="%s">Log in here</a>', 'xftc-membership' ),
                esc_url( wp_login_url() )
            ) ); ?>
        </p>
    </form>
</div>
