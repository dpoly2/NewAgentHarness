<?php
/**
 * Template Name: Parent Portal
 * @package TRACKSUITE_Theme
 */
TRACKSUITE_partial( 'header' );

if ( ! is_user_logged_in() ) {
    ?>
    <div class="container" style="padding-block:4rem;text-align:center;">
        <h1 class="section-header__title" style="font-family:var(--font-heading);font-size:2.5rem;margin-bottom:1rem;">Parent Portal</h1>
        <p style="color:var(--ts-gray-600);margin-bottom:2rem;">Please log in to access your athlete dashboard.</p>
        <?php echo do_shortcode( '[TRACKSUITE_login_form]' ); ?>
        <p style="margin-top:1.5rem;font-size:.85rem;">
            Don't have an account? <a href="<?php echo esc_url( home_url('/register') ); ?>">Register here</a>
        </p>
    </div>
    <?php
} else {
    $user = wp_get_current_user();
    ?>
    <div class="portal-header">
        <div class="container" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
            <div>
                <p class="section-header__eyebrow" style="margin-bottom:.25rem">👋 Welcome back</p>
                <h1 class="portal-header__title"><?php echo esc_html( $user->display_name ); ?></h1>
            </div>
            <a href="<?php echo esc_url( wp_logout_url( home_url() ) ); ?>" class="btn btn--outline btn--sm">Log Out</a>
        </div>
    </div>

    <section class="section" style="padding-top:1.5rem;">
        <div class="container">

            <div class="portal-tabs">
                <div class="portal-tab is-active" data-tab="athletes">My Athletes</div>
                <div class="portal-tab" data-tab="schedule">Schedule</div>
                <div class="portal-tab" data-tab="results">Results</div>
                <div class="portal-tab" data-tab="payments">Payments</div>
                <div class="portal-tab" data-tab="travel">Travel</div>
            </div>

            <div id="tab-athletes">
                <?php echo do_shortcode( '[TRACKSUITE_my_athletes]' ); ?>
            </div>

            <div id="tab-schedule" style="display:none;">
                <?php echo do_shortcode( '[TRACKSUITE_my_schedule show_register="true"]' ); ?>
            </div>

            <div id="tab-results" style="display:none;">
                <?php echo do_shortcode( '[TRACKSUITE_my_results show_chart="true"]' ); ?>
            </div>

            <div id="tab-payments" style="display:none;">
                <?php echo do_shortcode( '[TRACKSUITE_my_payments show_receipts="true"]' ); ?>
            </div>

            <div id="tab-travel" style="display:none;">
                <?php echo do_shortcode( '[TRACKSUITE_my_travel]' ); ?>
            </div>

        </div>
    </section>
    <?php
}
TRACKSUITE_partial( 'footer' );
?>

