<?php defined( 'ABSPATH' ) || exit; ?>
<div class="wrap ts-admin-wrap">
    <h1 class="ts-page-title">
        <span class="dashicons dashicons-admin-users"></span>
        <?php esc_html_e( 'Athletes', 'ts-membership' ); ?>
    </h1>

    <form method="get">
        <input type="hidden" name="page" value="ts-members">
        <p class="search-box">
            <input type="search" name="s" value="<?php echo esc_attr( $search ); ?>" placeholder="<?php esc_attr_e( 'Search athletes...', 'ts-membership' ); ?>">
            <button type="submit" class="button"><?php esc_html_e( 'Search', 'ts-membership' ); ?></button>
        </p>
    </form>

    <?php if ( empty( $list ) ) : ?>
        <p><?php esc_html_e( 'No athletes found.', 'ts-membership' ); ?></p>
    <?php else : ?>
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th><?php esc_html_e( 'ID', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Name', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'DOB', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Gender', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Team Level', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'School', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Emergency Contact', 'ts-membership' ); ?></th>
                <th><?php esc_html_e( 'Registered', 'ts-membership' ); ?></th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ( $list as $athlete ) : ?>
            <tr>
                <td><?php echo absint( $athlete->id ); ?></td>
                <td><strong><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></strong></td>
                <td><?php echo esc_html( $athlete->dob ?? '—' ); ?></td>
                <td><?php echo esc_html( $athlete->gender ?? '—' ); ?></td>
                <td><?php echo esc_html( $athlete->team_level ?? '—' ); ?></td>
                <td><?php echo esc_html( $athlete->school ?? '—' ); ?></td>
                <td><?php echo esc_html( ( $athlete->emergency_contact_name ?? '—' ) . ' ' . ( $athlete->emergency_contact_phone ?? '' ) ); ?></td>
                <td><?php echo esc_html( date( 'M j, Y', strtotime( $athlete->created_at ) ) ); ?></td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
    <?php endif; ?>
</div>

