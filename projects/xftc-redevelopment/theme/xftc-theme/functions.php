<?php
/**
 * XFTC Track & Field Theme — functions.php
 *
 * @package TRACKSUITE_Theme
 * @version 1.0.0
 */

defined( 'ABSPATH' ) || exit;

// ─── Constants ────────────────────────────────────────────────────────────────
define( 'TRACKSUITE_THEME_VERSION', '1.0.0' );
define( 'TRACKSUITE_THEME_DIR',     get_template_directory() );
define( 'TRACKSUITE_THEME_URI',     get_template_directory_uri() );

// ─── Theme Support ────────────────────────────────────────────────────────────
function TRACKSUITE_theme_setup() {
    load_theme_textdomain( 'ts-theme', TRACKSUITE_THEME_DIR . '/languages' );

    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', [ 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ] );
    add_theme_support( 'responsive-embeds' );
    add_theme_support( 'wp-block-styles' );
    add_theme_support( 'editor-styles' );
    add_theme_support( 'align-wide' );
    add_theme_support( 'custom-logo', [
        'height'      => 60,
        'width'       => 200,
        'flex-height' => true,
        'flex-width'  => true,
    ] );
    add_theme_support( 'custom-header', [
        'default-image' => '',
        'header-text'   => false,
    ] );

    // Image sizes
    add_image_size( 'ts-hero',    1920, 800,  true );
    add_image_size( 'ts-card',     600, 400,  true );
    add_image_size( 'ts-athlete',  400, 533,  true ); // 3:4 portrait
    add_image_size( 'ts-thumb',    200, 200,  true );

    // Nav menus
    register_nav_menus( [
        'primary'    => __( 'Primary Navigation',  'ts-theme' ),
        'footer-1'   => __( 'Footer Column 1',     'ts-theme' ),
        'footer-2'   => __( 'Footer Column 2',     'ts-theme' ),
        'footer-3'   => __( 'Footer Column 3',     'ts-theme' ),
        'social'     => __( 'Social Links Menu',   'ts-theme' ),
    ] );
}
add_action( 'after_setup_theme', 'TRACKSUITE_theme_setup' );

// ─── Enqueue Scripts & Styles ─────────────────────────────────────────────────
function TRACKSUITE_enqueue_assets() {
    // Google Fonts
    wp_enqueue_style(
        'ts-fonts',
        'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap',
        [],
        null
    );

    // Main stylesheet
    wp_enqueue_style(
        'ts-theme',
        get_stylesheet_uri(),
        [ 'ts-fonts' ],
        TRACKSUITE_THEME_VERSION
    );

    // Main JS
    wp_enqueue_script(
        'ts-theme',
        TRACKSUITE_THEME_URI . '/assets/js/theme.js',
        [ 'jquery' ],
        TRACKSUITE_THEME_VERSION,
        true
    );

    // Pass data to JS
    wp_localize_script( 'ts-theme', 'XFTC', [
        'ajaxUrl'  => admin_url( 'admin-ajax.php' ),
        'nonce'    => wp_create_nonce( 'TRACKSUITE_nonce' ),
        'siteUrl'  => home_url(),
        'themeUri' => TRACKSUITE_THEME_URI,
    ] );

    // Chart.js — only on results/stats pages
    if ( is_page_template( 'templates/results.php' ) || is_page_template( 'templates/portal.php' ) ) {
        wp_enqueue_script( 'chart-js', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js', [], '4.4.0', true );
    }

    // Comment reply
    if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
        wp_enqueue_script( 'comment-reply' );
    }
}
add_action( 'wp_enqueue_scripts', 'TRACKSUITE_enqueue_assets' );

// Editor styles
function TRACKSUITE_editor_styles() {
    add_editor_style( [ 'assets/css/editor.css', 'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap' ] );
}
add_action( 'after_setup_theme', 'TRACKSUITE_editor_styles' );

// ─── Widget Areas ─────────────────────────────────────────────────────────────
function TRACKSUITE_register_widgets() {
    $sidebars = [
        [ 'id' => 'sidebar-primary',  'name' => 'Primary Sidebar' ],
        [ 'id' => 'footer-col-1',     'name' => 'Footer Column 1' ],
        [ 'id' => 'footer-col-2',     'name' => 'Footer Column 2' ],
        [ 'id' => 'footer-col-3',     'name' => 'Footer Column 3' ],
        [ 'id' => 'announcement-bar', 'name' => 'Announcement Bar' ],
    ];
    foreach ( $sidebars as $s ) {
        register_sidebar( [
            'id'            => $s['id'],
            'name'          => $s['name'],
            'before_widget' => '<div class="widget %2$s">',
            'after_widget'  => '</div>',
            'before_title'  => '<h4 class="widget__title">',
            'after_title'   => '</h4>',
        ] );
    }
}
add_action( 'widgets_init', 'TRACKSUITE_register_widgets' );

// ─── Customizer ───────────────────────────────────────────────────────────────
function TRACKSUITE_customizer( $wp_customize ) {
    // ── Brand Panel ──
    $wp_customize->add_panel( 'TRACKSUITE_brand', [ 'title' => 'XFTC Brand Settings', 'priority' => 30 ] );

    // Colors
    $wp_customize->add_section( 'TRACKSUITE_colors', [ 'title' => 'Brand Colors', 'panel' => 'TRACKSUITE_brand' ] );

    $colors = [
        'TRACKSUITE_color_gold'  => [ 'label' => 'Gold Accent',  'default' => '#F5A623' ],
        'TRACKSUITE_color_dark'  => [ 'label' => 'Dark BG',      'default' => '#1A1A2E' ],
        'TRACKSUITE_color_blue'  => [ 'label' => 'Blue Accent',  'default' => '#0F3460' ],
    ];
    foreach ( $colors as $setting => $args ) {
        $wp_customize->add_setting( $setting, [ 'default' => $args['default'], 'sanitize_callback' => 'sanitize_hex_color', 'transport' => 'postMessage' ] );
        $wp_customize->add_control( new WP_Customize_Color_Control( $wp_customize, $setting, [ 'label' => $args['label'], 'section' => 'TRACKSUITE_colors' ] ) );
    }

    // Club info
    $wp_customize->add_section( 'TRACKSUITE_club_info', [ 'title' => 'Club Info', 'panel' => 'TRACKSUITE_brand' ] );
    foreach ( [ 'TRACKSUITE_phone' => 'Phone', 'TRACKSUITE_email' => 'Contact Email', 'TRACKSUITE_address' => 'Address', 'TRACKSUITE_facebook' => 'Facebook URL', 'TRACKSUITE_instagram' => 'Instagram URL', 'TRACKSUITE_twitter' => 'Twitter/X URL', 'TRACKSUITE_youtube' => 'YouTube URL' ] as $s => $l ) {
        $wp_customize->add_setting( $s, [ 'default' => '', 'sanitize_callback' => 'sanitize_text_field' ] );
        $wp_customize->add_control( $s, [ 'label' => $l, 'section' => 'TRACKSUITE_club_info', 'type' => 'text' ] );
    }

    // Hero
    $wp_customize->add_section( 'TRACKSUITE_hero', [ 'title' => 'Homepage Hero', 'panel' => 'TRACKSUITE_brand' ] );
    foreach ( [ 'TRACKSUITE_hero_title' => [ 'label' => 'Hero Title', 'default' => 'Train Hard. Run <em>Fast</em>. Win.' ], 'TRACKSUITE_hero_subtitle' => [ 'label' => 'Hero Subtitle', 'default' => 'Xtreme Force Track Club — developing champion athletes and future leaders in Austin & Pflugerville, TX.' ], 'TRACKSUITE_hero_cta_text' => [ 'label' => 'CTA Button Text', 'default' => 'Register Now' ], 'TRACKSUITE_hero_cta_url' => [ 'label' => 'CTA Button URL', 'default' => '/register' ] ] as $s => $args ) {
        $wp_customize->add_setting( $s, [ 'default' => $args['default'], 'sanitize_callback' => 'wp_kses_post' ] );
        $wp_customize->add_control( $s, [ 'label' => $args['label'], 'section' => 'TRACKSUITE_hero', 'type' => 'text' ] );
    }

    // Stats
    foreach ( [ 'TRACKSUITE_stat_athletes' => '150+', 'TRACKSUITE_stat_meets' => '25+', 'TRACKSUITE_stat_titles' => '40+' ] as $s => $d ) {
        $wp_customize->add_setting( $s, [ 'default' => $d, 'sanitize_callback' => 'sanitize_text_field' ] );
        $wp_customize->add_control( $s, [ 'label' => str_replace( 'TRACKSUITE_stat_', 'Hero Stat: ', $s ), 'section' => 'TRACKSUITE_hero', 'type' => 'text' ] );
    }
}
add_action( 'customize_register', 'TRACKSUITE_customizer' );

// Output customizer CSS variables
function TRACKSUITE_customizer_css() {
    $gold = get_theme_mod( 'TRACKSUITE_color_gold', '#F5A623' );
    $dark = get_theme_mod( 'TRACKSUITE_color_dark', '#1A1A2E' );
    $blue = get_theme_mod( 'TRACKSUITE_color_blue', '#0F3460' );
    echo "<style>:root{--ts-gold:{$gold};--ts-dark:{$dark};--ts-blue:{$blue};}</style>\n";
}
add_action( 'wp_head', 'TRACKSUITE_customizer_css' );

// ─── Template Hierarchy Helpers ───────────────────────────────────────────────

/**
 * Get custom page templates
 */
function TRACKSUITE_get_template( string $name, array $vars = [] ): void {
    $file = TRACKSUITE_THEME_DIR . "/templates/{$name}.php";
    if ( file_exists( $file ) ) {
        extract( $vars, EXTR_SKIP );
        include $file;
    }
}

/**
 * Partial loader
 */
function TRACKSUITE_partial( string $name, array $vars = [] ): void {
    $file = TRACKSUITE_THEME_DIR . "/templates/parts/{$name}.php";
    if ( file_exists( $file ) ) {
        extract( $vars, EXTR_SKIP );
        include $file;
    }
}

// ─── Announcement Bar ─────────────────────────────────────────────────────────
function TRACKSUITE_get_announcements(): array {
    // Check transient cache first
    $cached = get_transient( 'TRACKSUITE_announcements' );
    if ( $cached ) return $cached;

    // Pull from options or plugin if available
    $announcements = [];

    // Plugin integration — upcoming meets
    if ( function_exists( 'TRACKSUITE_get_upcoming_meets' ) ) {
        $meets = TRACKSUITE_get_upcoming_meets( 5 );
        foreach ( $meets as $meet ) {
            $announcements[] = '📍 ' . esc_html( $meet->name ) . ' — ' . date( 'M j', strtotime( $meet->meet_date ) );
        }
    }

    // Fallback
    if ( empty( $announcements ) ) {
        $announcements = [
            '🏃 2026 Outdoor Season registration is now OPEN!',
            '🏆 XFTC athletes — check your meet schedule for upcoming competitions.',
            '📣 New coaching staff announced for the 2026 season.',
        ];
    }

    set_transient( 'TRACKSUITE_announcements', $announcements, 15 * MINUTE_IN_SECONDS );
    return $announcements;
}

// ─── Hero Stats Helper ────────────────────────────────────────────────────────
function TRACKSUITE_get_hero_stats(): array {
    return [
        [ 'number' => get_theme_mod( 'TRACKSUITE_stat_athletes', '150+' ), 'label' => 'Athletes' ],
        [ 'number' => get_theme_mod( 'TRACKSUITE_stat_meets',    '25+'  ), 'label' => 'Meets / Year' ],
        [ 'number' => get_theme_mod( 'TRACKSUITE_stat_titles',   '40+'  ), 'label' => 'Championships' ],
    ];
}

// ─── Excerpt length ───────────────────────────────────────────────────────────
add_filter( 'excerpt_length', fn() => 20 );
add_filter( 'excerpt_more',   fn() => '&hellip;' );

// ─── Body classes ─────────────────────────────────────────────────────────────
function TRACKSUITE_body_classes( array $classes ): array {
    if ( is_singular() ) $classes[] = 'is-singular';
    if ( is_front_page() ) $classes[] = 'is-front-page';
    return $classes;
}
add_filter( 'body_class', 'TRACKSUITE_body_classes' );

// ─── Disable emoji (performance) ─────────────────────────────────────────────
remove_action( 'wp_head',             'print_emoji_detection_script', 7 );
remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
remove_action( 'wp_print_styles',     'print_emoji_styles' );
remove_action( 'admin_print_styles',  'print_emoji_styles' );

// ─── Security tweaks ─────────────────────────────────────────────────────────
remove_action( 'wp_head', 'wp_generator' );
remove_action( 'wp_head', 'wlwmanifest_link' );
remove_action( 'wp_head', 'rsd_link' );

// ─── Include sub-files ────────────────────────────────────────────────────────
require_once TRACKSUITE_THEME_DIR . '/inc/nav-walker.php';
require_once TRACKSUITE_THEME_DIR . '/inc/template-tags.php';

