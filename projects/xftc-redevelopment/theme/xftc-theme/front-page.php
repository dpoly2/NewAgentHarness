<?php
/**
 * Front Page Template
 * @package XFTC_Theme
 */
xftc_partial( 'header' );

$hero_title    = get_theme_mod( 'xftc_hero_title',    'Train Hard. Run <em>Fast</em>. Win.' );
$hero_subtitle = get_theme_mod( 'xftc_hero_subtitle', 'Xtreme Force Track Club — developing champion athletes and future leaders in Austin &amp; Pflugerville, TX.' );
$hero_cta_text = get_theme_mod( 'xftc_hero_cta_text', 'Register for 2026' );
$hero_cta_url  = get_theme_mod( 'xftc_hero_cta_url',  home_url( '/register' ) );
$stats         = xftc_get_hero_stats();
?>

<!-- ═══ HERO ═══ -->
<section class="hero">
    <?php if ( get_header_image() ) : ?>
        <img src="<?php header_image(); ?>" alt="" class="hero__bg-img" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;">
    <?php endif; ?>

    <div class="container hero__content">
        <p class="hero__eyebrow">Austin &bull; Pflugerville &bull; Texas &bull; AAU Registered</p>
        <h1 class="hero__title"><?php echo wp_kses_post( $hero_title ); ?></h1>
        <p class="hero__subtitle"><?php echo wp_kses_post( $hero_subtitle ); ?></p>
        <div class="hero__actions">
            <a href="<?php echo esc_url( $hero_cta_url ); ?>" class="btn btn--primary">
                🏃 <?php echo esc_html( $hero_cta_text ); ?>
            </a>
            <a href="<?php echo esc_url( home_url( '/schedule' ) ); ?>" class="btn btn--outline">
                📅 View Schedule
            </a>
        </div>
    </div>

    <!-- Hero stats -->
    <div class="hero__stats">
        <?php foreach ( $stats as $stat ) : ?>
        <div class="hero__stat">
            <div class="hero__stat-number"><?php echo esc_html( $stat['number'] ); ?></div>
            <div class="hero__stat-label"><?php echo esc_html( $stat['label'] ); ?></div>
        </div>
        <?php endforeach; ?>
    </div>

    <div class="hero__track-line"></div>
</section>

<!-- ═══ UPCOMING MEETS ═══ -->
<section class="section section--gray">
    <div class="container">
        <div class="section-header">
            <p class="section-header__eyebrow">On Deck</p>
            <h2 class="section-header__title">Upcoming Meets</h2>
            <div class="section-header__divider"></div>
        </div>
        <?php echo do_shortcode( '[xftc_meets limit="4" view="cards"]' ); ?>
        <div class="text-center mt-3">
            <a href="<?php echo esc_url( home_url( '/schedule' ) ); ?>" class="btn btn--blue">Full Schedule →</a>
        </div>
    </div>
</section>

<!-- ═══ RECENT RESULTS ═══ -->
<section class="section section--dark">
    <div class="container">
        <div class="section-header">
            <p class="section-header__eyebrow">Performance</p>
            <h2 class="section-header__title" style="color:var(--xftc-white)">Latest Results</h2>
            <div class="section-header__divider"></div>
        </div>
        <?php echo do_shortcode( '[xftc_results limit="5" highlight_pb="true"]' ); ?>
        <div class="text-center mt-3">
            <a href="<?php echo esc_url( home_url( '/results' ) ); ?>" class="btn btn--primary">All Results →</a>
        </div>
    </div>
</section>

<!-- ═══ ATHLETE SPOTLIGHT / ROSTER ═══ -->
<section class="section">
    <div class="container">
        <div class="section-header">
            <p class="section-header__eyebrow">The Team</p>
            <h2 class="section-header__title">Meet Our Athletes</h2>
            <div class="section-header__divider"></div>
        </div>
        <?php echo do_shortcode( '[xftc_roster limit="8" view="cards" show_stats="true"]' ); ?>
        <div class="text-center mt-3">
            <a href="<?php echo esc_url( home_url( '/roster' ) ); ?>" class="btn btn--blue">Full Roster →</a>
        </div>
    </div>
</section>

<!-- ═══ REGISTRATION CTA BANNER ═══ -->
<section class="section section--dark" style="padding-block:2rem;">
    <div class="container" style="display:flex;align-items:center;justify-content:space-between;gap:1.5rem;flex-wrap:wrap;">
        <div>
            <h2 style="font-family:var(--font-heading);font-size:2rem;color:var(--xftc-white);letter-spacing:.04em;">
                Ready to Join <span style="color:var(--xftc-gold)">Xtreme Force?</span>
            </h2>
            <p style="color:var(--xftc-gray-300);font-size:.95rem;">
                Open registration — ages 6–18. Competitive and development divisions available.
            </p>
        </div>
        <a href="<?php echo esc_url( home_url( '/register' ) ); ?>" class="btn btn--primary" style="font-size:1rem;padding:1rem 2.5rem;">
            🏃 Register Now
        </a>
    </div>
</section>

<!-- ═══ NEWS / BLOG ═══ -->
<?php
$recent_posts = get_posts( [ 'numberposts' => 3, 'post_status' => 'publish' ] );
if ( ! empty( $recent_posts ) ) :
?>
<section class="section section--gray">
    <div class="container">
        <div class="section-header">
            <p class="section-header__eyebrow">Club News</p>
            <h2 class="section-header__title">Latest Updates</h2>
            <div class="section-header__divider"></div>
        </div>
        <div class="grid-3">
            <?php foreach ( $recent_posts as $post ) : setup_postdata( $post ); ?>
            <article class="card">
                <?php if ( has_post_thumbnail() ) : ?>
                <div class="card__image">
                    <a href="<?php the_permalink(); ?>"><?php the_post_thumbnail( 'xftc-card' ); ?></a>
                </div>
                <?php endif; ?>
                <div class="card__body">
                    <span class="card__tag"><?php echo get_the_category_list( ', ' ); ?></span>
                    <h3 class="card__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
                    <div class="card__meta"><span><?php echo get_the_date(); ?></span></div>
                    <?php the_excerpt(); ?>
                </div>
            </article>
            <?php endforeach; wp_reset_postdata(); ?>
        </div>
    </div>
</section>
<?php endif; ?>

<?php xftc_partial( 'footer' ); ?>
