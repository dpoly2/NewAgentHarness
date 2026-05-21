<?php
/**
 * Admin View — Meet Management
 * WP Admin → Xtreme Force → Meets
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

$meets_mgr = new TRACKSUITE_Meets();

// Handle form actions
if ( isset( $_POST['TRACKSUITE_meets_nonce'] ) && wp_verify_nonce( $_POST['TRACKSUITE_meets_nonce'], 'TRACKSUITE_save_meet' ) ) {
    $action = sanitize_key( $_POST['action_type'] ?? 'create' );
    if ( $action === 'create' ) {
        $meets_mgr->create_meet( $_POST );
        echo '<div class="notice notice-success"><p>Meet created.</p></div>';
    } elseif ( $action === 'update' && ! empty( $_POST['meet_id'] ) ) {
        $meets_mgr->update_meet( (int) $_POST['meet_id'], $_POST );
        echo '<div class="notice notice-success"><p>Meet updated.</p></div>';
    }
}
if ( isset( $_GET['status_update'] ) && isset( $_GET['meet_id'] ) ) {
    if ( check_admin_referer( 'TRACKSUITE_meet_status' ) ) {
        $meets_mgr->update_status( (int) $_GET['meet_id'], sanitize_key( $_GET['status_update'] ) );
    }
}
if ( isset( $_GET['export_roster'] ) ) {
    $meets_mgr->export_roster_csv( (int) $_GET['export_roster'] );
}

$meets     = $meets_mgr->get_all_meets();
$edit_meet = ! empty( $_GET['edit_id'] ) ? $meets_mgr->get_meet( (int) $_GET['edit_id'] ) : null;
?>

<div class="wrap ts-admin-meets">
    <h1>🏟️ Meet Management
        <a href="#ts-meet-form" class="page-title-action">+ Add Meet</a>
    </h1>

    <!-- Meet List -->
    <table class="wp-list-table widefat fixed striped">
        <thead>
            <tr>
                <th>Meet Name</th><th>Date</th><th>Location</th><th>Type</th>
                <th>Categories</th><th>Status</th><th>Actions</th>
            </tr>
        </thead>
        <tbody>
        <?php if ( empty( $meets ) ) : ?>
            <tr><td colspan="7" style="text-align:center;padding:20px;"><em>No meets yet. Add one below.</em></td></tr>
        <?php else : foreach ( $meets as $m ) : ?>
            <tr>
                <td><strong><?php echo esc_html( $m['name'] ); ?></strong></td>
                <td><?php echo esc_html( date( 'M j, Y', strtotime( $m['meet_date'] ) ) ); ?></td>
                <td><?php echo esc_html( $m['location'] ); ?></td>
                <td><?php echo esc_html( ucfirst( $m['type'] ) ); ?></td>
                <td><?php echo esc_html( implode( ', ', (array) $m['categories'] ) ); ?></td>
                <td><span class="ts-status ts-status-<?php echo esc_attr( $m['status'] ); ?>"><?php echo esc_html( ucfirst( $m['status'] ) ); ?></span></td>
                <td>
                    <a href="?page=ts-meets&edit_id=<?php echo $m['id']; ?>">Edit</a> |
                    <a href="?page=ts-meets&meet_id=<?php echo $m['id']; ?>&status_update=active&<?php echo wp_create_nonce( 'TRACKSUITE_meet_status' ); ?>">Activate</a> |
                    <a href="?page=ts-meets&meet_id=<?php echo $m['id']; ?>&status_update=completed&<?php echo wp_create_nonce( 'TRACKSUITE_meet_status' ); ?>">Complete</a> |
                    <a href="?page=ts-meets&export_roster=<?php echo $m['id']; ?>">Export Roster</a>
                </td>
            </tr>
        <?php endforeach; endif; ?>
        </tbody>
    </table>

    <hr id="ts-meet-form">

    <!-- Create / Edit Form -->
    <h2><?php echo $edit_meet ? 'Edit Meet' : 'Add New Meet'; ?></h2>
    <form method="post">
        <?php wp_nonce_field( 'TRACKSUITE_save_meet', 'TRACKSUITE_meets_nonce' ); ?>
        <input type="hidden" name="action_type" value="<?php echo $edit_meet ? 'update' : 'create'; ?>">
        <?php if ( $edit_meet ) : ?>
            <input type="hidden" name="meet_id" value="<?php echo $edit_meet['id']; ?>">
        <?php endif; ?>
        <table class="form-table">
            <tr>
                <th><label>Meet Name</label></th>
                <td><input type="text" name="name" class="regular-text" required value="<?php echo esc_attr( $edit_meet['name'] ?? '' ); ?>"></td>
            </tr>
            <tr>
                <th><label>Date</label></th>
                <td><input type="date" name="meet_date" required value="<?php echo esc_attr( $edit_meet['meet_date'] ?? '' ); ?>"></td>
            </tr>
            <tr>
                <th><label>Time</label></th>
                <td><input type="time" name="meet_time" value="<?php echo esc_attr( $edit_meet['meet_time'] ?? '' ); ?>"></td>
            </tr>
            <tr>
                <th><label>Location</label></th>
                <td><input type="text" name="location" class="regular-text" value="<?php echo esc_attr( $edit_meet['location'] ?? '' ); ?>"></td>
            </tr>
            <tr>
                <th><label>Type</label></th>
                <td>
                    <select name="type">
                        <?php foreach ( ['practice','competitive','invitational'] as $t ) : ?>
                            <option value="<?php echo $t; ?>" <?php selected( $edit_meet['type'] ?? '', $t ); ?>><?php echo ucfirst( $t ); ?></option>
                        <?php endforeach; ?>
                    </select>
                </td>
            </tr>
            <tr>
                <th><label>Event Categories</label></th>
                <td>
                    <?php
                    $cats = ['Sprints','Hurdles','Distance','Field','Relays','Multi'];
                    $selected_cats = (array) ( $edit_meet['categories'] ?? [] );
                    foreach ( $cats as $cat ) : ?>
                        <label style="margin-right:16px;">
                            <input type="checkbox" name="categories[]" value="<?php echo $cat; ?>"
                                <?php checked( in_array( $cat, $selected_cats ) ); ?>>
                            <?php echo $cat; ?>
                        </label>
                    <?php endforeach; ?>
                </td>
            </tr>
        </table>
        <?php submit_button( $edit_meet ? 'Update Meet' : 'Create Meet' ); ?>
    </form>
</div>

