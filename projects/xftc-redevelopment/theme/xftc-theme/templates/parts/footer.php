<?php
/**
 * Site Footer partial
 * @package TRACKSUITE_Theme
 */
$phone     = get_theme_mod( 'TRACKSUITE_phone',     '' );
$email     = get_theme_mod( 'TRACKSUITE_email',     'info@xtremeforcetrackclub.org' );
$address   = get_theme_mod( 'TRACKSUITE_address',   'Austin / Pflugerville, TX' );
$facebook  = get_theme_mod( 'TRACKSUITE_facebook',  '' );
$instagram = get_theme_mod( 'TRACKSUITE_instagram', '' );
$twitter   = get_theme_mod( 'TRACKSUITE_twitter',   '' );
$youtube   = get_theme_mod( 'TRACKSUITE_youtube',   '' );
?>
</main><!-- /.site-main -->

<!-- Sponsor Strip -->
<?php if ( is_active_sidebar( 'sponsor-strip' ) || is_front_page() ) : ?>
<div class="sponsor-strip">
    <div class="container">
        <p class="sponsor-strip__label"><?php esc_html_e( 'Proud Sponsors & Partners', 'ts-theme' ); ?></p>
        <div class="sponsor-strip__logos">
            <?php if ( is_active_sidebar( 'sponsor-strip' ) ) : ?>
                <?php dynamic_sidebar( 'sponsor-strip' ); ?>
            <?php else : ?>
                <span style="font-size:.8rem;color:#999;letter-spacing:.1em">YOUR SPONSORS HERE</span>
            <?php endif; ?>
        </div>
    </div>
</div>
<?php endif; ?>

<!-- Site Footer -->
<footer class="site-footer" role="contentinfo">
    <div class="container">
        <div class="site-footer__grid">

            <!-- Brand column -->
            <div class="footer-brand">
                <?php if ( has_custom_logo() ) : ?>
                    <?php the_custom_logo(); ?>
                <?php else : ?>
                    <div class="site-title" style="font-size:1.3rem;margin-bottom:.75rem;">
                        XTREME <span style="color:var(--ts-gold)">FORCE</span>
                    </div>
                <?php endif; ?>

                <p class="footer-brand__desc">
                    <?php echo esc_html( get_bloginfo( 'description' ) ?: 'Developing champion athletes and future leaders. AAU-registered. Austin & Pflugerville, TX.' ); ?>
                </p>

                <?php if ( $address ) : ?><p style="font-size:.8rem;opacity:.6;margin-top:.5rem;">📍 <?php echo esc_html( $address ); ?></p><?php endif; ?>
                <?php if ( $email ) : ?><p style="font-size:.8rem;opacity:.6;">✉️ <a href="mailto:<?php echo esc_attr($email); ?>" style="color:inherit"><?php echo esc_html($email); ?></a></p><?php endif; ?>
                <?php if ( $phone ) : ?><p style="font-size:.8rem;opacity:.6;">📞 <?php echo esc_html($phone); ?></p><?php endif; ?>

                <!-- Social links -->
                <div class="footer-brand__social">
                    <?php if ($facebook)  : ?><a href="<?php echo esc_url($facebook);  ?>" target="_blank" rel="noopener" aria-label="Facebook">f</a><?php endif; ?>
                    <?php if ($instagram) : ?><a href="<?php echo esc_url($instagram); ?>" target="_blank" rel="noopener" aria-label="Instagram">📷</a><?php endif; ?>
                    <?php if ($twitter)   : ?><a href="<?php echo esc_url($twitter);   ?>" target="_blank" rel="noopener" aria-label="Twitter">𝕏</a><?php endif; ?>
                    <?php if ($youtube)   : ?><a href="<?php echo esc_url($youtube);   ?>" target="_blank" rel="noopener" aria-label="YouTube">▶</a><?php endif; ?>
                </div>
            </div>

            <!-- Footer nav columns -->
            <div class="footer-widget">
                <h4 class="footer-widget__title"><?php esc_html_e( 'Quick Links', 'ts-theme' ); ?></h4>
                <?php
                wp_nav_menu( [
                    'theme_location' => 'footer-1',
                    'container'      => false,
                    'fallback_cb'    => function() {
                        echo '<ul>';
                        $links = [ 'Home' => '/', 'About' => '/about', 'Schedule' => '/schedule', 'Results' => '/results', 'Roster' => '/roster' ];
                        foreach ( $links as $label => $url ) {
                            echo '<li><a href="' . esc_url( home_url( $url ) ) . '">' . esc_html( $label ) . '</a></li>';
                        }
                        echo '</ul>';
                    },
                ] );
                ?>
            </div>

            <div class="footer-widget">
                <h4 class="footer-widget__title"><?php esc_html_e( 'Program', 'ts-theme' ); ?></h4>
                <?php
                wp_nav_menu( [
                    'theme_location' => 'footer-2',
                    'container'      => false,
                    'fallback_cb'    => function() {
                        echo '<ul>';
                        $links = [ 'Register' => '/register', 'Portal' => '/portal', 'Travel' => '/travel', 'Payments' => '/payments', 'FAQ' => '/faq' ];
                        foreach ( $links as $label => $url ) {
                            echo '<li><a href="' . esc_url( home_url( $url ) ) . '">' . esc_html( $label ) . '</a></li>';
                        }
                        echo '</ul>';
                    },
                ] );
                ?>
            </div>

            <div class="footer-widget">
                <h4 class="footer-widget__title"><?php esc_html_e( 'Club', 'ts-theme' ); ?></h4>
                <?php
                wp_nav_menu( [
                    'theme_location' => 'footer-3',
                    'container'      => false,
                    'fallback_cb'    => function() {
                        echo '<ul>';
                        $links = [ 'Coaches' => '/coaches', 'Sponsors' => '/sponsors', 'News' => '/news', 'Contact' => '/contact', 'Privacy Policy' => '/privacy-policy' ];
                        foreach ( $links as $label => $url ) {
                            echo '<li><a href="' . esc_url( home_url( $url ) ) . '">' . esc_html( $label ) . '</a></li>';
                        }
                        echo '</ul>';
                    },
                ] );
                ?>
            </div>

        </div><!-- /.site-footer__grid -->

        <div class="site-footer__bottom">
            <span>
                &copy; <?php echo date( 'Y' ); ?> <?php bloginfo( 'name' ); ?>.
                <?php esc_html_e( 'All rights reserved.', 'ts-theme' ); ?>
            </span>
            <span>
                <?php
                printf(
                    esc_html__( 'Built by %s', 'ts-theme' ),
                    '<a href="https://xtremeforcetrackclub.org" style="color:var(--ts-gold)">XFTC Tech</a>'
                );
                ?>
            </span>
        </div>

    </div>
</footer><!-- /.site-footer -->

</div><!-- /.site-wrapper -->

<?php wp_footer(); ?>
</body>
</html>

