<?php
/**
 * Public view — Registration form
 * Used by: [xftc_register_form]
 * @package XFTC_Membership
 */
defined( 'ABSPATH' ) || exit;
?>
<div class="xftc-register-wrap">
    <form class="xftc-form" id="xftc-register-form" novalidate>
        <?php wp_nonce_field( 'xftc_public_nonce', 'xftc_nonce' ); ?>
        <input type="hidden" name="action" value="xftc_register_athlete">

        <!-- STEP 1: Parent Account -->
        <div class="xftc-form__step" data-step="1">
            <h3 class="xftc-form__step-title">👤 Parent / Guardian Account</h3>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="parent_first"><?php esc_html_e( 'First Name', 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="text" id="parent_first" name="parent_first" required placeholder="Jane">
                </div>
                <div class="xftc-form__group">
                    <label for="parent_last"><?php esc_html_e( 'Last Name', 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="text" id="parent_last" name="parent_last" required placeholder="Smith">
                </div>
            </div>
            <div class="xftc-form__group">
                <label for="parent_email"><?php esc_html_e( 'Email Address', 'xftc-membership' ); ?> <span class="req">*</span></label>
                <input type="email" id="parent_email" name="parent_email" required placeholder="parent@email.com">
            </div>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="reg_password"><?php esc_html_e( 'Password', 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="password" id="reg_password" name="password" required minlength="8" placeholder="Min. 8 characters">
                </div>
                <div class="xftc-form__group">
                    <label for="reg_password2"><?php esc_html_e( 'Confirm Password', 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="password" id="reg_password2" name="password2" required placeholder="Repeat password">
                </div>
            </div>
            <div class="xftc-form__actions">
                <button type="button" class="xftc-btn xftc-btn--primary xftc-next-step">
                    Next: Athlete Info →
                </button>
            </div>
        </div>

        <!-- STEP 2: Athlete Info -->
        <div class="xftc-form__step" data-step="2" style="display:none;">
            <h3 class="xftc-form__step-title">🏃 Athlete Information</h3>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="athlete_first"><?php esc_html_e( "Athlete's First Name", 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="text" id="athlete_first" name="athlete_first" required placeholder="Alex">
                </div>
                <div class="xftc-form__group">
                    <label for="athlete_last"><?php esc_html_e( "Athlete's Last Name", 'xftc-membership' ); ?> <span class="req">*</span></label>
                    <input type="text" id="athlete_last" name="athlete_last" required placeholder="Smith">
                </div>
            </div>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="dob"><?php esc_html_e( 'Date of Birth', 'xftc-membership' ); ?></label>
                    <input type="date" id="dob" name="dob">
                </div>
                <div class="xftc-form__group">
                    <label for="gender"><?php esc_html_e( 'Gender', 'xftc-membership' ); ?></label>
                    <select id="gender" name="gender">
                        <option value="">— Select —</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other / Prefer not to say</option>
                    </select>
                </div>
            </div>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="school"><?php esc_html_e( 'School', 'xftc-membership' ); ?></label>
                    <input type="text" id="school" name="school" placeholder="Pflugerville Middle School">
                </div>
                <div class="xftc-form__group">
                    <label for="team_level"><?php esc_html_e( 'Team Level', 'xftc-membership' ); ?></label>
                    <select id="team_level" name="team_level">
                        <option value="">— Select —</option>
                        <option value="Youth">Youth (6–10)</option>
                        <option value="Junior">Junior (11–14)</option>
                        <option value="Senior">Senior (15–18)</option>
                    </select>
                </div>
            </div>
            <div class="xftc-form__row xftc-form__row--2">
                <div class="xftc-form__group">
                    <label for="emergency_name"><?php esc_html_e( 'Emergency Contact Name', 'xftc-membership' ); ?></label>
                    <input type="text" id="emergency_name" name="emergency_name" placeholder="Full name">
                </div>
                <div class="xftc-form__group">
                    <label for="emergency_phone"><?php esc_html_e( 'Emergency Contact Phone', 'xftc-membership' ); ?></label>
                    <input type="tel" id="emergency_phone" name="emergency_phone" placeholder="(512) 000-0000">
                </div>
            </div>
            <div class="xftc-form__actions">
                <button type="button" class="xftc-btn xftc-btn--outline xftc-prev-step">← Back</button>
                <button type="button" class="xftc-btn xftc-btn--primary xftc-next-step">Next: Season & Tier →</button>
            </div>
        </div>

        <!-- STEP 3: Season Selection -->
        <div class="xftc-form__step" data-step="3" style="display:none;">
            <h3 class="xftc-form__step-title">📅 Season &amp; Membership Tier</h3>

            <?php
            if ( class_exists( 'XFTC_Seasons' ) ) {
                $seasons_obj = new XFTC_Seasons();
                $seasons     = $seasons_obj->get_active() ? [ $seasons_obj->get_active() ] : [];
            } else {
                $seasons = [];
            }
            ?>

            <?php if ( ! empty( $seasons ) ) : ?>
                <div class="xftc-form__group">
                    <label><?php esc_html_e( 'Select Season', 'xftc-membership' ); ?></label>
                    <?php foreach ( $seasons as $season ) :
                        $fee_std = ! empty( $season->fee_standard ) ? '$' . number_format( $season->fee_standard, 2 ) : 'TBD';
                        $fee_prm = ! empty( $season->fee_premium )  ? '$' . number_format( $season->fee_premium, 2 )  : 'TBD';
                    ?>
                    <label class="xftc-tier-option">
                        <input type="radio" name="season_id" value="<?php echo esc_attr( $season->id ); ?>" checked>
                        <span class="xftc-tier-option__label">
                            <strong><?php echo esc_html( $season->name ); ?></strong>
                            <span class="xftc-tier-option__dates">
                                <?php echo esc_html( date( 'M j', strtotime( $season->start_date ) ) ); ?> —
                                <?php echo esc_html( date( 'M j, Y', strtotime( $season->end_date ) ) ); ?>
                            </span>
                        </span>
                    </label>
                    <?php endforeach; ?>
                </div>
            <?php else : ?>
                <p class="xftc-notice xftc-notice--info">Registration is now open for the 2026 season. Tier selection will be confirmed during checkout.</p>
            <?php endif; ?>

            <div class="xftc-form__group">
                <label><?php esc_html_e( 'Membership Tier', 'xftc-membership' ); ?></label>
                <div class="xftc-tier-cards">
                    <label class="xftc-tier-card">
                        <input type="radio" name="tier" value="standard" checked>
                        <div class="xftc-tier-card__inner">
                            <div class="xftc-tier-card__name">Standard</div>
                            <div class="xftc-tier-card__desc">Season membership, practices, home meets</div>
                        </div>
                    </label>
                    <label class="xftc-tier-card">
                        <input type="radio" name="tier" value="premium">
                        <div class="xftc-tier-card__inner xftc-tier-card__inner--gold">
                            <div class="xftc-tier-card__name">Premium ⭐</div>
                            <div class="xftc-tier-card__desc">All Standard benefits + invitational travel + priority seeding</div>
                        </div>
                    </label>
                </div>
            </div>

            <div class="xftc-form__actions">
                <button type="button" class="xftc-btn xftc-btn--outline xftc-prev-step">← Back</button>
                <button type="button" class="xftc-btn xftc-btn--primary xftc-next-step">Next: Payment →</button>
            </div>
        </div>

        <!-- STEP 4: Review & Submit -->
        <div class="xftc-form__step" data-step="4" style="display:none;">
            <h3 class="xftc-form__step-title">💳 Review &amp; Submit</h3>
            <div class="xftc-review-summary" id="xftc-review-summary">
                <!-- Populated by JS -->
            </div>
            <div class="xftc-form__group">
                <label>
                    <input type="checkbox" name="waiver_agree" required>
                    <?php echo wp_kses_post( sprintf(
                        __( 'I agree to the <a href="%s" target="_blank">liability waiver</a> and <a href="%s" target="_blank">club code of conduct</a>.', 'xftc-membership' ),
                        esc_url( home_url( '/waiver' ) ),
                        esc_url( home_url( '/code-of-conduct' ) )
                    ) ); ?>
                </label>
            </div>
            <div class="xftc-form__actions">
                <button type="button" class="xftc-btn xftc-btn--outline xftc-prev-step">← Back</button>
                <button type="submit" class="xftc-btn xftc-btn--primary" id="xftc-submit-btn">
                    🏃 Complete Registration
                </button>
            </div>
            <div class="xftc-form__feedback" aria-live="polite"></div>
        </div>

    </form>
</div>
