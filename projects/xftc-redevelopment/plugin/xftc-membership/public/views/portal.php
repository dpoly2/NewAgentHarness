<?php defined( 'ABSPATH' ) || exit; ?>
<div class="xftc-portal-wrap">
    <div class="xftc-portal-header">
        <h2><?php echo esc_html( sprintf( __( 'Welcome, %s!', 'xftc-membership' ), $user->first_name ?: $user->display_name ) ); ?></h2>
        <?php if ( $active ) : ?>
            <span class="xftc-active-season-badge"><?php echo esc_html( $active->name ); ?> <?php esc_html_e( 'Season', 'xftc-membership' ); ?></span>
        <?php endif; ?>
        <a href="<?php echo esc_url( wp_logout_url( home_url() ) ); ?>" class="xftc-btn xftc-btn-outline xftc-btn-sm"><?php esc_html_e( 'Log Out', 'xftc-membership' ); ?></a>
    </div>

    <!-- Athlete Profiles -->
    <div class="xftc-portal-section">
        <div class="xftc-section-header">
            <h3><?php esc_html_e( 'Your Athletes', 'xftc-membership' ); ?></h3>
            <button class="xftc-btn xftc-btn-primary xftc-btn-sm" id="xftc-add-athlete-btn"><?php esc_html_e( '+ Add Athlete', 'xftc-membership' ); ?></button>
        </div>

        <?php if ( empty( $athletes ) ) : ?>
            <div class="xftc-empty-state">
                <p><?php esc_html_e( "You haven't added any athletes yet.", 'xftc-membership' ); ?></p>
                <button class="xftc-btn xftc-btn-primary" id="xftc-add-athlete-btn-2"><?php esc_html_e( 'Add Your First Athlete', 'xftc-membership' ); ?></button>
            </div>
        <?php else : ?>
            <div class="xftc-athlete-cards">
                <?php foreach ( $athletes as $athlete ) : ?>
                <div class="xftc-athlete-card">
                    <div class="xftc-athlete-avatar">
                        <?php echo esc_html( strtoupper( substr( $athlete->first_name, 0, 1 ) . substr( $athlete->last_name, 0, 1 ) ) ); ?>
                    </div>
                    <div class="xftc-athlete-info">
                        <strong><?php echo esc_html( $athlete->first_name . ' ' . $athlete->last_name ); ?></strong>
                        <?php if ( $athlete->team_level ) : ?>
                            <span class="xftc-tag"><?php echo esc_html( $athlete->team_level ); ?></span>
                        <?php endif; ?>
                        <?php if ( $athlete->school ) : ?>
                            <div class="xftc-athlete-school"><?php echo esc_html( $athlete->school ); ?></div>
                        <?php endif; ?>
                    </div>
                    <?php if ( $active ) : ?>
                    <div class="xftc-athlete-actions">
                        <button class="xftc-btn xftc-btn-outline xftc-btn-sm xftc-register-for-season"
                            data-athlete-id="<?php echo absint( $athlete->id ); ?>"
                            data-season-id="<?php echo absint( $active->id ); ?>">
                            <?php esc_html_e( 'Register for Season', 'xftc-membership' ); ?>
                        </button>
                    </div>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </div>

    <!-- Add Athlete Modal -->
    <div id="xftc-add-athlete-modal" class="xftc-modal" style="display:none;">
        <div class="xftc-modal-inner">
            <div class="xftc-modal-header">
                <h3><?php esc_html_e( 'Add Athlete', 'xftc-membership' ); ?></h3>
                <button class="xftc-modal-close">&times;</button>
            </div>
            <div id="xftc-add-athlete-message" class="xftc-message" style="display:none;"></div>
            <form id="xftc-add-athlete-form">
                <div class="xftc-form-row xftc-two-col">
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'First Name', 'xftc-membership' ); ?> *</label>
                        <input type="text" name="first_name" required>
                    </div>
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Last Name', 'xftc-membership' ); ?> *</label>
                        <input type="text" name="last_name" required>
                    </div>
                </div>
                <div class="xftc-form-row xftc-two-col">
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Date of Birth', 'xftc-membership' ); ?></label>
                        <input type="date" name="dob">
                    </div>
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Gender', 'xftc-membership' ); ?></label>
                        <select name="gender">
                            <option value=""><?php esc_html_e( 'Select...', 'xftc-membership' ); ?></option>
                            <option value="male"><?php esc_html_e( 'Male', 'xftc-membership' ); ?></option>
                            <option value="female"><?php esc_html_e( 'Female', 'xftc-membership' ); ?></option>
                            <option value="other"><?php esc_html_e( 'Other', 'xftc-membership' ); ?></option>
                        </select>
                    </div>
                </div>
                <div class="xftc-form-row xftc-two-col">
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Team Level', 'xftc-membership' ); ?></label>
                        <select name="team_level">
                            <option value=""><?php esc_html_e( 'Select...', 'xftc-membership' ); ?></option>
                            <option value="8 & Under"><?php esc_html_e( '8 & Under', 'xftc-membership' ); ?></option>
                            <option value="10 & Under"><?php esc_html_e( '10 & Under', 'xftc-membership' ); ?></option>
                            <option value="12 & Under"><?php esc_html_e( '12 & Under', 'xftc-membership' ); ?></option>
                            <option value="14 & Under"><?php esc_html_e( '14 & Under', 'xftc-membership' ); ?></option>
                            <option value="17 & Under"><?php esc_html_e( '17 & Under', 'xftc-membership' ); ?></option>
                            <option value="Open"><?php esc_html_e( 'Open', 'xftc-membership' ); ?></option>
                        </select>
                    </div>
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'School', 'xftc-membership' ); ?></label>
                        <input type="text" name="school">
                    </div>
                </div>
                <div class="xftc-form-row xftc-two-col">
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Emergency Contact Name', 'xftc-membership' ); ?></label>
                        <input type="text" name="emergency_contact_name">
                    </div>
                    <div class="xftc-form-group">
                        <label><?php esc_html_e( 'Emergency Contact Phone', 'xftc-membership' ); ?></label>
                        <input type="tel" name="emergency_contact_phone">
                    </div>
                </div>
                <div class="xftc-form-submit">
                    <button type="submit" class="xftc-btn xftc-btn-primary"><?php esc_html_e( 'Save Athlete', 'xftc-membership' ); ?></button>
                    <button type="button" class="xftc-btn xftc-btn-outline xftc-modal-close"><?php esc_html_e( 'Cancel', 'xftc-membership' ); ?></button>
                </div>
            </form>
        </div>
    </div>
</div>
