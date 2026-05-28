<?php
/**
 * Template Name: Meet Schedule
 * @package TRACKSUITE_Theme
 */
TRACKSUITE_partial( 'header' );
?>

<div class="portal-header">
    <div class="container">
        <p class="section-header__eyebrow" style="margin-bottom:.25rem">📅 2026 Season</p>
        <h1 class="portal-header__title">Meet Schedule</h1>
    </div>
</div>

<section class="section section--gray" style="padding-top:1.5rem;">
    <div class="container">

        <!-- Season filter tabs -->
        <div class="schedule-filters" role="tablist">
            <button class="schedule-filter-btn is-active" data-filter="all">All Meets</button>
            <button class="schedule-filter-btn" data-filter="indoor">Indoor</button>
            <button class="schedule-filter-btn" data-filter="outdoor">Outdoor</button>
            <button class="schedule-filter-btn" data-filter="invitational">Invitationals</button>
            <button class="schedule-filter-btn" data-filter="upcoming">Upcoming</button>
        </div>

        <!-- Plugin shortcode drives the data -->
        <?php echo do_shortcode( '[TRACKSUITE_schedule view="list" show_filters="false" show_register="true"]' ); ?>

    </div>
</section>

<?php TRACKSUITE_partial( 'footer' ); ?>

