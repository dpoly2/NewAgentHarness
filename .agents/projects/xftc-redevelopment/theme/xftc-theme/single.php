<?php
/**
 * Single Post Template
 * @package XFTC_Theme
 */
xftc_partial( 'header' );
?>

<section class="section">
    <div class="container" style="max-width:800px;">
        <?php while ( have_posts() ) : the_post(); ?>
        <article <?php post_class(); ?>>
            <header style="margin-bottom:2rem;">
                <div class="card__tag"><?php echo get_the_category_list( ', ' ); ?></div>
                <h1 style="font-family:var(--font-heading);font-size:2.5rem;letter-spacing:.03em;line-height:1.1;margin-bottom:.75rem;"><?php the_title(); ?></h1>
                <div class="card__meta">
                    <span>By <?php the_author(); ?></span>
                    <span><?php echo get_the_date(); ?></span>
                </div>
            </header>
            <?php if ( has_post_thumbnail() ) : ?>
                <div style="border-radius:var(--radius-lg);overflow:hidden;margin-bottom:2rem;">
                    <?php the_post_thumbnail( 'xftc-hero' ); ?>
                </div>
            <?php endif; ?>
            <div class="entry-content"><?php the_content(); ?></div>
            <footer style="margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--xftc-gray-200);">
                <?php the_tags( '<p>Tags: ', ', ', '</p>' ); ?>
                <?php wp_link_pages(); ?>
            </footer>
        </article>
        <?php endwhile; ?>
    </div>
</section>

<?php xftc_partial( 'footer' ); ?>
