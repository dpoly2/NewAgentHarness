<?php
/**
 * Template tag helpers
 * @package TRACKSUITE_Theme
 */

defined( 'ABSPATH' ) || exit;

/**
 * Output the page title block
 */
function TRACKSUITE_page_title( string $eyebrow = '', string $title = '', string $icon = '' ): void {
    if ( ! $title ) $title = get_the_title();
    ?>
    <div class="portal-header">
        <div class="container">
            <?php if ( $eyebrow ) : ?>
                <p class="section-header__eyebrow" style="margin-bottom:.25rem"><?php echo wp_kses_post( $icon . ' ' . $eyebrow ); ?></p>
            <?php endif; ?>
            <h1 class="portal-header__title"><?php echo esc_html( $title ); ?></h1>
        </div>
    </div>
    <?php
}

/**
 * Output a meet card
 */
function TRACKSUITE_meet_card( object $meet ): void {
    $date  = ! empty( $meet->meet_date ) ? strtotime( $meet->meet_date ) : 0;
    $day   = $date ? date( 'j', $date ) : '—';
    $month = $date ? date( 'M', $date ) : '';
    $type_labels = [
        'competitive'   => 'Competitive',
        'invitational'  => 'Invitational',
        'practice'      => 'Practice',
    ];
    $badge = $type_labels[ $meet->type ?? '' ] ?? ucfirst( $meet->type ?? '' );
    ?>
    <div class="meet-card" data-type="<?php echo esc_attr( $meet->type ?? '' ); ?>" data-status="<?php echo esc_attr( $meet->status ?? '' ); ?>">
        <div class="meet-card__date">
            <div class="meet-card__date-day"><?php echo esc_html( $day ); ?></div>
            <div class="meet-card__date-month"><?php echo esc_html( $month ); ?></div>
        </div>
        <div class="meet-card__info">
            <div class="meet-card__name"><?php echo esc_html( $meet->name ?? 'TBD' ); ?></div>
            <div class="meet-card__details">
                <?php if ( ! empty( $meet->location ) ) : ?><span>📍 <?php echo esc_html( $meet->location ); ?></span><?php endif; ?>
                <?php if ( ! empty( $meet->meet_time ) ) : ?><span>🕐 <?php echo esc_html( $meet->meet_time ); ?></span><?php endif; ?>
                <?php if ( $badge ) : ?><span class="meet-card__badge"><?php echo esc_html( $badge ); ?></span><?php endif; ?>
            </div>
        </div>
    </div>
    <?php
}

/**
 * Output an athlete card placeholder (used when plugin shortcodes aren't available)
 */
function TRACKSUITE_athlete_card_placeholder( string $name, string $events = '', string $division = '' ): void {
    $initials = implode( '', array_map( fn($p) => strtoupper( $p[0] ), explode( ' ', $name ) ) );
    ?>
    <div class="athlete-card" data-division="<?php echo esc_attr( $division ); ?>">
        <div class="athlete-card__photo">
            <div class="athlete-card__photo-placeholder"><?php echo esc_html( $initials ); ?></div>
        </div>
        <div class="athlete-card__body">
            <div class="athlete-card__name"><?php echo esc_html( $name ); ?></div>
            <?php if ( $events ) : ?><div class="athlete-card__details"><?php echo esc_html( $events ); ?></div><?php endif; ?>
        </div>
    </div>
    <?php
}

/**
 * Output a results table row
 */
function TRACKSUITE_result_row( object $result, bool $show_athlete = true ): void {
    $pb_badge = ! empty( $result->is_personal_best ) ? '<span class="pb-badge">PB</span>' : '';
    $cr_badge = ! empty( $result->is_club_record )   ? '<span class="pb-badge cr-badge">CR</span>' : '';
    $place_class = '';
    if ( ! empty( $result->placement ) ) {
        if ( $result->placement == 1 ) $place_class = 'place-1';
        if ( $result->placement == 2 ) $place_class = 'place-2';
        if ( $result->placement == 3 ) $place_class = 'place-3';
    }
    ?>
    <tr class="<?php echo esc_attr( $place_class ); ?>">
        <?php if ( $show_athlete ) : ?><td><?php echo esc_html( $result->athlete_name ?? '—' ); ?></td><?php endif; ?>
        <td><?php echo esc_html( $result->event_category ?? '—' ); ?></td>
        <td><?php echo esc_html( $result->result_value ?? '—' ); ?> <?php echo wp_kses_post( $pb_badge . $cr_badge ); ?></td>
        <td><?php echo ! empty( $result->placement ) ? esc_html( '#' . $result->placement ) : '—'; ?></td>
        <td><?php echo esc_html( $result->meet_name ?? '—' ); ?></td>
        <td><?php echo ! empty( $result->recorded_at ) ? esc_html( date( 'M j, Y', strtotime( $result->recorded_at ) ) ) : '—'; ?></td>
    </tr>
    <?php
}

/**
 * Print pagination
 */
function TRACKSUITE_pagination(): void {
    the_posts_pagination( [
        'mid_size'  => 2,
        'prev_text' => '← Prev',
        'next_text' => 'Next →',
    ] );
}

