<?php
/**
 * PHPUnit bootstrap — stubs out WordPress globals so unit tests can run
 * without a live WordPress install.
 */

// ── WordPress constant stubs ──────────────────────────────────────────────────
if ( ! defined( 'ABSPATH' ) )          define( 'ABSPATH', __DIR__ . '/../' );
if ( ! defined( 'PBS_EC_VERSION' ) )   define( 'PBS_EC_VERSION', '2.1.0' );
if ( ! defined( 'PBS_EC_PATH' ) )      define( 'PBS_EC_PATH', dirname( __DIR__ ) . '/' );
if ( ! defined( 'PBS_EC_URL' ) )       define( 'PBS_EC_URL', 'http://localhost/' );
if ( ! defined( 'MINUTE_IN_SECONDS' ) ) define( 'MINUTE_IN_SECONDS', 60 );
if ( ! defined( 'DAY_IN_SECONDS' ) )    define( 'DAY_IN_SECONDS', 86400 );

// ── WordPress function stubs ──────────────────────────────────────────────────
if ( ! function_exists( 'sanitize_text_field' ) ) {
    function sanitize_text_field( $str ) { return trim( strip_tags( (string) $str ) ); }
}
if ( ! function_exists( 'sanitize_email' ) ) {
    function sanitize_email( $email ) { return filter_var( (string) $email, FILTER_SANITIZE_EMAIL ); }
}
if ( ! function_exists( 'sanitize_key' ) ) {
    function sanitize_key( $key ) { return preg_replace( '/[^a-z0-9_-]/', '', strtolower( (string) $key ) ); }
}
if ( ! function_exists( 'is_email' ) ) {
    function is_email( $email ) { return filter_var( (string) $email, FILTER_VALIDATE_EMAIL ) !== false; }
}
if ( ! function_exists( 'wp_json_encode' ) ) {
    function wp_json_encode( $data ) { return json_encode( $data ); }
}
if ( ! function_exists( 'wp_generate_password' ) ) {
    function wp_generate_password( $len = 12, $special = true ) { return bin2hex( random_bytes( (int) ceil( $len / 2 ) ) ); }
}
if ( ! function_exists( 'wp_generate_uuid4' ) ) {
    function wp_generate_uuid4() { return sprintf( '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        random_int(0,0xffff), random_int(0,0xffff), random_int(0,0xffff),
        random_int(0x4000,0x4fff), random_int(0x8000,0xbfff),
        random_int(0,0xffff), random_int(0,0xffff), random_int(0,0xffff) ); }
}
if ( ! function_exists( 'get_option' ) ) {
    function get_option( $key, $default = false ) { return $GLOBALS['_pbs_test_options'][$key] ?? $default; }
}
if ( ! function_exists( 'update_option' ) ) {
    function update_option( $key, $value ) { $GLOBALS['_pbs_test_options'][$key] = $value; return true; }
}
if ( ! function_exists( 'delete_option' ) ) {
    function delete_option( $key ) { unset( $GLOBALS['_pbs_test_options'][$key] ); return true; }
}
if ( ! function_exists( 'rest_url' ) ) {
    function rest_url( $path = '' ) { return 'https://example.com/wp-json/' . ltrim( $path, '/' ); }
}
if ( ! function_exists( 'number_format' ) ) {
    // PHP built-in — already exists; this guard is just for safety
}
if ( ! function_exists( 'hash_equals' ) ) {
    // PHP built-in — already exists
}
if ( ! function_exists( 'wp_remote_post' ) ) {
    function wp_remote_post( $url, $args = [] ) { return []; }
}
if ( ! function_exists( 'wp_remote_get' ) ) {
    function wp_remote_get( $url, $args = [] ) { return []; }
}
if ( ! function_exists( 'wp_remote_retrieve_body' ) ) {
    function wp_remote_retrieve_body( $response ) { return $response['body'] ?? '{}'; }
}
if ( ! function_exists( 'wp_remote_retrieve_response_code' ) ) {
    function wp_remote_retrieve_response_code( $response ) { return $response['code'] ?? 200; }
}
if ( ! function_exists( 'is_wp_error' ) ) {
    function is_wp_error( $thing ) { return $thing instanceof WP_Error; }
}
if ( ! function_exists( 'add_query_arg' ) ) {
    function add_query_arg( $args, $url = '' ) { return $url . '?' . http_build_query( $args ); }
}
if ( ! function_exists( 'home_url' ) ) {
    function home_url( $path = '' ) { return 'https://example.com' . $path; }
}
if ( ! function_exists( 'set_transient' ) ) {
    function set_transient( $key, $value, $exp = 0 ) { $GLOBALS['_pbs_test_transients'][$key] = $value; return true; }
}
if ( ! function_exists( 'get_transient' ) ) {
    function get_transient( $key ) { return $GLOBALS['_pbs_test_transients'][$key] ?? false; }
}
if ( ! function_exists( 'delete_transient' ) ) {
    function delete_transient( $key ) { unset( $GLOBALS['_pbs_test_transients'][$key] ); return true; }
}
if ( ! function_exists( 'error_log' ) ) {
    // PHP built-in — already exists
}
if ( ! function_exists( 'base64_encode' ) ) {
    // PHP built-in — already exists
}

// ── WP_Error stub ─────────────────────────────────────────────────────────────
if ( ! class_exists( 'WP_Error' ) ) {
    class WP_Error {
        public string $code;
        public string $message;
        public function __construct( string $code = '', string $message = '' ) {
            $this->code    = $code;
            $this->message = $message;
        }
        public function get_error_code(): string    { return $this->code; }
        public function get_error_message(): string { return $this->message; }
    }
}

// ── WP_REST_Request / WP_REST_Response stubs ─────────────────────────────────
if ( ! class_exists( 'WP_REST_Request' ) ) {
    class WP_REST_Request {
        private array $headers = [];
        private array $params  = [];
        private string $body   = '';
        private string $route  = '';
        public function __construct( string $method = 'GET', string $route = '', array $params = [], array $headers = [], string $body = '' ) {
            $this->route   = $route;
            $this->params  = $params;
            $this->headers = array_change_key_case( $headers, CASE_LOWER );
            $this->body    = $body;
        }
        public function get_header( string $key ): ?string { return $this->headers[ strtolower( $key ) ] ?? null; }
        public function get_param( string $key ) { return $this->params[$key] ?? null; }
        public function get_body(): string { return $this->body; }
        public function get_route(): string { return $this->route; }
    }
}
if ( ! class_exists( 'WP_REST_Response' ) ) {
    class WP_REST_Response {
        public array $data;
        public int   $status;
        public function __construct( array $data = [], int $status = 200 ) {
            $this->data   = $data;
            $this->status = $status;
        }
    }
}
if ( ! class_exists( 'WP_REST_Server' ) ) {
    class WP_REST_Server {
        const CREATABLE = 'POST';
    }
}

// ── PBS_DB stub ───────────────────────────────────────────────────────────────
if ( ! class_exists( 'PBS_DB' ) ) {
    class PBS_DB {
        public static array $ticket_types = [];
        public static array $orders       = [];

        public static function get_ticket_type_by_name( int $event_id, string $name ): ?array {
            return self::$ticket_types["{$event_id}:{$name}"] ?? null;
        }

        public static function get_order( int $id ): ?array {
            return self::$orders[$id] ?? null;
        }

        public static function update_order_status( int $id, string $status, string $payment_id = '' ): void {
            if ( isset( self::$orders[$id] ) ) {
                self::$orders[$id]['status']     = $status;
                self::$orders[$id]['payment_id'] = $payment_id;
            }
        }

        public static function reset(): void {
            self::$ticket_types = [];
            self::$orders       = [];
        }
    }
}
