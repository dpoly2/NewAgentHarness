<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap ts-admin-wrap">
    <h1 class="ts-page-title">
        <span class="dashicons dashicons-calendar-alt"></span>
        <?php esc_html_e( 'Seasons', 'ts-membership' ); ?>
        <a href="#" class="page-title-action ts-open-modal" data-modal="ts-add-season"><?php esc_html_e( 'Add New Season', 'ts-membership' ); ?></a>
    </h1>

    <?php if ( empty( $list ) ) : ?>
        <p><?php esc_html_e( 'No seasons found. Add your first season above.', 'ts-membership' ); ?></p>
    <?php else : ?>
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th><?php esc_html_e( 'Season', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Type', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Dates', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Registration', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Standard Fee', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Premium Fee', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Status', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Actions', 'ts-membership' ); ?></th>
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
                        <span class="ts-badge ts-badge-active"><?php esc_html_e( 'Active', 'ts-membership' ); ?></span>
                    <?php else : ?>
                        <span class="ts-badge ts-badge-inactive"><?php esc_html_e( 'Inactive', 'ts-membership' ); ?></span>
                    <?php endif; ?>
                </td>
                <td>
                    <a href="#" class="ts-set-active" data-id="<?php echo absint( $season->id ); ?>"><?php esc_html_e( 'Set Active', 'ts-membership' ); ?></a>
                </td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>

