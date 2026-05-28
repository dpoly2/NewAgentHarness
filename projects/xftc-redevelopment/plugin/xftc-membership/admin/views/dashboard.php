<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap ts-admin-wrap">
    <h1 class="ts-page-title">
        <span class="dashicons dashicons-groups"></span>
        <?php esc_html_e( 'Xtreme Force Dashboard', 'ts-membership' ); ?>
    </h1>

    <div class="ts-stats-grid">
        <div class="ts-stat-card">
            <div class="ts-stat-number"><?php echo esc_html( $total ); ?></div>
            <div class="ts-stat-label"><?php esc_html_e( 'Total Athletes', 'ts-membership' ); ?></div>
        </div>
        <div class="ts-stat-card">
            <div class="ts-stat-number"><?php echo $active ? esc_html( $active->name ) : '—'; ?></div>
            <div class="ts-stat-label"><?php esc_html_e( 'Active Season', 'ts-membership' ); ?></div>
        </div>
        <div class="ts-stat-card">
            <div class="ts-stat-number">—</div>
            <div class="ts-stat-label"><?php esc_html_e( 'Upcoming Meets', 'ts-membership' ); ?></div>
        </div>
        <div class="ts-stat-card">
            <div class="ts-stat-number">—</div>
            <div class="ts-stat-label"><?php esc_html_e( 'Outstanding Balances', 'ts-membership' ); ?></div>
        </div>
    </div>

    <div class="ts-quick-links">
        <h2><?php esc_html_e( 'Quick Actions', 'ts-membership' ); ?></h2>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=ts-members' ) ); ?>" class="button button-primary"><?php esc_html_e( 'View Members', 'ts-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=ts-seasons' ) ); ?>" class="button"><?php esc_html_e( 'Manage Seasons', 'ts-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=ts-meets' ) ); ?>" class="button"><?php esc_html_e( 'Manage Meets', 'ts-membership' ); ?></a>
        <a href="<?php echo esc_url( admin_url( 'admin.php?page=ts-reports' ) ); ?>" class="button"><?php esc_html_e( 'View Reports', 'ts-membership' ); ?></a>
    </div>
</div>

