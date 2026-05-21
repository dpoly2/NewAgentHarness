<?php
/**
 * Front-end shortcodes, AJAX handlers, and public-facing hooks.
 *
 * Shortcodes registered:
 *  [xftc_meets]            — Upcoming meets list or card grid
 *  [xftc_schedule]         — Full season schedule with filters
 *  [xftc_results]          — Meet results table
 *  [xftc_club_records]     — Club records table
 *  [xftc_leaderboard]      — Season leaderboard
 *  [xftc_roster]           — Athlete roster cards or list
 *  [xftc_register_form]    — Multi-step registration form
 *  [xftc_login_form]       — Login form with redirect
 *  [xftc_my_athletes]      — Portal: logged-in parent's athletes
 *  [xftc_my_schedule]      — Portal: athlete schedules + meet sign-up
 *  [xftc_my_results]       — Portal: athlete results with chart
 *  [xftc_my_payments]      — Portal: payment history + receipts
 *  [xftc_my_travel]        — Portal: travel bookings
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Public {

    public function init(): void {
        // ── Shortcodes ──────────────────────────────────────────────────────
        $shortcodes = [
            'xftc_meets'         => 'shortcode_meets',
            'xftc_schedule'      => 'shortcode_schedule',
            'xftc_results'       => 'shortcode_results',
            'xftc_club_records'  => 'shortcode_club_records',
            'xftc_leaderboard'   => 'shortcode_leaderboard',
            'xftc_roster'        => 'shortcode_roster',
            'xftc_register_form' => 'shortcode_register_form',
            'xftc_login_form'    => 'shortcode_login_form',
            'xftc_my_athletes'   => 'shortcode_my_athletes',
            'xftc_my_schedule'   => 'shortcode_my_schedule',
            'xftc_my_results'    => 'shortcode_my_results',
            'xftc_my_payments'   => 'shortcode_my_payments',
            'xftc_my_travel'     => 'shortcode_my_travel',
            // Legacy aliases (Sprint 1)
            'xftc_register'      => 'shortcode_register_form',
            'xftc_portal'        => 'shortcode_my_athletes',
        ];
        foreach ( $shortcodes as $tag => $method ) {
            add_shortcode( $tag, [ $this, $method ] );
        }

        // ── AJAX ────────────────────────────────────────────────────────────
        $ajax_actions = [
            'xftc_register_athlete'    => 'ajax_register_athlete',
            'xftc_register_for_meet'   => 'ajax_register_for_meet',
            'xftc_login'               => 'ajax_login',
            'xftc_get_chart_data'      => 'ajax_get_chart_data',
        ];
        foreach ( $ajax_actions as $action => $method ) {
            add_action( "wp_ajax_{$action}",        [ $this, $method ] );
            add_action( "wp_ajax_nopriv_{$action}", [ $this, $method ] );
        }

        add_action( 'wp_enqueue_scripts', [ $this, 'enqueue_assets' ] );
    }

    // ═══════════════════════════════════════════════════════════════════════
    // ASSETS
    // ═══════════════════════════════════════════════════════════════════════

    public function enqueue_assets(): void {
        wp_enqueue_style(
            'xftc-public',
            XFTC_PLUGIN_URL . 'public/assets/public.css',
            [],
            XFTC_VERSION
        );
        wp_enqueue_script(
            'xftc-public',
            XFTC_PLUGIN_URL . 'public/assets/public.js',
            [ 'jquery' ],
            XFTC_VERSION,
            true
        );
        wp_localize_script( 'xftc-public', 'xftcPublic', [
            'ajaxUrl'       => admin_url( 'admin-ajax.php' ),
            'nonce'         => wp_create_nonce( 'xftc_public_nonce' ),
            'isLoggedIn'    => is_user_logged_in(),
            'portalUrl'     => home_url( '/portal' ),
            'registerUrl'   => home_url( '/register' ),
        ] );
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_meets]
    // Attrs: limit (int), view (cards|list), status (upcoming|all)
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_meets( array $atts ): string {
        $atts = shortcode_atts( [
            'limit'  => 4,
            'view'   => 'cards',
            'status' => 'upcoming',
        ], $atts, 'xftc_meets' );

        $meets_obj = new XFTC_Meets();
        $meets = $atts['status'] === 'upcoming'
            ? $meets_obj->get_upcoming_meets()
            : $meets_obj->get_all_meets();
        $meets = array_slice( $meets, 0, (int) $atts['limit'] );

        if ( empty( $meets ) ) {
            return '<p class="xftc-empty">No upcoming meets scheduled. Check back soon!</p>';
        }

        ob_start();
        $view = sanitize_key( $atts['view'] );
        include XFTC_PLUGIN_DIR . "public/views/meets.php";
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_schedule]
    // Attrs: show_filters (true|false), show_register (true|false)
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_schedule( array $atts ): string {
        $atts = shortcode_atts( [
            'show_filters'  => 'true',
            'show_register' => 'false',
        ], $atts, 'xftc_schedule' );

        $meets_obj = new XFTC_Meets();
        $all_meets = $meets_obj->get_all_meets();

        // Group by month
        $by_month = [];
        foreach ( $all_meets as $meet ) {
            $key = date( 'Y-m', strtotime( $meet['meet_date'] ) );
            $by_month[ $key ][] = $meet;
        }
        ksort( $by_month );

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/meets.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_results]
    // Attrs: limit, meet_id, highlight_pb, highlight_cr, show_filters, view
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_results( array $atts ): string {
        $atts = shortcode_atts( [
            'limit'        => 10,
            'meet_id'      => 0,
            'highlight_pb' => 'true',
            'highlight_cr' => 'true',
            'show_filters' => 'false',
            'view'         => 'table',
        ], $atts, 'xftc_results' );

        $results_obj = new XFTC_Results();

        if ( (int) $atts['meet_id'] > 0 ) {
            $results = $results_obj->get_meet_results( (int) $atts['meet_id'] );
        } else {
            // Get recent results across all meets
            global $wpdb;
            $results_table  = $wpdb->prefix . 'xftc_results';
            $athletes_table = $wpdb->prefix . 'xftc_athletes';
            $meets_table    = $wpdb->prefix . 'xftc_meets';
            $limit          = (int) $atts['limit'];
            $results = $wpdb->get_results(
                $wpdb->prepare(
                    "SELECT r.*, CONCAT(a.first_name,' ',a.last_name) AS athlete_name,
                            a.team_level, m.name AS meet_name, m.meet_date
                     FROM {$results_table} r
                     JOIN {$athletes_table} a ON r.athlete_id = a.id
                     JOIN {$meets_table} m ON r.meet_id = m.id
                     ORDER BY r.recorded_at DESC
                     LIMIT %d",
                    $limit
                ),
                ARRAY_A
            ) ?: [];
        }

        if ( empty( $results ) ) {
            return '<p class="xftc-empty">No results recorded yet.</p>';
        }

        $show_pb = $atts['highlight_pb'] === 'true';
        $show_cr = $atts['highlight_cr'] === 'true';

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/results.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_club_records]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_club_records( array $atts ): string {
        $results_obj = new XFTC_Results();
        $records     = $results_obj->get_club_records();

        if ( empty( $records ) ) {
            return '<p class="xftc-empty">No club records on file yet.</p>';
        }

        ob_start(); ?>
        <div class="xftc-records-wrap">
            <div class="xftc-table-wrap">
                <table class="xftc-table xftc-results-table">
                    <thead>
                        <tr>
                            <th>Event</th>
                            <th>Record</th>
                            <th>Athlete</th>
                            <th>Meet</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                    <?php foreach ( $records as $r ) : ?>
                        <tr>
                            <td><strong><?php echo esc_html( $r['event_category'] ); ?></strong></td>
                            <td class="xftc-result-val">
                                <?php echo esc_html( $r['result_value'] ); ?>
                                <span class="xftc-badge xftc-badge--cr">CR</span>
                            </td>
                            <td><?php echo esc_html( $r['first_name'] . ' ' . $r['last_name'] ); ?></td>
                            <td><?php echo esc_html( $r['meet_name'] ?? '—' ); ?></td>
                            <td><?php echo ! empty( $r['meet_date'] ) ? esc_html( date( 'M j, Y', strtotime( $r['meet_date'] ) ) ) : '—'; ?></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_leaderboard]
    // Attrs: season (current|all), limit
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_leaderboard( array $atts ): string {
        $atts = shortcode_atts( [
            'season' => 'current',
            'limit'  => 20,
        ], $atts, 'xftc_leaderboard' );

        global $wpdb;
        $results_table  = $wpdb->prefix . 'xftc_results';
        $athletes_table = $wpdb->prefix . 'xftc_athletes';
        $limit          = (int) $atts['limit'];

        // Rank by number of PBs and top placements
        $rows = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT a.first_name, a.last_name, a.team_level,
                        COUNT(r.id) AS total_results,
                        SUM(r.is_personal_best) AS pb_count,
                        SUM(CASE WHEN r.placement = 1 THEN 1 ELSE 0 END) AS gold,
                        SUM(CASE WHEN r.placement = 2 THEN 1 ELSE 0 END) AS silver,
                        SUM(CASE WHEN r.placement = 3 THEN 1 ELSE 0 END) AS bronze
                 FROM {$results_table} r
                 JOIN {$athletes_table} a ON r.athlete_id = a.id
                 GROUP BY r.athlete_id
                 ORDER BY gold DESC, silver DESC, bronze DESC, pb_count DESC
                 LIMIT %d",
                $limit
            ),
            ARRAY_A
        ) ?: [];

        if ( empty( $rows ) ) {
            return '<p class="xftc-empty">Season leaderboard will appear once results are entered.</p>';
        }

        ob_start(); ?>
        <div class="xftc-leaderboard">
            <div class="xftc-table-wrap">
                <table class="xftc-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Athlete</th>
                            <th>Level</th>
                            <th>🥇</th>
                            <th>🥈</th>
                            <th>🥉</th>
                            <th>PBs</th>
                        </tr>
                    </thead>
                    <tbody>
                    <?php foreach ( $rows as $i => $r ) : ?>
                        <tr class="<?php echo $i < 3 ? 'xftc-top-' . ( $i + 1 ) : ''; ?>">
                            <td><strong><?php echo $i + 1; ?></strong></td>
                            <td><?php echo esc_html( $r['first_name'] . ' ' . $r['last_name'] ); ?></td>
                            <td><?php echo esc_html( $r['team_level'] ?? '—' ); ?></td>
                            <td><?php echo (int) $r['gold']; ?></td>
                            <td><?php echo (int) $r['silver']; ?></td>
                            <td><?php echo (int) $r['bronze']; ?></td>
                            <td><?php echo (int) $r['pb_count']; ?></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
        <?php
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_roster]
    // Attrs: limit, view (cards|list), show_stats, show_events
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_roster( array $atts ): string {
        $atts = shortcode_atts( [
            'limit'       => 50,
            'view'        => 'cards',
            'show_stats'  => 'false',
            'show_events' => 'false',
        ], $atts, 'xftc_roster' );

        $members_obj = new XFTC_Members();
        $athletes    = $members_obj->get_all( [ 'limit' => (int) $atts['limit'] ] );

        if ( empty( $athletes ) ) {
            return '<p class="xftc-empty">Roster coming soon!</p>';
        }

        $view       = sanitize_key( $atts['view'] );
        $show_stats = $atts['show_stats'] === 'true';

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/portal.php';  // roster section
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_register_form]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_register_form( array $atts ): string {
        if ( is_user_logged_in() ) {
            return '<div class="xftc-notice xftc-notice--info">You\'re logged in! <a href="' . esc_url( home_url( '/portal' ) ) . '">Go to your portal →</a></div>';
        }
        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/register.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_login_form]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_login_form( array $atts ): string {
        if ( is_user_logged_in() ) {
            return '<div class="xftc-notice xftc-notice--info">You\'re already logged in. <a href="' . esc_url( home_url( '/portal' ) ) . '">Go to your portal →</a></div>';
        }
        $redirect = ! empty( $atts['redirect'] ) ? esc_url( $atts['redirect'] ) : home_url( '/portal' );
        ob_start(); ?>
        <div class="xftc-login-wrap">
            <form class="xftc-form xftc-login-form" id="xftc-login-form" novalidate>
                <?php wp_nonce_field( 'xftc_public_nonce', 'xftc_nonce' ); ?>
                <input type="hidden" name="action" value="xftc_login">
                <input type="hidden" name="redirect" value="<?php echo esc_attr( $redirect ); ?>">

                <div class="xftc-form__group">
                    <label for="xftc-login-email"><?php esc_html_e( 'Email', 'xftc-membership' ); ?></label>
                    <input type="email" id="xftc-login-email" name="email" required placeholder="parent@email.com">
                </div>
                <div class="xftc-form__group">
                    <label for="xftc-login-password"><?php esc_html_e( 'Password', 'xftc-membership' ); ?></label>
                    <input type="password" id="xftc-login-password" name="password" required>
                </div>

                <div class="xftc-form__actions">
                    <button type="submit" class="xftc-btn xftc-btn--primary"><?php esc_html_e( 'Log In', 'xftc-membership' ); ?></button>
                    <a href="<?php echo esc_url( wp_lostpassword_url() ); ?>" class="xftc-link"><?php esc_html_e( 'Forgot password?', 'xftc-membership' ); ?></a>
                </div>
                <div class="xftc-form__feedback" aria-live="polite"></div>
            </form>
        </div>
        <?php
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_my_athletes]  — Portal: athlete list for logged-in parent
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_my_athletes( array $atts ): string {
        if ( ! is_user_logged_in() ) {
            return $this->login_prompt();
        }
        $user     = wp_get_current_user();
        $members  = new XFTC_Members();
        $athletes = $members->get_by_parent( $user->ID );
        $seasons  = new XFTC_Seasons();
        $active   = $seasons->get_active();

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/portal.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_my_schedule]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_my_schedule( array $atts ): string {
        if ( ! is_user_logged_in() ) return $this->login_prompt();
        $atts = shortcode_atts( [ 'show_register' => 'true' ], $atts );

        $user     = wp_get_current_user();
        $members  = new XFTC_Members();
        $athletes = $members->get_by_parent( $user->ID );
        $meets_obj = new XFTC_Meets();
        $upcoming  = $meets_obj->get_upcoming_meets();

        // Get athlete meet entries
        $athlete_meets = [];
        foreach ( $athletes as $athlete ) {
            $athlete_meets[ $athlete->id ] = $meets_obj->get_athlete_meets( (int) $athlete->id );
        }

        ob_start();
        $show_register = $atts['show_register'] === 'true';
        include XFTC_PLUGIN_DIR . 'public/views/meets.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_my_results]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_my_results( array $atts ): string {
        if ( ! is_user_logged_in() ) return $this->login_prompt();
        $atts = shortcode_atts( [ 'show_chart' => 'true' ], $atts );

        $user       = wp_get_current_user();
        $members    = new XFTC_Members();
        $athletes   = $members->get_by_parent( $user->ID );
        $results_obj = new XFTC_Results();

        $all_results = [];
        $chart_data  = [];
        foreach ( $athletes as $athlete ) {
            $r = $results_obj->get_athlete_results( (int) $athlete->id );
            foreach ( $r as &$row ) {
                $row['athlete_name'] = $athlete->first_name . ' ' . $athlete->last_name;
            }
            $all_results = array_merge( $all_results, $r );

            // Build chart data for first athlete's most recent event
            if ( empty( $chart_data ) ) {
                $events = $results_obj->get_athlete_events( (int) $athlete->id );
                if ( ! empty( $events ) ) {
                    $chart_data = $results_obj->get_progression_chart_data( (int) $athlete->id, $events[0] );
                }
            }
        }

        $show_pb   = true;
        $show_cr   = false;
        $results   = $all_results;
        $show_chart = $atts['show_chart'] === 'true';

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/results.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_my_payments]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_my_payments( array $atts ): string {
        if ( ! is_user_logged_in() ) return $this->login_prompt();
        $atts = shortcode_atts( [ 'show_receipts' => 'true' ], $atts );

        global $wpdb;
        $payments_table = $wpdb->prefix . 'xftc_payments';
        $user_id        = get_current_user_id();

        $payments = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM {$payments_table} WHERE user_id = %d ORDER BY created_at DESC",
                $user_id
            ),
            ARRAY_A
        ) ?: [];

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/receipts.php';
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTCODE: [xftc_my_travel]
    // ═══════════════════════════════════════════════════════════════════════

    public function shortcode_my_travel( array $atts ): string {
        if ( ! is_user_logged_in() ) return $this->login_prompt();

        $user    = wp_get_current_user();
        $members = new XFTC_Members();
        $athletes = $members->get_by_parent( $user->ID );

        global $wpdb;
        $travel_table = $wpdb->prefix . 'xftc_travel';
        $meets_table  = $wpdb->prefix . 'xftc_meets';

        $travel = [];
        foreach ( $athletes as $athlete ) {
            $rows = $wpdb->get_results(
                $wpdb->prepare(
                    "SELECT t.*, m.name AS meet_name, m.meet_date, m.location
                     FROM {$travel_table} t
                     JOIN {$meets_table} m ON t.meet_id = m.id
                     WHERE t.athlete_id = %d
                     ORDER BY m.meet_date DESC",
                    $athlete->id
                ),
                ARRAY_A
            ) ?: [];
            foreach ( $rows as &$row ) {
                $row['athlete_name'] = $athlete->first_name . ' ' . $athlete->last_name;
            }
            $travel = array_merge( $travel, $rows );
        }

        ob_start();
        include XFTC_PLUGIN_DIR . 'public/views/receipts.php'; // travel section
        return ob_get_clean();
    }

    // ═══════════════════════════════════════════════════════════════════════
    // AJAX HANDLERS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * AJAX: Log in a parent/athlete
     */
    public function ajax_login(): void {
        check_ajax_referer( 'xftc_public_nonce', 'xftc_nonce' );

        $email    = sanitize_email( $_POST['email'] ?? '' );
        $password = $_POST['password'] ?? '';
        $redirect = esc_url_raw( $_POST['redirect'] ?? home_url( '/portal' ) );

        if ( ! $email || ! $password ) {
            wp_send_json_error( [ 'message' => __( 'Email and password are required.', 'xftc-membership' ) ] );
        }

        $user = get_user_by( 'email', $email );
        if ( ! $user ) {
            wp_send_json_error( [ 'message' => __( 'No account found with that email.', 'xftc-membership' ) ] );
        }

        $result = wp_signon( [
            'user_login'    => $user->user_login,
            'user_password' => $password,
            'remember'      => true,
        ], is_ssl() );

        if ( is_wp_error( $result ) ) {
            wp_send_json_error( [ 'message' => __( 'Invalid password. Please try again.', 'xftc-membership' ) ] );
        }

        wp_send_json_success( [ 'redirect' => $redirect ] );
    }

    /**
     * AJAX: Register a new parent account + athlete profile
     */
    public function ajax_register_athlete(): void {
        check_ajax_referer( 'xftc_public_nonce', 'xftc_nonce' );

        $required = [ 'parent_email', 'parent_first', 'parent_last', 'password', 'athlete_first', 'athlete_last' ];
        foreach ( $required as $field ) {
            if ( empty( $_POST[ $field ] ) ) {
                wp_send_json_error( [ 'message' => sprintf( __( 'Missing required field: %s', 'xftc-membership' ), $field ) ] );
            }
        }

        $email = sanitize_email( $_POST['parent_email'] );
        if ( email_exists( $email ) ) {
            wp_send_json_error( [ 'message' => __( 'An account with this email already exists. Please log in.', 'xftc-membership' ) ] );
        }

        // Create WP user
        $user_id = wp_create_user(
            $email,
            sanitize_text_field( $_POST['password'] ),
            $email
        );

        if ( is_wp_error( $user_id ) ) {
            wp_send_json_error( [ 'message' => $user_id->get_error_message() ] );
        }

        // Update display name and role
        wp_update_user( [
            'ID'           => $user_id,
            'first_name'   => sanitize_text_field( $_POST['parent_first'] ),
            'last_name'    => sanitize_text_field( $_POST['parent_last'] ),
            'display_name' => sanitize_text_field( $_POST['parent_first'] . ' ' . $_POST['parent_last'] ),
            'role'         => 'xftc_parent',
        ] );

        // Create athlete record
        $members = new XFTC_Members();
        $athlete_id = $members->create( [
            'parent_id'               => $user_id,
            'first_name'              => sanitize_text_field( $_POST['athlete_first'] ),
            'last_name'               => sanitize_text_field( $_POST['athlete_last'] ),
            'dob'                     => sanitize_text_field( $_POST['dob'] ?? '' ),
            'gender'                  => sanitize_text_field( $_POST['gender'] ?? '' ),
            'team_level'              => sanitize_text_field( $_POST['team_level'] ?? '' ),
            'school'                  => sanitize_text_field( $_POST['school'] ?? '' ),
            'emergency_contact_name'  => sanitize_text_field( $_POST['emergency_name'] ?? '' ),
            'emergency_contact_phone' => sanitize_text_field( $_POST['emergency_phone'] ?? '' ),
        ] );

        if ( is_wp_error( $athlete_id ) ) {
            wp_send_json_error( [ 'message' => $athlete_id->get_error_message() ] );
        }

        // Auto log in
        wp_set_current_user( $user_id );
        wp_set_auth_cookie( $user_id, true );

        // Send welcome email
        if ( class_exists( 'XFTC_Emails' ) ) {
            $emails = new XFTC_Emails();
            $emails->send_parent_welcome( $user_id );
        }

        wp_send_json_success( [
            'message'  => __( 'Welcome to Xtreme Force! Redirecting to your portal…', 'xftc-membership' ),
            'redirect' => home_url( '/portal' ),
        ] );
    }

    /**
     * AJAX: Register an athlete for a specific meet
     */
    public function ajax_register_for_meet(): void {
        check_ajax_referer( 'xftc_public_nonce', 'xftc_nonce' );

        if ( ! is_user_logged_in() ) {
            wp_send_json_error( [ 'message' => __( 'You must be logged in.', 'xftc-membership' ) ] );
        }

        $meet_id    = absint( $_POST['meet_id'] ?? 0 );
        $athlete_id = absint( $_POST['athlete_id'] ?? 0 );
        $event      = sanitize_text_field( $_POST['event_category'] ?? '' );
        $division   = sanitize_text_field( $_POST['division'] ?? '' );

        if ( ! $meet_id || ! $athlete_id ) {
            wp_send_json_error( [ 'message' => __( 'Invalid meet or athlete.', 'xftc-membership' ) ] );
        }

        // Verify this athlete belongs to the logged-in parent
        $members = new XFTC_Members();
        $athlete = $members->get( $athlete_id );
        if ( ! $athlete || (int) $athlete->parent_id !== get_current_user_id() ) {
            wp_send_json_error( [ 'message' => __( 'You do not have permission to register this athlete.', 'xftc-membership' ) ] );
        }

        $meets  = new XFTC_Meets();
        $entry_id = $meets->register_athlete( $meet_id, $athlete_id, [
            'event_category' => $event,
            'division'       => $division,
        ] );

        if ( ! $entry_id ) {
            wp_send_json_error( [ 'message' => __( 'Registration failed. Please try again.', 'xftc-membership' ) ] );
        }

        wp_send_json_success( [
            'message'  => sprintf( __( '%s has been registered for this meet!', 'xftc-membership' ), esc_html( $athlete->first_name ) ),
            'entry_id' => $entry_id,
        ] );
    }

    /**
     * AJAX: Get chart data for an athlete's progression in an event
     */
    public function ajax_get_chart_data(): void {
        check_ajax_referer( 'xftc_public_nonce', 'xftc_nonce' );

        $athlete_id = absint( $_POST['athlete_id'] ?? 0 );
        $event      = sanitize_text_field( $_POST['event'] ?? '' );

        if ( ! $athlete_id || ! $event ) {
            wp_send_json_error( [] );
        }

        $results    = new XFTC_Results();
        $chart_data = $results->get_progression_chart_data( $athlete_id, $event );
        wp_send_json_success( $chart_data );
    }

    // ═══════════════════════════════════════════════════════════════════════
    // HELPERS
    // ═══════════════════════════════════════════════════════════════════════

    private function login_prompt(): string {
        return '<div class="xftc-notice xftc-notice--warning">'
            . sprintf(
                __( 'Please <a href="%s">log in</a> to view this content.', 'xftc-membership' ),
                esc_url( home_url( '/portal' ) )
            )
            . '</div>';
    }

    /**
     * Map athlete age to division slug for frontend filtering.
     */
    public function age_to_division( ?int $age ): string {
        if ( ! $age ) return '';
        if ( $age <= 10 ) return 'youth';
        if ( $age <= 14 ) return 'junior';
        return 'senior';
    }

}
