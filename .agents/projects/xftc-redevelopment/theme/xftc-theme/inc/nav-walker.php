<?php
/**
 * Custom Nav Walker — adds CTA class support via CSS class in menu item
 * @package XFTC_Theme
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Nav_Walker extends Walker_Nav_Menu {

    public function start_el( &$output, $data_object, $depth = 0, $args = null, $current_object_id = 0 ) {
        $item = $data_object;

        $indent = ( $depth ) ? str_repeat( "\t", $depth ) : '';
        $classes = empty( $item->classes ) ? [] : (array) $item->classes;
        $classes[] = 'menu-item-' . $item->ID;

        // Check for CTA class
        $is_cta = in_array( 'nav-cta', $classes, true );

        $class_names = join( ' ', apply_filters( 'nav_menu_css_class', array_filter( $classes ), $item, $args, $depth ) );
        $class_names = $class_names ? ' class="' . esc_attr( $class_names ) . '"' : '';

        $id = apply_filters( 'nav_menu_item_id', 'menu-item-' . $item->ID, $item, $args, $depth );
        $id = $id ? ' id="' . esc_attr( $id ) . '"' : '';

        $output .= $indent . '<li' . $id . $class_names . '>';

        $atts = [];
        $atts['title']  = ! empty( $item->attr_title ) ? $item->attr_title : '';
        $atts['target'] = ! empty( $item->target )     ? $item->target     : '';
        $atts['rel']    = ! empty( $item->xfn )        ? $item->xfn        : '';
        $atts['href']   = ! empty( $item->url )        ? $item->url        : '';
        if ( $item->current || $item->current_item_ancestor ) {
            $atts['aria-current'] = 'page';
        }

        $atts = apply_filters( 'nav_menu_link_attributes', $atts, $item, $args, $depth );

        $attributes = '';
        foreach ( $atts as $attr => $value ) {
            if ( ! empty( $value ) ) {
                $value       = ( 'href' === $attr ) ? esc_url( $value ) : esc_attr( $value );
                $attributes .= ' ' . $attr . '="' . $value . '"';
            }
        }

        $item_output = isset( $args->before ) ? $args->before : '';
        $item_output .= '<a' . $attributes . '>';
        $item_output .= ( isset( $args->link_before ) ? $args->link_before : '' ) . apply_filters( 'the_title', $item->title, $item->ID ) . ( isset( $args->link_after ) ? $args->link_after : '' );
        $item_output .= '</a>';
        $item_output .= isset( $args->after ) ? $args->after : '';

        $output .= apply_filters( 'walker_nav_menu_start_el', $item_output, $item, $depth, $args );
    }
}

/**
 * Fallback nav — used when no menu is assigned
 */
function xftc_fallback_nav(): void {
    $links = [
        'Home'     => '/',
        'About'    => '/about',
        'Schedule' => '/schedule',
        'Results'  => '/results',
        'Roster'   => '/roster',
        'Portal'   => '/portal',
        'Register' => '/register',
    ];
    echo '<ul>';
    foreach ( $links as $label => $url ) {
        $class = ( $label === 'Register' ) ? ' class="nav-cta"' : '';
        echo '<li' . $class . '><a href="' . esc_url( home_url( $url ) ) . '">' . esc_html( $label ) . '</a></li>';
    }
    echo '</ul>';
}
