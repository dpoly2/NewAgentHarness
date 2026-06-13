<?php
/**
 * PBS Event Commerce — ProfilePress Integration
 *
 * Provides four integration points:
 *  1. Gate ticket widget by PP membership plan (per-event setting)
 *  2. Pre-fill checkout name/email from the logged-in WP/PP user
 *  3. Grant a PP membership plan after a successful ticket purchase
 *  4. Auto-apply a % discount for active PP members (per-event setting)
 *  5. Show purchased tickets inside the PP member account dashboard
 *
 * This file is only loaded when ProfilePress is active (checked in main plugin file).
 */
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_ProfilePress {

    public static function init() {
        // 1. Inject pre-fill data + gate check into ticket widget output
        add_filter( 'pbs_ticket_widget_data', [ __CLASS__, 'widget_data' ], 10, 2 );

        // 2. After PBS marks an order complete, grant PP membership if configured
        add_action( 'pbs_order_complete', [ __CLASS__, 'maybe_grant_membership' ], 10, 2 );

        // 3. Apply member discount during server-side amount calculation
        add_filter( 'pbs_order_amount', [ __CLASS__, 'apply_member_discount' ], 10, 3 );

        // 4. Add "My Tickets" tab to PP member account page
        add_filter( 'ppress_myac_tabs', [ __CLASS__, 'add_tickets_tab' ] );
        add_action( 'ppress_myac_tab_content_pbs_tickets', [ __CLASS__, 'render_tickets_tab' ] );

        // 5. Admin: add PP fields to event meta box
        add_action( 'pbs_event_meta_box_fields', [ __CLASS__, 'admin_fields' ] );
        add_action( 'pbs_save_event_meta',        [ __CLASS__, 'save_admin_fields' ], 10, 2 );
    }

    // -------------------------------------------------------------------------
    // 1 & 2. Widget data — gate check + pre-fill
    // -------------------------------------------------------------------------

    /**
     * Filter applied in ticket-widget.php before rendering.
     * Returns array with:
     *   blocked      bool   — show "members only" wall instead of form
     *   block_msg    string — message to show if blocked
     *   prefill_name string — logged-in user's display name
     *   prefill_email string — logged-in user's email
     *   member_discount float — % discount (0 if none)
     *
     * @param array $data    Existing widget data passed from shortcode handler.
     * @param int   $event_id
     */
    public static function widget_data( array $data, int $event_id ): array {
        $required_plan_id = (int) get_post_meta( $event_id, '_pbs_pp_required_plan', true );
        $discount_pct     = (float) get_post_meta( $event_id, '_pbs_pp_member_discount', true );

        $data['blocked']          = false;
        $data['block_msg']        = '';
        $data['prefill_name']     = '';
        $data['prefill_email']    = '';
        $data['member_discount']  = 0;

        // Pre-fill from logged-in user
        if ( is_user_logged_in() ) {
            $user = wp_get_current_user();
            $data['prefill_name']  = trim( $user->first_name . ' ' . $user->last_name ) ?: $user->display_name;
            $data['prefill_email'] = $user->user_email;
        }

        // Gate check
        if ( $required_plan_id ) {
            if ( ! is_user_logged_in() ) {
                $data['blocked']   = true;
                $data['block_msg'] = sprintf(
                    '<p class="pbs-members-only">This event is for members only. <a href="%s">Log in</a> or <a href="%s">join now</a>.</p>',
                    esc_url( ppress_login_url() ),
                    esc_url( ppress_signup_url() )
                );
            } elseif ( ! self::user_has_plan( get_current_user_id(), $required_plan_id ) ) {
                $plan_name = self::get_plan_name( $required_plan_id );
                $data['blocked']   = true;
                $data['block_msg'] = sprintf(
                    '<p class="pbs-members-only">This event requires an active <strong>%s</strong> membership. <a href="%s">Upgrade now</a>.</p>',
                    esc_html( $plan_name ),
                    esc_url( self::get_plan_url( $required_plan_id ) )
                );
            }
        }

        // Member discount
        if ( $discount_pct > 0 && is_user_logged_in() ) {
            if ( ! $required_plan_id || ! $data['blocked'] ) {
                // Apply discount to all logged-in members (or specifically to plan members)
                $discount_plan_id = (int) get_post_meta( $event_id, '_pbs_pp_discount_plan', true );
                $qualifies = ! $discount_plan_id || self::user_has_plan( get_current_user_id(), $discount_plan_id );
                if ( $qualifies ) {
                    $data['member_discount'] = $discount_pct;
                }
            }
        }

        return $data;
    }

    // -------------------------------------------------------------------------
    // 3. Grant PP membership after PBS order completes
    // -------------------------------------------------------------------------

    /**
     * Hooked to `pbs_order_complete` action (fired from PBS_Checkout after
     * PBS_DB::update_order_status( $order_id, 'complete' ) is called).
     *
     * @param int   $order_id PBS order ID.
     * @param array $order    Order row from pbs_orders table.
     */
    public static function maybe_grant_membership( int $order_id, array $order ): void {
        $event_id = (int) ( $order['event_id'] ?? 0 );

        // Per-event plan takes priority; fall back to the global default
        $plan_id = (int) get_post_meta( $event_id, '_pbs_pp_grant_plan', true );
        if ( ! $plan_id ) {
            $plan_id = (int) get_option( 'pbs_pp_default_grant_plan', 0 );
        }
        if ( ! $plan_id ) return;

        // Match order to a WP user by email
        $user = get_user_by( 'email', $order['attendee_email'] ?? '' );
        if ( ! $user ) {
            // Create a WP user so PP can manage their membership
            $username = sanitize_user( explode( '@', $order['attendee_email'] )[0], true );
            $username = self::unique_username( $username );
            $user_id  = wp_create_user( $username, wp_generate_password(), $order['attendee_email'] );
            if ( is_wp_error( $user_id ) ) return;
            wp_update_user( [
                'ID'           => $user_id,
                'display_name' => $order['attendee_name'] ?? $username,
                'first_name'   => self::first_name( $order['attendee_name'] ?? '' ),
                'last_name'    => self::last_name( $order['attendee_name'] ?? '' ),
            ] );
            $user = get_user_by( 'id', $user_id );
        }

        // Don't double-grant if they already have an active subscription to this plan
        if ( self::user_has_plan( $user->ID, $plan_id ) ) return;

        self::grant_plan( $user->ID, $plan_id, $order_id );
    }

    // -------------------------------------------------------------------------
    // 4. Member discount filter
    // -------------------------------------------------------------------------

    /**
     * Reduce the order amount by the configured % discount for active PP members.
     * Hooked to `pbs_order_amount` (must be fired in PBS_Checkout::sanitize_order_input).
     *
     * @param float $amount    Calculated order amount.
     * @param int   $event_id
     * @param int   $user_id   0 if not logged in.
     * @return float
     */
    public static function apply_member_discount( float $amount, int $event_id, int $user_id ): float {
        if ( $amount <= 0 || ! $user_id ) return $amount;

        $discount_pct     = (float) get_post_meta( $event_id, '_pbs_pp_member_discount', true );
        $discount_plan_id = (int)   get_post_meta( $event_id, '_pbs_pp_discount_plan',   true );

        if ( $discount_pct <= 0 ) return $amount;

        $qualifies = ! $discount_plan_id || self::user_has_plan( $user_id, $discount_plan_id );
        if ( ! $qualifies ) return $amount;

        $discount = round( $amount * ( $discount_pct / 100 ), 2 );
        return max( 0.00, $amount - $discount );
    }

    // -------------------------------------------------------------------------
    // 5. PP member account tab
    // -------------------------------------------------------------------------

    public static function add_tickets_tab( array $tabs ): array {
        $tabs['pbs_tickets'] = [
            'title' => __( 'My Tickets', 'pbs-event-commerce' ),
            'icon'  => 'ticket',
        ];
        return $tabs;
    }

    public static function render_tickets_tab(): void {
        $user_id = get_current_user_id();
        if ( ! $user_id ) return;

        $user   = get_user_by( 'id', $user_id );
        $orders = PBS_DB::get_orders( [
            'attendee_email' => $user->user_email,
            'status'         => 'complete',
        ] );

        if ( empty( $orders ) ) {
            echo '<p>' . esc_html__( 'You have no ticket purchases yet.', 'pbs-event-commerce' ) . '</p>';
            return;
        }

        echo '<table class="pbs-my-tickets" style="width:100%;border-collapse:collapse">';
        echo '<thead><tr>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Order #', 'pbs-event-commerce' ) . '</th>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Event', 'pbs-event-commerce' ) . '</th>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Ticket', 'pbs-event-commerce' ) . '</th>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Qty', 'pbs-event-commerce' ) . '</th>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Amount', 'pbs-event-commerce' ) . '</th>
            <th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' . esc_html__( 'Date', 'pbs-event-commerce' ) . '</th>
        </tr></thead><tbody>';

        foreach ( $orders as $order ) {
            $event_title = get_the_title( $order['event_id'] ) ?: '#' . $order['event_id'];
            $token       = substr( wp_hash( $order['order_number'] ), 0, 12 );
            $detail_url  = add_query_arg( [
                'pbs_oid' => $order['id'],
                'pbs_tok' => $token,
            ], get_permalink( get_option( 'pbs_confirmation_page_id', 0 ) ) ?: home_url( '/order-confirmation/' ) );

            printf(
                '<tr>
                    <td style="padding:8px;border-bottom:1px solid #eee"><a href="%s">%s</a></td>
                    <td style="padding:8px;border-bottom:1px solid #eee">%s</td>
                    <td style="padding:8px;border-bottom:1px solid #eee">%s</td>
                    <td style="padding:8px;border-bottom:1px solid #eee">%s</td>
                    <td style="padding:8px;border-bottom:1px solid #eee">$%s</td>
                    <td style="padding:8px;border-bottom:1px solid #eee">%s</td>
                </tr>',
                esc_url( $detail_url ),
                esc_html( $order['order_number'] ),
                esc_html( $event_title ),
                esc_html( $order['ticket_type'] ),
                esc_html( $order['quantity'] ),
                esc_html( number_format( (float) $order['amount'], 2 ) ),
                esc_html( date_i18n( get_option( 'date_format' ), strtotime( $order['created_at'] ) ) )
            );
        }

        echo '</tbody></table>';
    }

    // -------------------------------------------------------------------------
    // Admin: per-event PP settings inside the PBS event meta box
    // -------------------------------------------------------------------------

    public static function admin_fields( int $event_id ): void {
        if ( ! self::profilepress_active() ) return;

        $plans            = self::get_all_plans();
        $required_plan    = (int)   get_post_meta( $event_id, '_pbs_pp_required_plan',    true );
        $grant_plan       = (int)   get_post_meta( $event_id, '_pbs_pp_grant_plan',       true );
        $discount_plan    = (int)   get_post_meta( $event_id, '_pbs_pp_discount_plan',    true );
        $discount_pct     = (float) get_post_meta( $event_id, '_pbs_pp_member_discount',  true );

        ?>
        <tr>
            <th><label>PP: Members-Only Plan</label></th>
            <td>
                <select name="pbs_pp_required_plan">
                    <option value="0">— No restriction —</option>
                    <?php foreach ( $plans as $plan ) : ?>
                        <option value="<?php echo esc_attr( $plan->id ); ?>"
                            <?php selected( $required_plan, $plan->id ); ?>>
                            <?php echo esc_html( $plan->name ); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <p class="description">Only members with this plan can purchase tickets.</p>
            </td>
        </tr>
        <tr>
            <th><label>PP: Grant Plan on Purchase</label></th>
            <td>
                <select name="pbs_pp_grant_plan">
                    <option value="0">— Do not grant —</option>
                    <?php foreach ( $plans as $plan ) : ?>
                        <option value="<?php echo esc_attr( $plan->id ); ?>"
                            <?php selected( $grant_plan, $plan->id ); ?>>
                            <?php echo esc_html( $plan->name ); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <p class="description">Override the global default, or set to "Do not grant" to skip enrollment for this event.</p>
            </td>
        </tr>
        <tr>
            <th><label>PP: Member Discount %</label></th>
            <td>
                <input type="number" name="pbs_pp_member_discount" value="<?php echo esc_attr( $discount_pct ); ?>"
                       min="0" max="100" step="1" style="width:80px"> %
                <select name="pbs_pp_discount_plan" style="margin-left:10px">
                    <option value="0">— Any logged-in member —</option>
                    <?php foreach ( $plans as $plan ) : ?>
                        <option value="<?php echo esc_attr( $plan->id ); ?>"
                            <?php selected( $discount_plan, $plan->id ); ?>>
                            <?php echo esc_html( $plan->name ); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <p class="description">Apply this % discount to the specified PP plan members (0 = off).</p>
            </td>
        </tr>
        <?php
    }

    public static function save_admin_fields( int $event_id, array $post_data ): void {
        update_post_meta( $event_id, '_pbs_pp_required_plan',   (int)   ( $post_data['pbs_pp_required_plan']   ?? 0 ) );
        update_post_meta( $event_id, '_pbs_pp_grant_plan',      (int)   ( $post_data['pbs_pp_grant_plan']      ?? 0 ) );
        update_post_meta( $event_id, '_pbs_pp_discount_plan',   (int)   ( $post_data['pbs_pp_discount_plan']   ?? 0 ) );
        update_post_meta( $event_id, '_pbs_pp_member_discount', (float) ( $post_data['pbs_pp_member_discount'] ?? 0 ) );
    }

    // -------------------------------------------------------------------------
    // ProfilePress helpers
    // -------------------------------------------------------------------------

    public static function profilepress_active(): bool {
        return defined( 'PPRESS_VERSION' ) || function_exists( 'ppress_login_url' );
    }

    /**
     * Check if a user has an active subscription to a specific PP plan.
     */
    public static function user_has_plan( int $user_id, int $plan_id ): bool {
        if ( ! $user_id || ! $plan_id ) return false;

        // ProfilePress 4.x API
        if ( class_exists( '\ProfilePress\Core\Membership\Models\Subscription\SubscriptionFactory' ) ) {
            $subs = \ProfilePress\Core\Membership\Models\Subscription\SubscriptionFactory::get_subscriptions_by_user_id( $user_id );
            foreach ( $subs as $sub ) {
                if ( (int) $sub->plan_id === $plan_id && $sub->is_active() ) {
                    return true;
                }
            }
            return false;
        }

        // Fallback: ProfilePress 3.x / legacy
        if ( function_exists( 'ppress_is_plan_user' ) ) {
            return (bool) ppress_is_plan_user( $plan_id, $user_id );
        }

        return false;
    }

    /**
     * Grant a PP plan to a user by creating a free active subscription.
     */
    private static function grant_plan( int $user_id, int $plan_id, int $pbs_order_id ): void {
        if ( ! class_exists( '\ProfilePress\Core\Membership\Models\Subscription\SubscriptionFactory' ) ) return;

        try {
            $sub = new \ProfilePress\Core\Membership\Models\Subscription\SubscriptionEntity();
            $sub->plan_id    = $plan_id;
            $sub->user_id    = $user_id;
            $sub->status     = \ProfilePress\Core\Membership\Models\Subscription\SubscriptionStatus::ACTIVE;
            $sub->created_date    = current_time( 'mysql' );
            $sub->expiration_date = self::plan_expiry( $plan_id );
            $sub_id = $sub->save();

            // Record the PBS order reference in subscription meta
            if ( $sub_id ) {
                update_metadata( 'ppress_subscriptions', $sub_id, 'pbs_order_id', $pbs_order_id );
            }
        } catch ( \Exception $e ) {
            error_log( 'PBS_ProfilePress::grant_plan error: ' . $e->getMessage() );
        }
    }

    /**
     * Calculate expiry date from a PP plan's billing period.
     */
    private static function plan_expiry( int $plan_id ): string {
        if ( ! class_exists( '\ProfilePress\Core\Membership\Models\Plan\PlanFactory' ) ) {
            return date( 'Y-m-d H:i:s', strtotime( '+1 year' ) );
        }
        $plan = \ProfilePress\Core\Membership\Models\Plan\PlanFactory::fromId( $plan_id );
        if ( ! $plan || ! $plan->billing_frequency ) {
            return date( 'Y-m-d H:i:s', strtotime( '+1 year' ) );
        }
        $freq = $plan->billing_frequency;  // e.g. 'monthly', 'yearly', '3_months'
        $map  = [
            'daily'    => '+1 day',
            'weekly'   => '+1 week',
            'monthly'  => '+1 month',
            'yearly'   => '+1 year',
            'lifetime' => '+100 years',
        ];
        $offset = $map[ $freq ] ?? '+1 year';
        return date( 'Y-m-d H:i:s', strtotime( $offset ) );
    }

    private static function get_all_plans(): array {
        if ( class_exists( '\ProfilePress\Core\Membership\Models\Plan\PlanFactory' ) ) {
            return \ProfilePress\Core\Membership\Models\Plan\PlanFactory::get_plans() ?: [];
        }
        return [];
    }

    private static function get_plan_name( int $plan_id ): string {
        if ( class_exists( '\ProfilePress\Core\Membership\Models\Plan\PlanFactory' ) ) {
            $plan = \ProfilePress\Core\Membership\Models\Plan\PlanFactory::fromId( $plan_id );
            return $plan->name ?? "Plan #{$plan_id}";
        }
        return "Plan #{$plan_id}";
    }

    private static function get_plan_url( int $plan_id ): string {
        if ( function_exists( 'ppress_signup_url' ) ) {
            return ppress_signup_url( $plan_id );
        }
        return home_url( '/register/' );
    }

    // -------------------------------------------------------------------------
    // WP user helpers
    // -------------------------------------------------------------------------

    private static function unique_username( string $base ): string {
        $username = $base;
        $i        = 1;
        while ( username_exists( $username ) ) {
            $username = $base . $i++;
        }
        return $username;
    }

    private static function first_name( string $full ): string {
        $parts = explode( ' ', trim( $full ), 2 );
        return $parts[0] ?? '';
    }

    private static function last_name( string $full ): string {
        $parts = explode( ' ', trim( $full ), 2 );
        return $parts[1] ?? '';
    }
}
