<?php
/**
 * Main template fallback
 * @package XFTC_Theme
 */
xftc_partial( 'header' );
?>

<div class="container" style="padding-block:3rem;">
    <?php if ( have_posts() ) : ?>
        <h1 class="section-header__title" style="font-family:var(--font-heading);font-size:2rem;letter-spacing:.04em;margin-bottom:2rem;">
            <?php
            if ( is_archive() ) the_archive_title();
            elseif ( is_search() ) printf( esc_html__( 'Search: %s', 'xftc-theme' ), get_search_query() );
            else esc_html_e( 'Latest News', 'xftc-theme' );
            ?>
        </h1>
        <div class="grid-3">
            <?php while ( have_posts() ) : the_post(); ?>
                <article <?php post_class( 'card' ); ?>>
                    <?php if ( has_post_thumbnail() ) : ?>
                    <div class="card__image">
                        <a href="<?php the_permalink(); ?>"><?php the_post_thumbnail( 'xftc-card' ); ?></a>
                    </div>
                    <?php endif; ?>
                    <div class="card__body">
                        <span class="card__tag"><?php echo get_the_category_list( ', ' ); ?></span>
                        <h2 class="card__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                        <div class="card__meta">
                            <span><?php echo get_the_date(); ?></span>
                            <span><?php the_author(); ?></span>
                        </div>
                        <?php the_excerpt(); ?>
                    </div>
                </article>
            <?php endwhile; ?>
        </div>
        <?php the_posts_pagination(); ?>
    <?php else : ?>
        <p><?php esc_html_e( 'No content found.', 'xftc-theme' ); ?></p>
    <?php endif; ?>
</div>

<?php xftc_partial( 'footer' ); ?>
