<?php
/**
 * Site Header partial
 * @package XFTC_Theme
 */
$announcements = xftc_get_announcements();
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div class="site-wrapper">

<!-- Announcement Bar -->
<?php if ( ! empty( $announcements ) ) : ?>
<div class="announcement-bar" role="marquee" aria-label="Announcements">
    <span class="announcement-bar__label">📢 News</span>
    <div class="announcement-bar__track">
        <?php
        // Double the items so the loop is seamless
        $items = array_merge( $announcements, $announcements );
        foreach ( $items as $item ) :
        ?>
        <span class="announcement-bar__item"><?php echo wp_kses_post( $item ); ?></span>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<!-- Site Header -->
<header class="site-header" role="banner">
    <div class="container">

        <!-- Logo / Branding -->
        <div class="site-branding">
            <?php if ( has_custom_logo() ) : ?>
                <?php the_custom_logo(); ?>
            <?php else : ?>
                <a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home" class="site-title-link">
                    <div class="site-title">
                        XTREME <span>FORCE</span>
                        <div class="site-tagline">Track Club</div>
                    </div>
                </a>
            <?php endif; ?>
        </div>

        <!-- Primary Nav -->
        <nav class="nav-primary" id="site-navigation" role="navigation" aria-label="<?php esc_attr_e( 'Primary', 'xftc-theme' ); ?>">
            <?php
            wp_nav_menu( [
                'theme_location' => 'primary',
                'menu_class'     => '',
                'container'      => false,
                'walker'         => new XFTC_Nav_Walker(),
                'fallback_cb'    => 'xftc_fallback_nav',
            ] );
            ?>
        </nav>

        <!-- Mobile Toggle -->
        <button class="nav-toggle" aria-controls="site-navigation" aria-expanded="false" aria-label="<?php esc_attr_e( 'Toggle menu', 'xftc-theme' ); ?>">
            <span></span><span></span><span></span>
        </button>

    </div>
</header>

<main class="site-main" id="main">
