<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap xftc-admin-wrap">
    <h1 class="xftc-page-title">
        <span class="dashicons dashicons-calendar-alt"></span>
        <?php esc_html_e( 'Seasons', 'xftc-membership' ); ?>
        <a href="#" class="page-title-action xftc-open-modal" data-modal="xftc-add-season"><?php esc_html_e( 'Add New Season', 'xftc-membership' ); ?></a>
    </h1>

    <?php if ( empty( $list ) ) : ?>
        <p><?php esc_html_e( 'No seasons found. Add your first season above.', 'xftc-membership' ); ?></p>
    <?php else : ?>
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th><?php esc_html_e( 'Season', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Type', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Dates', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Registration', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Standard Fee', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Premium Fee', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Status', 'xftc-membership' ); ?></th>
                <th><?php esc_html_e( 'Actions', 'xftc-membership' ); ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ( $list as $season ) : ?>
            <tr>
                <td><strong><?php echo esc_html( $season->name ); ?></strong></td>
                <td><?php echo esc_html( ucfirst( $season->type ) ); ?></td>
                <td><?php echo esc_html( ( $season->start_date ?? '—' ) . ' → ' . ( $season->end_date ?? '—' ) ); ?></td>
                <td><?php echo esc_html( ( $season->reg_open ?? '—' ) . ' → ' . ( $season->reg_close ?? '—' ) ); ?></td>
                <td>$<?php echo number_format( (float) $season->fee_standard, 2 ); ?></td>
                <td>$<?php echo number_format( (float) $season->fee_premium, 2 ); ?></td>
                <td>
                    <?php if ( $season->is_active ) : ?>
                        <span class="xftc-badge xftc-badge-active"><?php esc_html_e( 'Active', 'xftc-membership' ); ?></span>
                    <?php else : ?>
                        <span class="xftc-badge xftc-badge-inactive"><?php esc_html_e( 'Inactive', 'xftc-membership' ); ?></span>
                    <?php endif; ?>
                </td>
                <td>
                    <a href="#" class="xftc-set-active" data-id="<?php echo absint( $season->id ); ?>"><?php esc_html_e( 'Set Active', 'xftc-membership' ); ?></a>
                </td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>
