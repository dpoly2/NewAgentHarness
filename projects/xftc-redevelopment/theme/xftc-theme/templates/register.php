<?php
/**
 * Template Name: Registration
 * @package TRACKSUITE_Theme
 */
TRACKSUITE_partial( 'header' );
?>

<div class="portal-header">
    <div class="container">
        <p class="section-header__eyebrow" style="margin-bottom:.25rem">🏃 Join the Club</p>
        <h1 class="portal-header__title">2026 Season Registration</h1>
    </div>
</div>

<section class="section" style="padding-top:1.5rem;">
    <div class="container" style="max-width:860px;">

        <!-- Steps indicator -->
        <div style="display:flex;gap:0;margin-bottom:2rem;border:1px solid var(--ts-gray-200);border-radius:var(--radius-lg);overflow:hidden;">
            <?php
            $steps = [ '1. Account', '2. Athlete Info', '3. Season & Tier', '4. Payment' ];
            foreach ( $steps as $i => $step ) {
                $active = $i === 0 ? 'background:var(--ts-gold);color:var(--ts-black);font-weight:700;' : 'background:var(--ts-gray-100);color:var(--ts-gray-600);';
                echo '<div style="flex:1;padding:.75rem;text-align:center;font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;' . $active . '">' . esc_html( $step ) . '</div>';
            }
            ?>
        </div>

        <?php echo do_shortcode( '[TRACKSUITE_register_form]' ); ?>

    </div>
</section>

<?php TRACKSUITE_partial( 'footer' ); ?>

