<?php
/**
 * Template Name: Athlete Roster
 * @package TRACKSUITE_Theme
 */
TRACKSUITE_partial( 'header' );
?>

<div class="portal-header">
    <div class="container">
        <p class="section-header__eyebrow" style="margin-bottom:.25rem">👟 The Team</p>
        <h1 class="portal-header__title">2026 Roster</h1>
    </div>
</div>

<section class="section section--gray" style="padding-top:1.5rem;">
    <div class="container">

        <!-- Division filters -->
        <div class="schedule-filters" role="tablist">
            <button class="schedule-filter-btn is-active" data-filter="all">All Athletes</button>
            <button class="schedule-filter-btn" data-filter="youth">Youth (6–10)</button>
            <button class="schedule-filter-btn" data-filter="junior">Junior (11–14)</button>
            <button class="schedule-filter-btn" data-filter="senior">Senior (15–18)</button>
        </div>

        <?php echo do_shortcode( '[TRACKSUITE_roster view="cards" show_stats="true" show_events="true"]' ); ?>

    </div>
</section>

<?php TRACKSUITE_partial( 'footer' ); ?>

