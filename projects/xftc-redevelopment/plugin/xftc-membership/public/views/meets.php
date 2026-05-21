<?php
/**
 * Public view — Meets (used by [TRACKSUITE_meets] and [TRACKSUITE_schedule])
 * Variables available: $meets, $view, $by_month, $show_register, $upcoming,
 *                      $athletes, $athlete_meets, $atts
 * @package TRACKSUITE_Membership
 */
defined( 'ABSPATH' ) || exit;

// ── [TRACKSUITE_meets] card/list view ──────────────────────────────────────────────
if ( ! empty( $meets ) ) :

    if ( isset( $view ) && $view === 'cards' ) : ?>
        <div class="ts-meets-grid">
            <?php foreach ( $meets as $meet ) :
                $ts    = ! empty( $meet['meet_date'] ) ? strtotime( $meet['meet_date'] ) : 0;
                $day   = $ts ? date( 'j',   $ts ) : '—';
                $month = $ts ? date( 'M',   $ts ) : '';
                $types = [ 'competitive' => 'Competitive', 'invitational' => 'Invitational', 'practice' => 'Practice' ];
                $badge = $types[ $meet['type'] ?? '' ] ?? '';
            ?>
            <div class="ts-meet-card" data-type="<?php echo esc_attr( $meet['type'] ?? '' ); ?>"
                 data-status="<?php echo esc_attr( $meet['status'] ?? '' ); ?>">
                <div class="ts-meet-card__date">
                    <span class="ts-meet-card__day"><?php echo esc_html( $day ); ?></span>
                    <span class="ts-meet-card__month"><?php echo esc_html( $month ); ?></span>
                </div>
                <div class="ts-meet-card__info">
                    <div class="ts-meet-card__name"><?php echo esc_html( $meet['name'] ); ?></div>
                    <div class="ts-meet-card__meta">
                        <?php if ( ! empty( $meet['location'] ) ) : ?>
                            <span>📍 <?php echo esc_html( $meet['location'] ); ?></span>
                        <?php endif; ?>
                        <?php if ( ! empty( $meet['meet_time'] ) ) : ?>
                            <span>🕐 <?php echo esc_html( $meet['meet_time'] ); ?></span>
                        <?php endif; ?>
                    </div>
                    <?php if ( $badge ) : ?>
                        <span class="ts-badge ts-badge--type"><?php echo esc_html( $badge ); ?></span>
                    <?php endif; ?>
                </div>
                <?php if ( ! empty( $show_register ) && is_user_logged_in() ) : ?>
                <div class="ts-meet-card__action">
                    <button class="ts-btn ts-btn--sm ts-btn--outline ts-register-meet-btn"
                            data-meet-id="<?php echo esc_attr( $meet['id'] ); ?>"
                            data-meet-name="<?php echo esc_attr( $meet['name'] ); ?>">
                        Register
                    </button>
                </div>
                <?php endif; ?>
            </div>
            <?php endforeach; ?>
        </div>

    <?php else : // list view ?>
        <div class="ts-meets-list">
            <?php foreach ( $meets as $meet ) :
                $ts = ! empty( $meet['meet_date'] ) ? strtotime( $meet['meet_date'] ) : 0;
            ?>
            <div class="ts-meet-row" data-type="<?php echo esc_attr( $meet['type'] ?? '' ); ?>">
                <span class="ts-meet-row__date"><?php echo $ts ? esc_html( date( 'D, M j', $ts ) ) : '—'; ?></span>
                <span class="ts-meet-row__name"><?php echo esc_html( $meet['name'] ); ?></span>
                <span class="ts-meet-row__loc"><?php echo esc_html( $meet['location'] ?? '' ); ?></span>
            </div>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>

<?php endif; // end $meets ?>


<?php // ── [TRACKSUITE_schedule] full schedule grouped by month ──────────────────────
if ( ! empty( $by_month ) ) : ?>
    <div class="ts-schedule">
        <?php foreach ( $by_month as $ym => $month_meets ) :
            $month_label = date( 'F Y', strtotime( $ym . '-01' ) );
        ?>
        <div class="ts-schedule__month">
            <h3 class="ts-schedule__month-heading"><?php echo esc_html( $month_label ); ?></h3>
            <div class="ts-schedule__list">
                <?php foreach ( $month_meets as $meet ) :
                    $ts    = ! empty( $meet['meet_date'] ) ? strtotime( $meet['meet_date'] ) : 0;
                    $types = [ 'competitive' => 'Competitive', 'invitational' => 'Invitational', 'practice' => 'Practice' ];
                    $badge = $types[ $meet['type'] ?? '' ] ?? '';
                    $past  = $ts && $ts < time();
                ?>
                <div class="ts-meet-card <?php echo $past ? 'ts-meet-card--past' : ''; ?>"
                     data-type="<?php echo esc_attr( $meet['type'] ?? '' ); ?>"
                     data-status="<?php echo esc_attr( $meet['status'] ?? '' ); ?>">
                    <div class="ts-meet-card__date">
                        <span class="ts-meet-card__day"><?php echo $ts ? esc_html( date( 'j', $ts ) ) : '—'; ?></span>
                        <span class="ts-meet-card__month"><?php echo $ts ? esc_html( date( 'M', $ts ) ) : ''; ?></span>
                    </div>
                    <div class="ts-meet-card__info">
                        <div class="ts-meet-card__name"><?php echo esc_html( $meet['name'] ); ?></div>
                        <div class="ts-meet-card__meta">
                            <?php if ( ! empty( $meet['location'] ) ) : ?>
                                <span>📍 <?php echo esc_html( $meet['location'] ); ?></span>
                            <?php endif; ?>
                            <?php if ( ! empty( $meet['meet_time'] ) ) : ?>
                                <span>🕐 <?php echo esc_html( $meet['meet_time'] ); ?></span>
                            <?php endif; ?>
                            <?php if ( $badge ) : ?>
                                <span class="ts-badge ts-badge--type"><?php echo esc_html( $badge ); ?></span>
                            <?php endif; ?>
                        </div>
                    </div>
                    <?php if ( ! empty( $show_register ) && is_user_logged_in() && ! $past ) : ?>
                    <div class="ts-meet-card__action">
                        <button class="ts-btn ts-btn--sm ts-register-meet-btn"
                                data-meet-id="<?php echo esc_attr( $meet['id'] ); ?>"
                                data-meet-name="<?php echo esc_attr( $meet['name'] ); ?>">
                            Register
                        </button>
                    </div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
<?php endif; // end $by_month ?>


<?php // ── [TRACKSUITE_my_schedule] portal view: athlete meet registrations ───────────
if ( ! empty( $athlete_meets ) && ! empty( $athletes ) ) : ?>
    <div class="ts-my-schedule">
        <?php foreach ( $athletes as $athlete ) :
            $ath_meets = $athlete_meets[ $athlete->id ] ?? [];
        ?>
        <div class="ts-portal-athlete">
            <h4 class="ts-portal-athlete__name">
                👤 <?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?>
            </h4>

            <?php if ( ! empty( $ath_meets ) ) : ?>
                <div class="ts-table-wrap">
                    <table class="ts-table">
                        <thead>
                            <tr><th>Meet</th><th>Date</th><th>Event</th><th>Waiver</th></tr>
                        </thead>
                        <tbody>
                        <?php foreach ( $ath_meets as $m ) : ?>
                            <tr>
                                <td><?php echo esc_html( $m['name'] ?? '—' ); ?></td>
                                <td><?php echo ! empty( $m['meet_date'] ) ? esc_html( date( 'M j, Y', strtotime( $m['meet_date'] ) ) ) : '—'; ?></td>
                                <td><?php echo esc_html( $m['event_category'] ?? '—' ); ?></td>
                                <td><?php echo $m['waiver_uploaded'] ? '✅' : '<span style="color:#dc3545">⚠️ Pending</span>'; ?></td>
                            </tr>
                        <?php endforeach; ?>
                        </tbody>
                    </table>
                </div>
            <?php else : ?>
                <p class="ts-empty">No meets registered yet.</p>
            <?php endif; ?>

            <?php if ( ! empty( $show_register ) && ! empty( $upcoming ) ) : ?>
                <details class="ts-collapsible" style="margin-top:1rem;">
                    <summary class="ts-btn ts-btn--sm ts-btn--outline">+ Register for a Meet</summary>
                    <div style="padding-top:1rem;">
                        <?php foreach ( $upcoming as $um ) :
                            $ts = ! empty( $um['meet_date'] ) ? strtotime( $um['meet_date'] ) : 0;
                        ?>
                        <div style="margin-bottom:.75rem;padding:.75rem;background:#f8f9fa;border-radius:6px;display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;">
                            <div>
                                <strong><?php echo esc_html( $um['name'] ); ?></strong>
                                <span style="color:#6c757d;font-size:.8rem;margin-left:.5rem;"><?php echo $ts ? esc_html( date( 'M j, Y', $ts ) ) : ''; ?></span>
                            </div>
                            <button class="ts-btn ts-btn--sm ts-btn--primary ts-register-meet-btn"
                                    data-meet-id="<?php echo esc_attr( $um['id'] ); ?>"
                                    data-meet-name="<?php echo esc_attr( $um['name'] ); ?>"
                                    data-athlete-id="<?php echo esc_attr( $athlete->id ); ?>">
                                Register
                            </button>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </details>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
    </div>
<?php endif; ?>

