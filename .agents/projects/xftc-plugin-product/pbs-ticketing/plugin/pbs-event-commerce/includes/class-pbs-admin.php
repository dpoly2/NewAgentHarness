<?php
if ( ! defined( 'ABSPATH' ) ) exit;

class PBS_Admin {

    public static function init() {
        add_action( 'admin_menu',             [ __CLASS__, 'register_menu' ] );
        add_action( 'admin_init',             [ __CLASS__, 'register_settings' ] );
        add_action( 'admin_enqueue_scripts',  [ __CLASS__, 'enqueue_admin_assets' ] );
        add_action( 'admin_post_pbs_create_confirmation_page', [ __CLASS__, 'create_confirmation_page' ] );
        add_action( 'admin_post_pbs_resend_confirmation',      [ __CLASS__, 'resend_confirmation' ] );
        add_action( 'admin_post_pbs_print_receipt',            [ __CLASS__, 'print_receipt' ] );
    }

    /**
     * Auto-create the Order Confirmation page with [pbs_order_summary] shortcode.
     * Called by the "Create Confirmation Page" button in Settings.
     */
    public static function create_confirmation_page() {
        if ( ! current_user_can( 'manage_options' ) ) wp_die( 'Unauthorized' );
        check_admin_referer( 'pbs_create_confirmation_page' );

        // Don't create if already exists
        $existing = (int) get_option( 'pbs_confirmation_page_id', 0 );
        if ( $existing && get_post( $existing ) ) {
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&conf_page=exists' ) );
            exit;
        }

        $page_id = wp_insert_post( [
            'post_title'   => 'Order Confirmation',
            'post_name'    => 'order-confirmation',
            'post_content' => '<!-- wp:shortcode -->[pbs_order_summary]<!-- /wp:shortcode -->',
            'post_status'  => 'publish',
            'post_type'    => 'page',
            'post_author'  => get_current_user_id(),
        ] );

        if ( $page_id && ! is_wp_error( $page_id ) ) {
            update_option( 'pbs_confirmation_page_id', $page_id );
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&conf_page=created' ) );
        } else {
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce-settings&conf_page=error' ) );
        }
        exit;
    }

    public static function register_menu() {
        add_menu_page( 'PBS Commerce', 'PBS Commerce', 'manage_options', 'pbs-commerce', [ __CLASS__, 'orders_page' ], 'dashicons-tickets-alt', 30 );
        add_submenu_page( 'pbs-commerce', 'Orders',       'Orders',       'manage_options', 'pbs-commerce',          [ __CLASS__, 'orders_page' ] );
        add_submenu_page( 'pbs-commerce', 'Ticket Types', 'Ticket Types', 'manage_options', 'pbs-ticket-types',      [ __CLASS__, 'ticket_types_page' ] );
        add_submenu_page( 'pbs-commerce', 'Attendees',    'Attendees',    'manage_options', 'pbs-attendees',         [ __CLASS__, 'attendees_page' ] );
        add_submenu_page( 'pbs-commerce', 'Settings',     'Settings',     'manage_options', 'pbs-commerce-settings', [ __CLASS__, 'settings_page' ] );
    }

    public static function register_settings() {
        $options = [
            // Stripe
            'pbs_stripe_enabled', 'pbs_stripe_publishable_key', 'pbs_stripe_secret_key',
            'pbs_stripe_webhook_secret', 'pbs_stripe_connect_client_id', 'pbs_stripe_mode',
            'pbs_stripe_user_id',
            // Square
            'pbs_square_enabled', 'pbs_square_app_id', 'pbs_square_location_id',
            'pbs_square_access_token', 'pbs_square_env', 'pbs_square_app_secret',
            'pbs_square_webhook_signature_key',
            // PayPal
            'pbs_paypal_enabled', 'pbs_paypal_client_id', 'pbs_paypal_secret',
            'pbs_paypal_mode', 'pbs_paypal_venmo', 'pbs_paypal_merchant_email',
            'pbs_paypal_payer_id', 'pbs_paypal_webhook_id',
            // Email
            'pbs_email_from', 'pbs_email_from_name', 'pbs_email_bcc',
            'pbs_treasurer_email', 'pbs_email_reminders',
            // Checkout
            'pbs_confirmation_page_id', 'pbs_donor_covers_fees', 'pbs_tax_receipts',
            'pbs_max_tickets', 'pbs_org_ein',
        ];
        foreach ( $options as $opt ) {
            register_setting( 'pbs_commerce_settings', $opt );
        }
    }

    public static function enqueue_admin_assets( $hook ) {
        if ( strpos( $hook, 'pbs-commerce' ) === false && strpos( $hook, 'pbs-ticket' ) === false ) return;
        wp_enqueue_style( 'pbs-admin', PBS_EC_URL . 'assets/css/pbs-tickets.css', [], PBS_EC_VERSION );
        wp_register_script( 'pbs-admin', false, [ 'jquery' ], PBS_EC_VERSION, true );
        wp_enqueue_script( 'pbs-admin' );
        wp_localize_script( 'pbs-admin', 'PBS_Admin', [
            'nonce'    => wp_create_nonce( 'pbs_admin_nonce' ),
            'ajax_url' => admin_url( 'admin-ajax.php' ),
        ] );
    }

    /** Helper: return array of enabled gateway slugs */
    public static function enabled_gateways() {
        $gateways = [];
        if ( get_option('pbs_stripe_enabled') && get_option('pbs_stripe_secret_key') )    $gateways[] = 'stripe';
        if ( get_option('pbs_square_enabled') && PBS_Square::get_valid_token()
             && ( get_option('pbs_square_location_id') || true ) )                         $gateways[] = 'square';
        if ( get_option('pbs_paypal_enabled') && get_option('pbs_paypal_client_id') )     $gateways[] = 'paypal';
        return $gateways;
    }

    public static function orders_page() {
        $msg = isset( $_GET['msg'] ) ? sanitize_key( $_GET['msg'] ) : '';
        $event_filter  = isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0;
        $status_filter = sanitize_text_field( $_GET['status'] ?? '' );
        $orders = PBS_DB::get_orders( array_filter( [ 'event_id' => $event_filter, 'status' => $status_filter ] ) );
        include PBS_EC_PATH . 'admin/views/orders.php';
    }

    /** Resend confirmation email to the attendee */
    public static function resend_confirmation() {
        if ( ! current_user_can( 'manage_options' ) ) wp_die( 'Unauthorized' );
        check_admin_referer( 'pbs_resend_confirmation' );

        $order_id = (int) ( $_POST['order_id'] ?? 0 );
        $order    = $order_id ? PBS_DB::get_order( $order_id ) : null;

        if ( ! $order ) {
            wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce&msg=order_not_found' ) );
            exit;
        }

        PBS_Email::send_confirmation( $order );
        wp_safe_redirect( admin_url( 'admin.php?page=pbs-commerce&msg=email_sent&order=' . $order_id ) );
        exit;
    }

    /** Render a printable receipt for an order */
    public static function print_receipt() {
        if ( ! current_user_can( 'manage_options' ) ) wp_die( 'Unauthorized' );

        $order_id = isset( $_GET['order_id'] ) ? (int) $_GET['order_id'] : 0;
        $nonce    = isset( $_GET['_wpnonce'] ) ? $_GET['_wpnonce'] : '';
        if ( ! wp_verify_nonce( $nonce, 'pbs_print_receipt_' . $order_id ) ) wp_die( 'Invalid request' );

        $order = $order_id ? PBS_DB::get_order( $order_id ) : null;
        if ( ! $order ) wp_die( 'Order not found.' );

        $event_title = get_the_title( $order['event_id'] ) ?: 'Event #' . $order['event_id'];
        $qr_img      = class_exists( 'PBS_QR' ) ? PBS_QR::qr_img( $order['id'], $order['order_number'], 140 ) : '';
        $org_name    = get_option( 'pbs_email_from_name', 'Psi Beta Sigma 1914' );
        $org_ein     = get_option( 'pbs_org_ein', '' );

        // Output printable receipt — standalone HTML, no WP chrome
        header( 'Content-Type: text/html; charset=UTF-8' );
        echo '<!DOCTYPE html><html><head><meta charset="UTF-8">
        <title>Receipt — ' . esc_html( $order['order_number'] ) . '</title>
        <style>
          body{font-family:Arial,sans-serif;max-width:680px;margin:40px auto;padding:20px;color:#333;}
          h1{color:#164f90;margin-bottom:4px;} .sub{color:#666;font-size:14px;margin-bottom:24px;}
          table{width:100%;border-collapse:collapse;margin-bottom:20px;}
          th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #eee;}
          th{background:#f5f5f5;width:180px;}
          .qr{text-align:center;margin:24px 0;padding:20px;border:2px dashed #164f90;border-radius:8px;}
          .footer{font-size:12px;color:#999;text-align:center;margin-top:32px;border-top:1px solid #eee;padding-top:16px;}
          @media print{.no-print{display:none;}}
        </style></head><body>
        <div class="no-print" style="margin-bottom:20px;">
          <button onclick="window.print()" style="padding:8px 20px;background:#164f90;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:14px;">🖨️ Print / Save PDF</button>
          <button onclick="window.close()" style="margin-left:8px;padding:8px 16px;cursor:pointer;">Close</button>
        </div>
        <h1>' . esc_html( $org_name ) . '</h1>
        <div class="sub">Payment Receipt</div>
        <table>
          <tr><th>Order #</th><td><strong>' . esc_html( $order['order_number'] ) . '</strong></td></tr>
          <tr><th>Date</th><td>' . esc_html( date( 'F j, Y g:i A', strtotime( $order['created_at'] ) ) ) . '</td></tr>
          <tr><th>Event</th><td>' . esc_html( $event_title ) . '</td></tr>
          <tr><th>Ticket Type</th><td>' . esc_html( $order['ticket_type'] ) . '</td></tr>
          <tr><th>Quantity</th><td>' . esc_html( $order['quantity'] ) . '</td></tr>
          <tr><th>Amount Paid</th><td><strong>$' . number_format( (float)$order['amount'], 2 ) . '</strong></td></tr>
          <tr><th>Payment Method</th><td>' . esc_html( strtoupper( $order['payment_method'] ) ) . '</td></tr>
          <tr><th>Transaction ID</th><td style="font-size:12px;">' . esc_html( $order['payment_id'] ) . '</td></tr>
          <tr><th>Attendee</th><td>' . esc_html( $order['attendee_name'] ) . '</td></tr>
          <tr><th>Email</th><td>' . esc_html( $order['attendee_email'] ) . '</td></tr>
          ' . ( $org_ein ? '<tr><th>EIN</th><td>' . esc_html( $org_ein ) . '</td></tr>' : '' ) . '
        </table>
        ' . ( $qr_img ? '<div class="qr">' . $qr_img . '<p style="margin:8px 0 0;font-size:12px;color:#999;">Scan at the door</p></div>' : '' ) . '
        <div class="footer">' . esc_html( $org_name ) . ' &bull; ' . esc_html( get_option( 'pbs_email_from', '' ) ) . ( $org_ein ? ' &bull; EIN: ' . esc_html( $org_ein ) : '' ) . '</div>
        </body></html>';
        exit;
    }

    public static function ticket_types_page() {
        // Handle POST actions (add / edit / delete / toggle)
        if ( isset( $_POST['pbs_tt_action'] ) && check_admin_referer( 'pbs_ticket_types' ) ) {
            $action = sanitize_key( $_POST['pbs_tt_action'] );
            $id     = (int) ( $_POST['tt_id'] ?? 0 );

            if ( $action === 'delete' && $id ) {
                PBS_DB::delete_ticket_type( $id );
                wp_safe_redirect( add_query_arg( [ 'page' => 'pbs-ticket-types', 'msg' => 'deleted' ], admin_url( 'admin.php' ) ) );
                exit;
            }
            if ( $action === 'toggle' && $id ) {
                $tt = PBS_DB::get_ticket_type( $id );
                if ( $tt ) PBS_DB::update_ticket_type( $id, array_merge( $tt, [ 'active' => $tt['active'] ? 0 : 1 ] ) );
                wp_safe_redirect( add_query_arg( [ 'page' => 'pbs-ticket-types', 'event_id' => (int)($tt['event_id']??0) ], admin_url( 'admin.php' ) ) );
                exit;
            }
            if ( in_array( $action, [ 'add', 'save' ], true ) ) {
                $fields = [
                    'event_id'    => $_POST['tt_event_id'] ?? 0,
                    'name'        => $_POST['tt_name'] ?? '',
                    'description' => $_POST['tt_description'] ?? '',
                    'price'       => $_POST['tt_price'] ?? 0,
                    'capacity'    => $_POST['tt_capacity'] ?? 0,
                    'ticket_start'=> $_POST['tt_start'] ?? '',
                    'ticket_end'  => $_POST['tt_end'] ?? '',
                    'is_donation' => $_POST['tt_is_donation'] ?? 0,
                    'sort_order'  => $_POST['tt_sort_order'] ?? 0,
                    'active'      => isset( $_POST['tt_active'] ) ? 1 : 0,
                ];
                if ( $action === 'add' ) {
                    PBS_DB::insert_ticket_type( $fields );
                } else {
                    PBS_DB::update_ticket_type( $id, $fields );
                }
                wp_safe_redirect( add_query_arg( [ 'page' => 'pbs-ticket-types', 'event_id' => (int)$fields['event_id'], 'msg' => $action === 'add' ? 'added' : 'saved' ], admin_url( 'admin.php' ) ) );
                exit;
            }
        }

        $edit_id   = isset( $_GET['edit'] ) ? (int) $_GET['edit'] : 0;
        $edit_tt   = $edit_id ? PBS_DB::get_ticket_type( $edit_id ) : null;
        $event_id  = $edit_tt ? (int) $edit_tt['event_id'] : ( isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0 );
        $msg       = isset( $_GET['msg'] ) ? sanitize_key( $_GET['msg'] ) : '';
        $ticket_types = PBS_DB::get_all_ticket_types( $event_id );

        // Get distinct event IDs that have ticket types + published pages/posts for dropdown
        global $wpdb;
        $tt_event_ids = $wpdb->get_col( "SELECT DISTINCT event_id FROM {$wpdb->prefix}pbs_ticket_types ORDER BY event_id DESC" );

        include PBS_EC_PATH . 'admin/views/ticket-types.php';
    }

    public static function attendees_page() {
        $event_id = isset( $_GET['event_id'] ) ? (int) $_GET['event_id'] : 0;
        $status   = isset( $_GET['status'] ) ? sanitize_text_field( $_GET['status'] ) : 'complete';
        $search   = isset( $_GET['s'] ) ? sanitize_text_field( $_GET['s'] ) : '';

        $args = [ 'status' => $status, 'limit' => 500 ];
        if ( $event_id ) $args['event_id'] = $event_id;

        $orders = PBS_DB::get_orders( $args );

        // Filter by search term (name or email)
        if ( $search && is_array( $orders ) ) {
            $orders = array_filter( $orders, function( $o ) use ( $search ) {
                return stripos( $o['attendee_name'], $search ) !== false
                    || stripos( $o['attendee_email'], $search ) !== false
                    || stripos( $o['order_number'], $search ) !== false;
            } );
        }

        // Get all events that have orders for the filter dropdown
        global $wpdb;
        $event_ids = $wpdb->get_col( "SELECT DISTINCT event_id FROM {$wpdb->prefix}pbs_orders ORDER BY event_id DESC" );

        include PBS_EC_PATH . 'admin/views/attendees.php';
    }

    public static function settings_page() {
        include PBS_EC_PATH . 'admin/views/settings.php';
    }

    /** REST: get orders */
    public static function get_orders( WP_REST_Request $request ) {
        $args = [
            'event_id' => (int) $request->get_param('event_id'),
            'status'   => sanitize_text_field( $request->get_param('status') ),
            'limit'    => (int) $request->get_param('limit') ?: 200,
        ];
        return rest_ensure_response( PBS_DB::get_orders( array_filter( $args ) ) );
    }
}
