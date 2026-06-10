<?php
/**
 * Tests for server-side order amount calculation in PBS_Checkout::sanitize_order_input().
 * Tests the security-critical spec §19 requirement: order totals never trusted from client.
 */

// Load stubs and the class under test
require_once __DIR__ . '/bootstrap.php';
require_once __DIR__ . '/../includes/class-pbs-checkout.php';

use PHPUnit\Framework\TestCase;

class CheckoutAmountTest extends TestCase {

    protected function setUp(): void {
        PBS_DB::reset();
        $GLOBALS['_pbs_test_options'] = [];
    }

    // ── Fixed-price ticket ────────────────────────────────────────────────────

    public function test_fixed_price_uses_db_price_not_client(): void {
        PBS_DB::$ticket_types['107:General Admission'] = [
            'price' => '75.00', 'is_donation' => '0',
        ];

        // Client sends amount=1 (malicious undercharge)
        $result = $this->call_sanitize( [
            'event_id'    => '107',
            'ticket_type' => 'General Admission',
            'quantity'    => '1',
            'amount'      => '1',        // client lie — should be ignored
            'name'        => 'Alice',
            'email'       => 'alice@example.com',
            'gateway'     => 'stripe',
        ] );

        $this->assertNotInstanceOf( WP_Error::class, $result );
        $this->assertSame( 75.00, $result['amount'] );
    }

    public function test_fixed_price_multiplied_by_quantity(): void {
        PBS_DB::$ticket_types['107:General Admission'] = [
            'price' => '75.00', 'is_donation' => '0',
        ];

        $result = $this->call_sanitize( [
            'event_id'    => '107',
            'ticket_type' => 'General Admission',
            'quantity'    => '3',
            'amount'      => '99999',   // ignored
            'name'        => 'Bob',
            'email'       => 'bob@example.com',
            'gateway'     => 'stripe',
        ] );

        $this->assertNotInstanceOf( WP_Error::class, $result );
        $this->assertSame( 225.00, $result['amount'] ); // 75 * 3
    }

    public function test_fixed_free_ticket_returns_zero(): void {
        PBS_DB::$ticket_types['223:Free RSVP'] = [
            'price' => '0.00', 'is_donation' => '0',
        ];

        $result = $this->call_sanitize( [
            'event_id'    => '223',
            'ticket_type' => 'Free RSVP',
            'quantity'    => '1',
            'amount'      => '50',      // ignored
            'name'        => 'Carol',
            'email'       => 'carol@example.com',
            'gateway'     => 'stripe',
        ] );

        $this->assertNotInstanceOf( WP_Error::class, $result );
        $this->assertSame( 0.00, $result['amount'] );
    }

    // ── Donation ticket ───────────────────────────────────────────────────────

    public function test_donation_uses_client_amount(): void {
        PBS_DB::$ticket_types['222:Custom Donation'] = [
            'price' => '0.00', 'is_donation' => '1',
        ];

        $result = $this->call_sanitize( [
            'event_id'    => '222',
            'ticket_type' => 'Custom Donation',
            'quantity'    => '1',
            'amount'      => '50',
            'name'        => 'Dave',
            'email'       => 'dave@example.com',
            'gateway'     => 'stripe',
        ] );

        $this->assertNotInstanceOf( WP_Error::class, $result );
        $this->assertSame( 50.0, $result['amount'] );
    }

    public function test_donation_minimum_enforced(): void {
        PBS_DB::$ticket_types['222:Custom Donation'] = [
            'price' => '0.00', 'is_donation' => '1',
        ];

        $result = $this->call_sanitize( [
            'event_id'    => '222',
            'ticket_type' => 'Custom Donation',
            'quantity'    => '1',
            'amount'      => '0.50',   // below $1 minimum
            'name'        => 'Eve',
            'email'       => 'eve@example.com',
            'gateway'     => 'stripe',
        ] );

        $this->assertInstanceOf( WP_Error::class, $result );
        $this->assertSame( 'amount', $result->get_error_code() );
    }

    public function test_unknown_ticket_type_rejected(): void {
        // Ticket type not in DB — should reject (not fall back to client amount)
        $result = $this->call_sanitize( [
            'event_id'    => '107',
            'ticket_type' => 'Nonexistent Type',
            'quantity'    => '1',
            'amount'      => '1',
            'name'        => 'Ivan',
            'email'       => 'ivan@example.com',
            'gateway'     => 'stripe',
        ] );
        $this->assertInstanceOf( WP_Error::class, $result );
        $this->assertSame( 'amount', $result->get_error_code() );
    }

    public function test_no_ticket_type_zero_amount_allowed(): void {
        // No ticket_type at all with $0 — allowed (free RSVP flow)
        $result = $this->call_sanitize( [
            'event_id'    => '223',
            'ticket_type' => '',
            'quantity'    => '1',
            'amount'      => '0',
            'name'        => 'Jane',
            'email'       => 'jane@example.com',
            'gateway'     => 'stripe',
        ] );
        $this->assertNotInstanceOf( WP_Error::class, $result );
        $this->assertSame( 0.00, $result['amount'] );
    }

    // ── Input validation ──────────────────────────────────────────────────────

    public function test_invalid_gateway_rejected(): void {
        $result = $this->call_sanitize( [
            'event_id' => '107',
            'name'     => 'Frank',
            'email'    => 'frank@example.com',
            'gateway'  => 'bitcoin',   // not in whitelist
        ] );
        $this->assertInstanceOf( WP_Error::class, $result );
    }

    public function test_missing_event_id_rejected(): void {
        $result = $this->call_sanitize( [
            'name'    => 'George',
            'email'   => 'g@example.com',
            'gateway' => 'stripe',
        ] );
        $this->assertInstanceOf( WP_Error::class, $result );
    }

    public function test_invalid_email_rejected(): void {
        PBS_DB::$ticket_types['107:General Admission'] = [
            'price' => '75.00', 'is_donation' => '0',
        ];
        $result = $this->call_sanitize( [
            'event_id' => '107',
            'name'     => 'Harry',
            'email'    => 'not-an-email',
            'gateway'  => 'stripe',
        ] );
        $this->assertInstanceOf( WP_Error::class, $result );
    }

    // ── Helper ────────────────────────────────────────────────────────────────

    private function call_sanitize( array $post ) {
        // sanitize_order_input is private — use Reflection
        $ref    = new ReflectionClass( PBS_Checkout::class );
        $method = $ref->getMethod( 'sanitize_order_input' );
        $method->setAccessible( true );
        return $method->invoke( null, $post );
    }
}
