<?php
/**
 * Template Name: Results & Records
 * @package XFTC_Theme
 */
xftc_partial( 'header' );
?>

<div class="portal-header">
    <div class="container">
        <p class="section-header__eyebrow" style="margin-bottom:.25rem">🏆 Performance</p>
        <h1 class="portal-header__title">Results & Club Records</h1>
    </div>
</div>

<section class="section" style="padding-top:1.5rem;">
    <div class="container">

        <!-- View toggle tabs -->
        <div class="portal-tabs">
            <div class="portal-tab is-active" data-tab="results">Meet Results</div>
            <div class="portal-tab" data-tab="records">Club Records</div>
            <div class="portal-tab" data-tab="leaderboard">Season Leaderboard</div>
        </div>

        <!-- Results tab -->
        <div class="tab-panel" id="tab-results">
            <?php echo do_shortcode( '[xftc_results view="table" show_filters="true" highlight_pb="true" highlight_cr="true"]' ); ?>
        </div>

        <!-- Records tab -->
        <div class="tab-panel" id="tab-records" style="display:none;">
            <?php echo do_shortcode( '[xftc_club_records]' ); ?>
        </div>

        <!-- Leaderboard tab -->
        <div class="tab-panel" id="tab-leaderboard" style="display:none;">
            <?php echo do_shortcode( '[xftc_leaderboard season="current" limit="20"]' ); ?>
        </div>

    </div>
</section>

<?php xftc_partial( 'footer' ); ?>
