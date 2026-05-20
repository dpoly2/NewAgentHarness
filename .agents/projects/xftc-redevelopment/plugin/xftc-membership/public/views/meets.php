<?php
/**
 * Public View — Meet Browser & Registration
 * Shortcode: [xftc_meets]
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */
if ( ! defined( 'ABSPATH' ) ) exit;

$meets_mgr = new XFTC_Meets();
$user_id   = get_current_user_id();

// Handle registration
if ( is_user_logged_in() && isset( $_POST['xftc_meet_reg_nonce'] ) && wp_verify_nonce( $_POST['xftc_meet_reg_nonce'], 'xftc_register_meet' ) ) {
    $entry_id = $meets_mgr->register_athlete(
        (int) $_POST['meet_id'],
        (int) $_POST['athlete_id'],
        [ 'event_category' => sanitize_text_field( $_POST['event_category'] ), 'division' => sanitize_text_field( $_POST['division'] ?? '' ) ]
    );
    echo $entry_id
        ? '<div class="xftc-notice xftc-notice-success"><p>✅ Registration confirmed!</p></div>'
        : '<div class="xftc-notice xftc-notice-error"><p>Registration failed or already exists.</p></div>';
}

$upcoming = $meets_mgr->get_upcoming_meets();
?>

<div class="xftc-meets-wrap">
    <h2>Upcoming Meets</h2>

    <?php if ( empty( $upcoming ) ) : ?>
        <div class="xftc-notice xftc-notice-info">
            <p>No upcoming meets scheduled. Check back soon!</p>
        </div>
    <?php else : ?>
        <div class="xftc-meets-grid">
        <?php foreach ( $upcoming as $meet ) :
            $categories = (array) $meet['categories'];
        ?>
            <div class="xftc-meet-card">
                <div class="xftc-meet-header">
                    <h3><?php echo esc_html( $meet['name'] ); ?></h3>
                    <span class="xftc-meet-type xftc-type-<?php echo esc_attr( $meet['type'] ); ?>"><?php echo esc_html( ucfirst( $meet['type'] ) ); ?></span>
                </div>
                <div class="xftc-meet-details">
                    <p>📅 <?php echo esc_html( date( 'l, F j, Y', strtotime( $meet['meet_date'] ) ) ); ?>
                        <?php if ( $meet['meet_time'] ) echo ' at ' . date( 'g:i A', strtotime( $meet['meet_time'] ) ); ?>
                    </p>
                    <p>📍 <?php echo esc_html( $meet['location'] ?: 'Location TBD' ); ?></p>
                    <?php if ( ! empty( $categories ) ) : ?>
                        <p>🏃 Events: <?php echo esc_html( implode( ', ', $categories ) ); ?></p>
                    <?php endif; ?>
                </div>

                <?php if ( is_user_logged_in() ) : ?>
                    <!-- Registration Form -->
                    <div class="xftc-meet-register">
                        <h4>Register an Athlete</h4>
                        <form method="post">
                            <?php wp_nonce_field( 'xftc_register_meet', 'xftc_meet_reg_nonce' ); ?>
                            <input type="hidden" name="meet_id" value="<?php echo $meet['id']; ?>">
                            <div class="xftc-form-row">
                                <label>Athlete:
                                    <select name="athlete_id" required>
                                        <option value="">— Select Athlete —</option>
                                        <?php
                                        // TODO: Load athletes for current parent
                                        // $members = new XFTC_Members();
                                        // $athletes = $members->get_athletes_by_parent( $user_id );
                                        // foreach ( $athletes as $a ) :
                                        //     echo '<option value="' . $a['id'] . '">' . esc_html($a['first_name'] . ' ' . $a['last_name']) . '</option>';
                                        // endforeach;
                                        ?>
                                    </select>
                                </label>
                            </div>
                            <div class="xftc-form-row">
                                <label>Event:
                                    <select name="event_category" required>
                                        <option value="">— Select Event —</option>
                                        <?php foreach ( $categories as $cat ) : ?>
                                            <option value="<?php echo esc_attr( $cat ); ?>"><?php echo esc_html( $cat ); ?></option>
                                        <?php endforeach; ?>
                                    </select>
                                </label>
                            </div>
                            <div class="xftc-form-row">
                                <label>Division: <input type="text" name="division" placeholder="e.g. U10, U14, Open"></label>
                            </div>
                            <button type="submit" class="xftc-btn xftc-btn-primary">Register</button>
                        </form>
                    </div>
                <?php else : ?>
                    <p class="xftc-login-cta"><a href="<?php echo esc_url( wp_login_url( get_permalink() ) ); ?>">Log in</a> to register your athlete.</p>
                <?php endif; ?>
            </div>
        <?php endforeach; ?>
        </div>
    <?php endif; ?>

    <?php if ( is_user_logged_in() ) :
        // TODO: Show athlete's existing meet registrations
    ?>
        <hr>
        <h2>Your Registrations</h2>
        <p class="xftc-muted"><em>Your athlete meet registrations will appear here.</em></p>
    <?php endif; ?>
</div>
