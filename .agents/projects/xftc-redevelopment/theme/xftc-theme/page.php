<?php
/**
 * Default Page Template
 * @package XFTC_Theme
 */
xftc_partial( 'header' );
?>

<?php xftc_page_title( get_the_category_list( ', ' ), get_the_title() ); ?>

<section class="section">
    <div class="container" style="max-width:860px;">
        <?php while ( have_posts() ) : the_post(); ?>
            <article <?php post_class(); ?>>
                <?php the_content(); ?>
            </article>
        <?php endwhile; ?>
    </div>
</section>

<?php xftc_partial( 'footer' ); ?>
