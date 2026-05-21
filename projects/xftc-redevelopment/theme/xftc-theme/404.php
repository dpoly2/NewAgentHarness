<?php
/**
 * 404 Template
 * @package TRACKSUITE_Theme
 */
TRACKSUITE_partial( 'header' );
?>
<section class="section" style="text-align:center;padding-block:5rem;">
    <div class="container">
        <div style="font-family:var(--font-heading);font-size:8rem;color:var(--ts-gold);line-height:1;">404</div>
        <h1 style="font-family:var(--font-heading);font-size:2.5rem;margin-bottom:1rem;">False Start.</h1>
        <p style="color:var(--ts-gray-600);max-width:420px;margin-inline:auto;margin-bottom:2rem;">
            That page doesn't exist or has moved. Let's get you back on track.
        </p>
        <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="btn btn--primary">🏠 Back to Home</a>
    </div>
</section>
<?php TRACKSUITE_partial( 'footer' ); ?>

