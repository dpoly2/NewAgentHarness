<?php
/**
 * Class TRACKSUITE_Payments
 *
 * Handles Stripe Checkout session creation, webhook processing,
 * and manual payment entry for XFTC membership, travel, and meet fees.
 *
 * @package TRACKSUITE_Membership
 * @since   0.2.0
 *
 * ─── STRIPE SETUP REQUIRED ───────────────────────────────────────────────────
 * Before this class will function, you must:
 *
 * 1. Create a Stripe account at https://dashboard.stripe.com/register
 * 2. Retrieve your API keys from https://dashboard.stripe.com/apikeys
 * 3. Add keys to WordPress via WP Admin → Xtreme Force → Settings → Payments:
 *    - Publishable Key (pk_live_... or pk_test_... for testing)
 *    - Secret Key     (sk_live_... or sk_test_... for testing)
 * 4. Set your Webhook Secret from https://dashboard.stripe.com/webhooks
 *    - Endpoint URL: https://xtremeforcetrackclub.org/wp-json/xftc/v1/payments/webhook
 *    - Events to listen for:
 *        checkout.session.completed
 *        payment_intent.payment_failed
 * 5. Install Stripe PHP SDK — add to plugin root:
 *    composer require stripe/stripe-php
 *    OR place stripe-php manually in /vendor/stripe/stripe-php/
 * ─────────────────────────────────────────────────────────────────────────────
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

class TRACKSUITE_Payments {

    /**
     * Stripe Publishable Key (from WP options).
     * Set via WP Admin → Xtreme Force → Settings → Payments.
     */
    private string $publishable_key;

    /**
     * Stripe Secret Key (from WP options).
     * NEVER expose this on the front end.
     */
    private string $secret_key;

    /**
     * Stripe Webhook Signing Secret (from WP options).
     * Used to verify webhook payloads from Stripe.
     */
    private string $webhook_secret;

    /**
     * Test mode flag. When true, uses test keys and test mode behavior.
     */
    private bool $test_mode;

    public function __construct() {
        $this->test_mode       = (bool) get_option( 'TRACKSUITE_stripe_test_mode', true );
        $this->publishable_key = $this->test_mode
            ? get_option( 'TRACKSUITE_stripe_test_publishable_key', '' )
            : get_option( 'TRACKSUITE_stripe_live_publishable_key', '' );
        $this->secret_key      = $this->test_mode
            ? get_option( 'TRACKSUITE_stripe_test_secret_key', '' )
            : get_option( 'TRACKSUITE_stripe_live_secret_key', '' );
        $this->webhook_secret  = get_option( 'TRACKSUITE_stripe_webhook_secret', '' );
    }

    /**
     * Check if Stripe is configured and ready to use.
     *
     * @return bool
     */
    public function is_configured(): bool {
        return ! empty( $this->secret_key ) && ! empty( $this->publishable_key );
    }

    /**
     * Load the Stripe PHP SDK.
     * Looks for Composer autoloader first, then manual vendor path.
     *
     * @return bool True if SDK loaded successfully.
     */
    private function load_stripe_sdk(): bool {
        // Composer autoloader (preferred)
        $composer_autoload = TRACKSUITE_PLUGIN_DIR . 'vendor/autoload.php';
        if ( file_exists( $composer_autoload ) ) {
            require_once $composer_autoload;
            return true;
        }

        // Manual SDK path fallback
        $manual_sdk = TRACKSUITE_PLUGIN_DIR . 'vendor/stripe/stripe-php/init.php';
        if ( file_exists( $manual_sdk ) ) {
            require_once $manual_sdk;
            return true;
        }

        error_log( 'XFTC Payments: Stripe PHP SDK not found. Install via Composer or place in /vendor/stripe/stripe-php/' );
        return false;
    }

    /**
     * Create a Stripe Checkout Session.
     *
     * @param array $args {
     *   @type string $type        Payment type: 'membership' | 'travel' | 'meet_entry' | 'other'
     *   @type int    $reference_id  ID of the related record (membership_id, travel_id, etc.)
     *   @type int    $user_id     WP user ID of the payer
     *   @type float  $amount      Amount in dollars (e.g. 150.00)
     *   @type string $description Line item description shown to payer
     *   @type string $success_url URL to redirect after successful payment
     *   @type string $cancel_url  URL to redirect if user cancels
     * }
     * @return array|WP_Error Stripe session data or WP_Error on failure.
     */
    public function create_checkout_session( array $args ): array|\WP_Error {
        // ── PLACEHOLDER ──────────────────────────────────────────────────────
        // This method will create a Stripe Checkout session when keys are set.
        // Replace the placeholder block below with live Stripe SDK calls.
        // ─────────────────────────────────────────────────────────────────────

        if ( ! $this->is_configured() ) {
            return new \WP_Error(
                'stripe_not_configured',
                'Stripe API keys are not set. Go to WP Admin → Xtreme Force → Settings → Payments to configure.'
            );
        }

        if ( ! $this->load_stripe_sdk() ) {
            return new \WP_Error( 'stripe_sdk_missing', 'Stripe PHP SDK is not installed.' );
        }

        // TODO: Implement Stripe Checkout Session creation
        // ── BEGIN IMPLEMENTATION BLOCK ────────────────────────────────────
        // \Stripe\Stripe::setApiKey( $this->secret_key );
        //
        // $session = \Stripe\Checkout\Session::create([
        //     'payment_method_types' => ['card'],
        //     'line_items' => [[
        //         'price_data' => [
        //             'currency'     => 'usd',
        //             'unit_amount'  => (int) ( $args['amount'] * 100 ),
        //             'product_data' => ['name' => $args['description']],
        //         ],
        //         'quantity' => 1,
        //     ]],
        //     'mode'        => 'payment',
        //     'success_url' => $args['success_url'],
        //     'cancel_url'  => $args['cancel_url'],
        //     'metadata'    => [
        //         'TRACKSUITE_type'         => $args['type'],
        //         'TRACKSUITE_reference_id' => $args['reference_id'],
        //         'TRACKSUITE_user_id'      => $args['user_id'],
        //     ],
        // ]);
        //
        // $this->log_payment_pending( $args, $session->id );
        // return ['session_id' => $session->id, 'url' => $session->url];
        // ── END IMPLEMENTATION BLOCK ──────────────────────────────────────

        return new \WP_Error( 'stripe_placeholder', 'Stripe Checkout not yet implemented. Add API keys and uncomment the implementation block.' );
    }

    /**
     * Handle incoming Stripe webhook events.
     * Registered as REST endpoint: POST /wp-json/xftc/v1/payments/webhook
     *
     * @param \WP_REST_Request $request
     * @return \WP_REST_Response
     */
    public function handle_webhook( \WP_REST_Request $request ): \WP_REST_Response {
        // ── PLACEHOLDER ──────────────────────────────────────────────────────
        // This handler will verify and process Stripe webhook events.
        // Uncomment the implementation block after SDK is installed.
        // ─────────────────────────────────────────────────────────────────────

        if ( ! $this->load_stripe_sdk() ) {
            return new \WP_REST_Response( ['error' => 'Stripe SDK missing'], 500 );
        }

        $payload    = $request->get_body();
        $sig_header = $_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '';

        // TODO: Verify and process webhook
        // ── BEGIN IMPLEMENTATION BLOCK ────────────────────────────────────
        // try {
        //     $event = \Stripe\Webhook::constructEvent( $payload, $sig_header, $this->webhook_secret );
        // } catch ( \Exception $e ) {
        //     return new \WP_REST_Response( ['error' => $e->getMessage()], 400 );
        // }
        //
        // switch ( $event->type ) {
        //     case 'checkout.session.completed':
        //         $this->handle_payment_completed( $event->data->object );
        //         break;
        //     case 'payment_intent.payment_failed':
        //         $this->handle_payment_failed( $event->data->object );
        //         break;
        // }
        //
        // return new \WP_REST_Response( ['status' => 'ok'], 200 );
        // ── END IMPLEMENTATION BLOCK ──────────────────────────────────────

        return new \WP_REST_Response( ['status' => 'placeholder — webhook not yet active'], 200 );
    }

    /**
     * Mark a payment as completed after webhook confirmation.
     * Updates wp_ts_payments, wp_ts_memberships, and wp_ts_travel as needed.
     *
     * @param object $session Stripe Checkout Session object
     */
    private function handle_payment_completed( object $session ): void {
        // TODO: Implement after Stripe keys are configured
        // global $wpdb;
        //
        // $meta        = $session->metadata;
        // $type        = $meta->TRACKSUITE_type;
        // $ref_id      = $meta->TRACKSUITE_reference_id;
        // $transaction = $session->payment_intent;
        // $amount      = $session->amount_total / 100;
        //
        // $wpdb->update( "{$wpdb->prefix}TRACKSUITE_payments",
        //     ['status' => 'completed', 'transaction_id' => $transaction],
        //     ['reference_type' => $type, 'reference_id' => $ref_id]
        // );
        //
        // if ( $type === 'membership' ) {
        //     $wpdb->update( "{$wpdb->prefix}TRACKSUITE_memberships",
        //         ['payment_status' => 'paid', 'amount_paid' => $amount],
        //         ['id' => $ref_id]
        //     );
        // } elseif ( $type === 'travel' ) {
        //     $wpdb->update( "{$wpdb->prefix}TRACKSUITE_travel",
        //         ['payment_status' => 'paid'],
        //         ['id' => $ref_id]
        //     );
        // }
        //
        // // Send receipt email
        // $emails = new TRACKSUITE_Emails();
        // $emails->send_payment_receipt( $ref_id, $type, $amount );
    }

    /**
     * Handle a failed payment event from Stripe.
     *
     * @param object $intent Stripe PaymentIntent object
     */
    private function handle_payment_failed( object $intent ): void {
        // TODO: Implement after Stripe keys are configured
        // Log failure, notify admin, update payment record status to 'failed'
    }

    /**
     * Log a pending payment record to wp_ts_payments.
     *
     * @param array  $args       Payment args passed to create_checkout_session()
     * @param string $session_id Stripe session ID
     */
    private function log_payment_pending( array $args, string $session_id ): void {
        // TODO: Implement DB insert
        // global $wpdb;
        // $wpdb->insert( "{$wpdb->prefix}TRACKSUITE_payments", [
        //     'user_id'        => $args['user_id'],
        //     'reference_type' => $args['type'],
        //     'reference_id'   => $args['reference_id'],
        //     'amount'         => $args['amount'],
        //     'gateway'        => 'stripe',
        //     'transaction_id' => $session_id,
        //     'status'         => 'pending',
        //     'created_at'     => current_time( 'mysql' ),
        // ]);
    }

    /**
     * Record a manual payment (cash/check) entered by admin.
     *
     * @param array $args {
     *   @type int    $user_id       WP user ID
     *   @type string $type          'membership' | 'travel' | 'other'
     *   @type int    $reference_id  Related record ID
     *   @type float  $amount        Amount received
     *   @type string $notes         Optional notes (e.g. "Check #1042")
     * }
     * @return int|false Inserted record ID or false on failure.
     */
    public function record_manual_payment( array $args ): int|false {
        global $wpdb;

        // TODO: Uncomment when DB tables are confirmed active
        // return $wpdb->insert( "{$wpdb->prefix}TRACKSUITE_payments", [
        //     'user_id'        => $args['user_id'],
        //     'reference_type' => $args['type'],
        //     'reference_id'   => $args['reference_id'],
        //     'amount'         => $args['amount'],
        //     'gateway'        => 'manual',
        //     'transaction_id' => 'MANUAL-' . time(),
        //     'status'         => 'completed',
        //     'created_at'     => current_time( 'mysql' ),
        // ]) ? $wpdb->insert_id : false;

        return false; // Placeholder
    }

    /**
     * Get the Stripe publishable key for use in front-end JS.
     *
     * @return string
     */
    public function get_publishable_key(): string {
        return $this->publishable_key;
    }

    /**
     * Return payment history for a given user.
     *
     * @param int $user_id
     * @return array
     */
    public function get_payment_history( int $user_id ): array {
        global $wpdb;
        // TODO: Uncomment when DB is active
        // return $wpdb->get_results( $wpdb->prepare(
        //     "SELECT * FROM {$wpdb->prefix}TRACKSUITE_payments WHERE user_id = %d ORDER BY created_at DESC",
        //     $user_id
        // ), ARRAY_A );
        return []; // Placeholder
    }
}

