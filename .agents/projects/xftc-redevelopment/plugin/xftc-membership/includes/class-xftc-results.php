<?php
/**
 * XFTC Results — CRUD, leaderboard logic, athlete profile
 * Version: 2.1.0
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

class XFTC_Results {

    /* ── Event categories (canonical order) ─────────────────────────────── */
    public static $TRACK_EVENTS = [
        '100m', '200m', '400m', '800m', '1500m', '1600m', 'Mile',
        '3000m', '3200m', '5000m', '60m Hurdles', '100m Hurdles',
        '110m Hurdles', '400m Hurdles', '4x100m Relay', '4x400m Relay',
        '4x800m Relay', 'Sprint Medley',
    ];
    public static $FIELD_EVENTS = [
        'Long Jump', 'Triple Jump', 'High Jump', 'Pole Vault',
        'Shot Put', 'Discus', 'Javelin', 'Hammer',
    ];

    /* ── Age division labels (AAU standard) ──────────────────────────────── */
    public static $DIVISIONS = [
        '6U'  => [0,  6],
        '8U'  => [7,  8],
        '10U' => [9,  10],
        '12U' => [11, 12],
        '14U' => [13, 14],
        '16U' => [15, 16],
        '18U' => [17, 18],
    ];

    /* ── Init ────────────────────────────────────────────────────────────── */
    public function __construct() {
        add_shortcode( 'xftc_leaderboard',      [ $this, 'shortcode_leaderboard' ] );
        add_shortcode( 'xftc_athlete_profile',  [ $this, 'shortcode_athlete_profile' ] );
        add_shortcode( 'xftc_top_times',        [ $this, 'shortcode_leaderboard' ] ); // alias

        add_action( 'wp_ajax_xftc_get_leaderboard',        [ $this, 'ajax_leaderboard' ] );
        add_action( 'wp_ajax_nopriv_xftc_get_leaderboard', [ $this, 'ajax_leaderboard' ] );
        add_action( 'wp_ajax_xftc_get_athlete_results',        [ $this, 'ajax_athlete_results' ] );
        add_action( 'wp_ajax_nopriv_xftc_get_athlete_results', [ $this, 'ajax_athlete_results' ] );
    }

    /* ════════════════════════════════════════════════════════════════════════
       UTILITY: Convert result_value to sortable decimal seconds / cm
       ════════════════════════════════════════════════════════════════════════ */

    /**
     * Convert a result string to a float for sorting.
     * Track: "1:45.30" → 105.30, "10.02" → 10.02
     * Field: "25-11.5" → 791.9 (cm), "6.50" → 6.50 (meters)
     * Returns PHP_FLOAT_MAX on error (sinks bad data to bottom).
     */
    public static function result_to_sortable( $value, $unit = 'time' ) {
        $value = trim( $value );
        if ( $unit === 'time' ) {
            // Format MM:SS.ss or HH:MM:SS.ss or SS.ss
            if ( preg_match( '/^(\d+):(\d+)(?:\.(\d+))?$/', $value, $m ) ) {
                return intval($m[1]) * 60 + intval($m[2]) + ( isset($m[3]) ? floatval('0.'.$m[3]) : 0 );
            }
            if ( preg_match( '/^(\d+):(\d+):(\d+)(?:\.(\d+))?$/', $value, $m ) ) {
                return intval($m[1]) * 3600 + intval($m[2]) * 60 + intval($m[3]) + ( isset($m[4]) ? floatval('0.'.$m[4]) : 0 );
            }
            if ( is_numeric( $value ) ) return floatval( $value );
        } else { // distance/height
            // Format: Feet-Inches  e.g. "25-11.5" or "6-2"
            if ( preg_match( '/^(\d+)-(\d+(?:\.\d+)?)$/', $value, $m ) ) {
                return ( intval($m[1]) * 12 + floatval($m[2]) ) * 2.54; // → cm
            }
            // Format: plain meters e.g. "6.50"
            if ( is_numeric( $value ) ) return floatval( $value ) * 100; // → cm
        }
        return PHP_FLOAT_MAX; // unsortable
    }

    /**
     * Determine if an event is field (distance sort = bigger is better).
     */
    public static function is_field_event( $event ) {
        $field_keywords = [ 'jump', 'vault', 'put', 'throw', 'discus', 'javelin', 'hammer', 'weight' ];
        $ev = strtolower( $event );
        foreach ( $field_keywords as $kw ) {
            if ( strpos( $ev, $kw ) !== false ) return true;
        }
        return false;
    }

    /**
     * Get age division label for a given age.
     */
    public static function age_to_division( $age ) {
        foreach ( self::$DIVISIONS as $label => [$min, $max] ) {
            if ( $age >= $min && $age <= $max ) return $label;
        }
        return '18U';
    }

    /**
     * Calculate athlete age from DOB string.
     */
    public static function calc_age( $dob ) {
        if ( empty( $dob ) ) return null;
        return floor( ( time() - strtotime( $dob ) ) / 31557600 );
    }

    /* ════════════════════════════════════════════════════════════════════════
       LEADERBOARD — Top N results per event per division
       ════════════════════════════════════════════════════════════════════════ */

    /**
     * Get leaderboard data: top N results for each event x division.
     *
     * @param array $args {
     *   season_id  int|null    — null = all seasons
     *   gender     string|null — 'male'|'female'|null
     *   division   string|null — '10U'|'12U' etc, null = all
     *   event      string|null — specific event, null = all
     *   limit      int         — top N per group (default 20)
     * }
     * @return array Keyed [event][division] => [ row, row, ... ]
     */
    public function get_leaderboard( $args = [] ) {
        global $wpdb;

        $args = wp_parse_args( $args, [
            'season_id' => null,
            'gender'    => null,
            'division'  => null,
            'event'     => null,
            'limit'     => 20,
        ] );

        $rt  = $wpdb->prefix . 'xftc_results';
        $mt  = $wpdb->prefix . 'xftc_meets';
        $at  = $wpdb->prefix . 'xftc_athletes';
        $met = $wpdb->prefix . 'xftc_meet_entries';

        // Build WHERE
        $where  = [ '1=1' ];
        $params = [];

        if ( ! empty( $args['season_id'] ) ) {
            // meets have a season_id if we add it; for now filter by season date range
            // no-op if season_id not in meets table — extend as needed
        }
        if ( ! empty( $args['event'] ) ) {
            $where[]  = 'r.event_category = %s';
            $params[] = $args['event'];
        }
        if ( ! empty( $args['gender'] ) ) {
            $where[]  = 'a.gender = %s';
            $params[] = $args['gender'];
        }

        $where_sql = implode( ' AND ', $where );

        $sql = "
            SELECT
                r.id,
                r.event_category,
                r.result_value,
                r.result_unit,
                r.placement,
                r.is_personal_best,
                r.is_club_record,
                r.recorded_at,
                a.id          AS athlete_id,
                a.first_name,
                a.last_name,
                a.dob,
                a.gender,
                a.team_level,
                m.id          AS meet_id,
                m.name        AS meet_name,
                m.meet_date
            FROM {$rt} r
            LEFT JOIN {$at} a  ON r.athlete_id = a.id
            LEFT JOIN {$mt} m  ON r.meet_id    = m.id
            WHERE {$where_sql}
            ORDER BY r.event_category, r.recorded_at DESC
        ";

        $results = ! empty( $params )
            ? $wpdb->get_results( $wpdb->prepare( $sql, ...$params ) )
            : $wpdb->get_results( $sql );

        if ( empty( $results ) ) return [];

        // ── Group + rank per event × division ──────────────────────────────
        $grouped = []; // [event][division] => [ rows ]
        $seen    = []; // deduplicate: best result per athlete per event per division

        foreach ( $results as $row ) {
            $age      = self::calc_age( $row->dob );
            $div      = $age ? self::age_to_division( $age ) : 'Open';
            $ev       = $row->event_category;

            // Division filter
            if ( ! empty( $args['division'] ) && $div !== $args['division'] ) continue;

            $key      = "{$ev}|{$div}|{$row->athlete_id}";
            $sortable = self::result_to_sortable( $row->result_value, $row->result_unit ?? 'time' );

            // Keep only the best result per athlete per event per division
            if ( isset( $seen[$key] ) ) {
                $is_field = self::is_field_event( $ev );
                $existing = $seen[$key]['sortable'];
                $better   = $is_field ? $sortable > $existing : $sortable < $existing;
                if ( ! $better ) continue;
            }

            $seen[$key] = [ 'sortable' => $sortable, 'row' => $row ];
        }

        // Build grouped array from best-only records
        foreach ( $seen as $key => $entry ) {
            $row      = $entry['row'];
            $age      = self::calc_age( $row->dob );
            $div      = $age ? self::age_to_division( $age ) : 'Open';
            $ev       = $row->event_category;
            $grouped[$ev][$div][] = [ 'row' => $row, 'sortable' => $entry['sortable'] ];
        }

        // Sort each group + limit to top N
        $limit = max( 1, intval( $args['limit'] ) );
        foreach ( $grouped as $ev => &$divisions ) {
            foreach ( $divisions as $div => &$rows ) {
                $is_field = self::is_field_event( $ev );
                usort( $rows, function($a, $b) use ($is_field) {
                    return $is_field
                        ? $b['sortable'] <=> $a['sortable']
                        : $a['sortable'] <=> $b['sortable'];
                });
                $rows = array_slice( $rows, 0, $limit );
                // Add rank
                foreach ( $rows as $i => &$r ) { $r['rank'] = $i + 1; }
                unset($r);
            }
            unset($rows);
        }
        unset($divisions);

        return $grouped;
    }

    /* ════════════════════════════════════════════════════════════════════════
       SHORTCODE: [xftc_leaderboard limit="20" gender="" division="" season=""]
       ════════════════════════════════════════════════════════════════════════ */
    public function shortcode_leaderboard( $atts ) {
        $atts = shortcode_atts([
            'limit'    => 20,
            'gender'   => '',
            'division' => '',
            'season'   => 'current',
            'event'    => '',
        ], $atts );

        // Enqueue Chart.js + public assets
        wp_enqueue_script( 'chart-js', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js', [], '4.4.0', true );
        wp_enqueue_script( 'xftc-public', plugins_url( 'public/assets/public.js', XFTC_PLUGIN_FILE ), ['jquery','chart-js'], XFTC_VERSION, true );
        wp_enqueue_style( 'xftc-public', plugins_url( 'public/assets/public.css', XFTC_PLUGIN_FILE ), [], XFTC_VERSION );

        $data = $this->get_leaderboard([
            'limit'    => intval( $atts['limit'] ),
            'gender'   => sanitize_text_field( $atts['gender'] ),
            'division' => sanitize_text_field( $atts['division'] ),
            'event'    => sanitize_text_field( $atts['event'] ),
        ]);

        // Get distinct events and divisions for filter UI
        global $wpdb;
        $rt       = $wpdb->prefix . 'xftc_results';
        $events   = $wpdb->get_col( "SELECT DISTINCT event_category FROM {$rt} ORDER BY event_category ASC" );
        $seasons  = $wpdb->get_results( "SELECT * FROM {$wpdb->prefix}xftc_seasons ORDER BY start_date DESC" );

        ob_start();
        include plugin_dir_path( XFTC_PLUGIN_FILE ) . 'public/views/leaderboard.php';
        return ob_get_clean();
    }

    /* ════════════════════════════════════════════════════════════════════════
       SHORTCODE: [xftc_athlete_profile id="123"]
       ════════════════════════════════════════════════════════════════════════ */
    public function shortcode_athlete_profile( $atts ) {
        $atts = shortcode_atts([
            'id' => isset( $_GET['athlete_id'] ) ? intval( $_GET['athlete_id'] ) : 0,
        ], $atts );

        if ( ! $atts['id'] ) {
            return '<p class="xftc-notice xftc-notice--info">No athlete selected.</p>';
        }

        wp_enqueue_script( 'chart-js', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js', [], '4.4.0', true );
        wp_enqueue_script( 'xftc-public', plugins_url( 'public/assets/public.js', XFTC_PLUGIN_FILE ), ['jquery','chart-js'], XFTC_VERSION, true );
        wp_enqueue_style( 'xftc-public', plugins_url( 'public/assets/public.css', XFTC_PLUGIN_FILE ), [], XFTC_VERSION );

        global $wpdb;
        $at = $wpdb->prefix . 'xftc_athletes';
        $rt = $wpdb->prefix . 'xftc_results';
        $mt = $wpdb->prefix . 'xftc_meets';

        $athlete = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$at} WHERE id=%d", $atts['id'] ) );
        if ( ! $athlete ) return '<p class="xftc-notice xftc-notice--warning">Athlete not found.</p>';

        // All results with meet info
        $results = $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, m.name AS meet_name, m.meet_date, m.location
             FROM {$rt} r
             LEFT JOIN {$mt} m ON r.meet_id = m.id
             WHERE r.athlete_id = %d
             ORDER BY m.meet_date DESC, r.event_category ASC",
            $athlete->id
        ));

        // Build PRs per event (best result per event)
        $prs = [];
        foreach ( $results as $res ) {
            $ev  = $res->event_category;
            $val = self::result_to_sortable( $res->result_value, $res->result_unit ?? 'time' );
            $is_field = self::is_field_event( $ev );
            if ( ! isset( $prs[$ev] ) ) {
                $prs[$ev] = $res;
            } else {
                $cur = self::result_to_sortable( $prs[$ev]->result_value, $prs[$ev]->result_unit ?? 'time' );
                if ( $is_field ? $val > $cur : $val < $cur ) $prs[$ev] = $res;
            }
        }

        // Group results by event for chart data
        $by_event = [];
        foreach ( $results as $res ) {
            $by_event[ $res->event_category ][] = $res;
        }
        foreach ( $by_event as $ev => &$rows ) {
            usort( $rows, fn($a,$b) => strcmp( $a->meet_date, $b->meet_date ) );
        }
        unset($rows);

        $age      = self::calc_age( $athlete->dob );
        $division = $age ? self::age_to_division( $age ) : 'Open';

        ob_start();
        include plugin_dir_path( XFTC_PLUGIN_FILE ) . 'public/views/athlete-profile.php';
        return ob_get_clean();
    }

    /* ════════════════════════════════════════════════════════════════════════
       AJAX handlers
       ════════════════════════════════════════════════════════════════════════ */
    public function ajax_leaderboard() {
        check_ajax_referer( 'xftc_nonce', 'nonce' );
        $data = $this->get_leaderboard([
            'gender'   => sanitize_text_field( $_POST['gender']   ?? '' ),
            'division' => sanitize_text_field( $_POST['division'] ?? '' ),
            'event'    => sanitize_text_field( $_POST['event']    ?? '' ),
            'limit'    => intval( $_POST['limit'] ?? 20 ),
        ]);
        wp_send_json_success( $data );
    }

    public function ajax_athlete_results() {
        check_ajax_referer( 'xftc_nonce', 'nonce' );
        $id = intval( $_POST['athlete_id'] ?? 0 );
        if ( ! $id ) wp_send_json_error( 'Invalid athlete.' );

        global $wpdb;
        $rt = $wpdb->prefix . 'xftc_results';
        $mt = $wpdb->prefix . 'xftc_meets';
        $results = $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, m.name AS meet_name, m.meet_date FROM {$rt} r
             LEFT JOIN {$mt} m ON r.meet_id=m.id
             WHERE r.athlete_id=%d ORDER BY m.meet_date DESC",
            $id
        ));
        wp_send_json_success( $results );
    }

    /* ════════════════════════════════════════════════════════════════════════
       CRUD — Admin entry
       ════════════════════════════════════════════════════════════════════════ */
    public function create( $data ) {
        global $wpdb;
        // Auto-detect PB and Club Record
        $ev_unit   = self::is_field_event( $data['event_category'] ) ? 'distance' : 'time';
        $new_sort  = self::result_to_sortable( $data['result_value'], $ev_unit );
        $is_field  = self::is_field_event( $data['event_category'] );
        $rt        = $wpdb->prefix . 'xftc_results';

        // Check personal best
        $prev_best = $wpdb->get_var( $wpdb->prepare(
            "SELECT result_value FROM {$rt} WHERE athlete_id=%d AND event_category=%s ORDER BY recorded_at ASC",
            $data['athlete_id'], $data['event_category']
        ));
        $is_pb = 0;
        if ( $prev_best ) {
            $pb_sort = self::result_to_sortable( $prev_best, $ev_unit );
            $is_pb   = $is_field ? $new_sort > $pb_sort : $new_sort < $pb_sort;
        } else {
            $is_pb = 1; // first result is always a PB
        }

        // Check club record
        $club_best = $wpdb->get_var( $wpdb->prepare(
            "SELECT result_value FROM {$rt} WHERE event_category=%s ORDER BY recorded_at ASC LIMIT 1",
            $data['event_category']
        ));
        $is_cr = 0;
        if ( $club_best ) {
            $cr_sort = self::result_to_sortable( $club_best, $ev_unit );
            $is_cr   = $is_field ? $new_sort > $cr_sort : $new_sort < $cr_sort;
        } else {
            $is_cr = 1;
        }

        $wpdb->insert( $rt, [
            'meet_id'         => intval( $data['meet_id'] ),
            'athlete_id'      => intval( $data['athlete_id'] ),
            'event_category'  => sanitize_text_field( $data['event_category'] ),
            'placement'       => intval( $data['placement'] ?? 0 ),
            'result_value'    => sanitize_text_field( $data['result_value'] ),
            'result_unit'     => $ev_unit,
            'is_personal_best'=> $is_pb ? 1 : 0,
            'is_club_record'  => $is_cr ? 1 : 0,
            'recorded_by'     => get_current_user_id(),
            'recorded_at'     => current_time( 'mysql' ),
        ]);
        return $wpdb->insert_id;
    }

    public function update( $id, $data ) {
        global $wpdb;
        $wpdb->update( $wpdb->prefix . 'xftc_results', $data, ['id' => $id] );
    }

    public function delete( $id ) {
        global $wpdb;
        $wpdb->delete( $wpdb->prefix . 'xftc_results', ['id' => $id] );
    }

    public function get( $id ) {
        global $wpdb;
        return $wpdb->get_row( $wpdb->prepare(
            "SELECT * FROM {$wpdb->prefix}xftc_results WHERE id=%d", $id
        ));
    }

    public function get_for_meet( $meet_id ) {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT r.*, a.first_name, a.last_name FROM {$wpdb->prefix}xftc_results r
             LEFT JOIN {$wpdb->prefix}xftc_athletes a ON r.athlete_id=a.id
             WHERE r.meet_id=%d ORDER BY r.event_category, r.placement ASC",
            $meet_id
        ));
    }
}
