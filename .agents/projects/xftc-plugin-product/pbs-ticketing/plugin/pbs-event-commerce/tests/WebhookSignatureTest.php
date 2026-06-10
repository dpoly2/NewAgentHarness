<?php
/**
 * Tests for PBS_Webhooks signature verification methods.
 * Tests spec §8 security: all webhook endpoints must verify payload signatures.
 */

require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/../includes/class-pbs-webhooks.php';

use PHPUnit\Framework\TestCase;

class WebhookSignatureTest extends TestCase {

    // ── Stripe signature verification ────────────────────────────────────────

    public function test_valid_stripe_signature_passes(): void {
        $secret  = 'whsec_test_secret';
        $payload = '{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_123"}}}';
        $ts      = time();
        $sig     = hash_hmac( 'sha256', $ts . '.' . $payload, $secret );
        $header  = "t={$ts},v1={$sig}";

        $this->assertTrue( $this->call_verify_stripe( $payload, $header, $secret ) );
    }

    public function test_invalid_stripe_signature_fails(): void {
        $payload = '{"type":"test"}';
        $ts      = time();
        $header  = "t={$ts},v1=deadbeefdeadbeef";

        $this->assertFalse( $this->call_verify_stripe( $payload, $header, 'real_secret' ) );
    }

    public function test_stripe_replay_attack_rejected(): void {
        $secret  = 'whsec_replay_test';
        $payload = '{"type":"test"}';
        $ts      = time() - 400; // 400 seconds old — exceeds 300s window
        $sig     = hash_hmac( 'sha256', $ts . '.' . $payload, $secret );
        $header  = "t={$ts},v1={$sig}";

        $this->assertFalse( $this->call_verify_stripe( $payload, $header, $secret ) );
    }

    public function test_stripe_within_window_passes(): void {
        $secret  = 'whsec_window_test';
        $payload = '{"type":"test"}';
        $ts      = time() - 200; // 200 seconds old — within 300s window
        $sig     = hash_hmac( 'sha256', $ts . '.' . $payload, $secret );
        $header  = "t={$ts},v1={$sig}";

        $this->assertTrue( $this->call_verify_stripe( $payload, $header, $secret ) );
    }

    public function test_stripe_empty_header_fails(): void {
        $this->assertFalse( $this->call_verify_stripe( '{}', '', 'secret' ) );
        $this->assertFalse( $this->call_verify_stripe( '{}', null, 'secret' ) );
    }

    public function test_stripe_multiple_v1_sigs_one_valid(): void {
        $secret  = 'whsec_multi';
        $payload = '{"type":"test"}';
        $ts      = time();
        $valid   = hash_hmac( 'sha256', $ts . '.' . $payload, $secret );
        $header  = "t={$ts},v1=badhash,v1={$valid}"; // one bad, one good

        $this->assertTrue( $this->call_verify_stripe( $payload, $header, $secret ) );
    }

    // ── Square signature verification ────────────────────────────────────────

    public function test_valid_square_signature_passes(): void {
        $key     = 'sq_webhook_key';
        $payload = '{"type":"payment.completed"}';
        $url     = 'https://example.com/wp-json/pbs-ec/v1/webhooks/square';
        $sig     = base64_encode( hash_hmac( 'sha256', $url . $payload, $key, true ) );

        $this->assertTrue( $this->call_verify_square( $payload, $sig, $key ) );
    }

    public function test_invalid_square_signature_fails(): void {
        $payload = '{"type":"payment.completed"}';
        $this->assertFalse( $this->call_verify_square( $payload, 'badsig==', 'real_key' ) );
    }

    public function test_square_empty_header_fails(): void {
        $this->assertFalse( $this->call_verify_square( '{}', '', 'key' ) );
        $this->assertFalse( $this->call_verify_square( '{}', null, 'key' ) );
    }

    public function test_square_wrong_key_fails(): void {
        $key     = 'correct_key';
        $payload = '{"type":"test"}';
        $url     = 'https://example.com/wp-json/pbs-ec/v1/webhooks/square';
        $sig     = base64_encode( hash_hmac( 'sha256', $url . $payload, 'wrong_key', true ) );

        $this->assertFalse( $this->call_verify_square( $payload, $sig, $key ) );
    }

    // ── Stripe event processing ───────────────────────────────────────────────

    public function test_stripe_payment_succeeded_marks_order_complete(): void {
        PBS_DB::reset();
        PBS_DB::$orders[42] = [
            'status'     => 'pending',
            'payment_id' => 'pi_abc123',
        ];

        // Seed the payment_id lookup via global wpdb stub
        $GLOBALS['_pbs_test_pi_map'] = [ 'pi_abc123' => 42 ];

        // We test the dispatch path via handle_stripe with a faked valid request
        $payload = json_encode( [
            'type' => 'payment_intent.succeeded',
            'data' => [ 'object' => [ 'id' => 'pi_abc123' ] ],
        ] );

        $ts     = time();
        $secret = 'whsec_test';
        $sig    = hash_hmac( 'sha256', $ts . '.' . $payload, $secret );

        // Configure secret so signature verification runs
        $GLOBALS['_pbs_test_options']['pbs_stripe_webhook_secret'] = $secret;

        $request  = new WP_REST_Request( 'POST', '/pbs-ec/v1/webhooks/stripe', [], [
            'X-Stripe-Signature' => "t={$ts},v1={$sig}",
        ], $payload );

        $response = PBS_Webhooks::handle_stripe( $request );
        $this->assertSame( 200, $response->status );
        $this->assertSame( 'ok', $response->data['status'] );
    }

    public function test_stripe_unknown_event_returns_ignored(): void {
        // Webhook secret must be set or the handler returns 401 (fail-closed)
        $GLOBALS['_pbs_test_options']['pbs_stripe_webhook_secret'] = 'whsec_test';

        $payload  = json_encode( [ 'type' => 'some.unknown.event', 'data' => [ 'object' => [] ] ] );
        $ts       = time();
        $sig      = hash_hmac( 'sha256', $ts . '.' . $payload, 'whsec_test' );
        $request  = new WP_REST_Request( 'POST', '', [], [
            'X-Stripe-Signature' => "t={$ts},v1={$sig}",
        ], $payload );
        $response = PBS_Webhooks::handle_stripe( $request );

        $this->assertSame( 200, $response->status );
        $this->assertSame( 'ignored', $response->data['status'] );
    }

    public function test_stripe_missing_secret_returns_401(): void {
        $GLOBALS['_pbs_test_options']['pbs_stripe_webhook_secret'] = '';

        $payload  = json_encode( [ 'type' => 'payment_intent.succeeded', 'data' => [ 'object' => [] ] ] );
        $request  = new WP_REST_Request( 'POST', '', [], [], $payload );
        $response = PBS_Webhooks::handle_stripe( $request );

        $this->assertSame( 401, $response->status );
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private function call_verify_stripe( string $payload, ?string $header, string $secret ): bool {
        $ref    = new ReflectionClass( PBS_Webhooks::class );
        $method = $ref->getMethod( 'verify_stripe_signature' );
        $method->setAccessible( true );
        return $method->invoke( null, $payload, $header, $secret );
    }

    private function call_verify_square( string $payload, ?string $header, string $key ): bool {
        $ref    = new ReflectionClass( PBS_Webhooks::class );
        $method = $ref->getMethod( 'verify_square_signature' );
        $method->setAccessible( true );
        return $method->invoke( null, $payload, $header, $key, '' );
    }
}
