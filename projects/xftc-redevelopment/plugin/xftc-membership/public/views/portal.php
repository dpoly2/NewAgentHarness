<?php
/**
 * Public view — Portal (athlete list + roster cards)
 * Used by: [xftc_my_athletes] and [xftc_roster]
 * Variables: $athletes, $active (active season), $user, $view, $show_stats
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;

// ── [xftc_roster] — public athlete card grid ────────────────────────────────
if ( isset( $view ) ) :
    if ( $view === 'cards' ) : ?>
        <div class="xftc-roster-grid">
            <?php if ( empty( $athletes ) ) : ?>
                <p class="xftc-empty">Roster coming soon!</p>
            <?php else : foreach ( $athletes as $athlete ) :
                $initials = strtoupper( substr( $athlete->first_name, 0, 1 ) . substr( $athlete->last_name, 0, 1 ) );
                $age = ! empty( $athlete->dob ) ? floor( ( time() - strtotime( $athlete->dob ) ) / 31557600 ) : null;
            ?>
            <div class="xftc-athlete-card" data-division="<?php echo esc_attr( $this->age_to_division( $age ) ); ?>">
                <div class="xftc-athlete-card__photo">
                    <div class="xftc-athlete-card__initials"><?php echo esc_html( $initials ); ?></div>
                </div>
                <div class="xftc-athlete-card__body">
                    <div class="xftc-athlete-card__name">
                        <?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?>
                    </div>
                    <div class="xftc-athlete-card__details">
                        <?php
                        $meta = [];
                        if ( $age ) $meta[] = 'Age ' . $age;
                        if ( ! empty( $athlete->team_level ) ) $meta[] = $athlete->team_level;
                        if ( ! empty( $athlete->school ) ) $meta[] = $athlete->school;
                        echo esc_html( implode( ' · ', $meta ) );
                        ?>
                    </div>
                    <?php if ( $show_stats ) :
                        global $wpdb;
                        $rt = $wpdb->prefix . 'xftc_results';
                        $pbs   = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND is_personal_best=1", $athlete->id ) );
                        $golds = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND placement=1", $athlete->id ) );
                    ?>
                    <div class="xftc-athlete-card__stats">
                        <div class="xftc-athlete-card__stat"><strong><?php echo $pbs; ?></strong> PBs</div>
                        <div class="xftc-athlete-card__stat"><strong><?php echo $golds; ?></strong> 🥇</div>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            <?php endforeach; endif; ?>
        </div>

    <?php else : // list view ?>
        <div class="xftc-table-wrap">
            <table class="xftc-table">
                <thead><tr><th>Name</th><th>Level</th><th>School</th></tr></thead>
                <tbody>
                <?php foreach ( $athletes as $athlete ) : ?>
                    <tr>
                        <td><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></td>
                        <td><?php echo esc_html( $athlete->team_level ?? '—' ); ?></td>
                        <td><?php echo esc_html( $athlete->school ?? '—' ); ?></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    <?php endif; ?>

<?php // ── [xftc_my_athletes] — portal dashboard ─────────────────────────────
else : ?>
    <div class="xftc-portal">
        <?php if ( empty( $athletes ) ) : ?>
            <div class="xftc-empty-state">
                <p>No athletes registered yet.</p>
                <a href="<?php echo esc_url( home_url( '/register' ) ); ?>" class="xftc-btn xftc-btn--primary">
                    ➕ Add an Athlete
                </a>
            </div>
        <?php else : ?>

            <?php if ( ! empty( $active ) ) : ?>
            <div class="xftc-season-banner">
                <strong>Active Season:</strong> <?php echo esc_html( $active->name ?? '' ); ?>
                <?php if ( ! empty( $active->reg_close ) ) : ?>
                    — Registration closes <?php echo esc_html( date( 'M j, Y', strtotime( $active->reg_close ) ) ); ?>
                <?php endif; ?>
            </div>
            <?php endif; ?>

            <div class="xftc-athletes-list">
                <?php foreach ( $athletes as $athlete ) :
                    $initials = strtoupper( substr( $athlete->first_name, 0, 1 ) . substr( $athlete->last_name, 0, 1 ) );
                    $age      = ! empty( $athlete->dob ) ? floor( ( time() - strtotime( $athlete->dob ) ) / 31557600 ) : null;

                    // Mini stats
                    global $wpdb;
                    $rt    = $wpdb->prefix . 'xftc_results';
                    $pbs   = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND is_personal_best=1", $athlete->id ) );
                    $golds = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d AND placement=1", $athlete->id ) );
                    $total = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$rt} WHERE athlete_id=%d", $athlete->id ) );
                ?>
                <div class="xftc-portal-athlete-card">
                    <div class="xftc-portal-athlete-card__avatar"><?php echo esc_html( $initials ); ?></div>
                    <div class="xftc-portal-athlete-card__info">
                        <h3><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></h3>
                        <div class="xftc-portal-athlete-card__meta">
                            <?php if ( $age ) echo esc_html( 'Age ' . $age . ' · ' ); ?>
                            <?php echo esc_html( $athlete->team_level ?? '' ); ?>
                            <?php if ( ! empty( $athlete->school ) ) echo ' · ' . esc_html( $athlete->school ); ?>
                        </div>
                        <div class="xftc-portal-athlete-card__stats">
                            <span>🏅 <?php echo $total; ?> Results</span>
                            <span>⚡ <?php echo $pbs; ?> PBs</span>
                            <span>🥇 <?php echo $golds; ?> Wins</span>
                        </div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

        <?php endif; ?>
    </div>
<?php endif; ?>
