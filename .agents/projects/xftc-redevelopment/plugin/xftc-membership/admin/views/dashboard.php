<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap xftc-admin-wrap">
    <h1 class="xftc-page-title">
        <span class="dashicons dashicons-groups"></span>
        <?php esc_html_e( 'Xtreme Force Dashboard', 'xftc-membership' ); ?>
    </h1>

    <div class="xftc-stats-grid">
        <div class="xftc-stat-card">
            <div class="xftc-stat-number"><?php echo esc_html( $total ); ?></div>
            <div class="xftc-stat-label"><?php esc_html_e( 'Total Athletes', 'xftc-membership' ); ?></div>
        </div>
        <div class="xftc-stat-card">
            <div class="xftc-stat-number"><?php echo $active ? esc_html( $active->name ) : '—'; ?></div>
            <div class="xftc-stat-label"><?php esc_html_e( 'Active Season', 'xftc-membership' ); ?></div>
        </div>
        <div class="xftc-stat-card">
            <div class="xftc-stat-number">—</div>
            <div class="xftc-stat-label"><?php esc_html_e( 'Upcoming Meets', 'xftc-membership' ); ?></div>
        </div>
        <div class="xftc-stat-card">
            <div class="xftc-stat-number">—</div>
            <div class="xftc-stat-label"><?php esc_html_e( 'Outstanding Balances', 'xftc-membership' ); ?></div>
        </div>
    </div>

    <div class="xftc-quick-links">
        <h2><?php esc_html_e( 'Quick Actions', 'xftc-membership' ); ?></h2>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-members' ) ); ?>" class="button button-primary"><?php esc_html_e( 'View Members', 'xftc-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-seasons' ) ); ?>" class="button"><?php esc_html_e( 'Manage Seasons', 'xftc-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-meets' ) ); ?>" class="button"><?php esc_html_e( 'Manage Meets', 'xftc-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=xftc-reports' ) ); ?>" class="button"><?php esc_html_e( 'View Reports', 'xftc-membership' ); ?></a>
    </div>
</div>
