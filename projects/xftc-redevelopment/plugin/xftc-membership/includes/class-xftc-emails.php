<?php
/**
 * Transactional email system for XFTC Membership.
 *
 * @package XFTC_Membership
 */

defined( 'ABSPATH' ) || exit;

class XFTC_Emails {

    /** @var string Club name from options. */
    private $club_name;

    /** @var string Admin email from options. */
    private $admin_email;

    public function __construct() {
        $this->club_name   = get_option( 'xftc_club_name', 'Xtreme Force Track Club' );
        $this->admin_email = get_option( 'xftc_admin_email', get_option( 'admin_email' ) );
    }

    /**
     * Send welcome email to a newly registered parent.
     *
     * @param int $user_id WP user ID.
     */
    public function send_parent_welcome( int $user_id ) {
        $user       = get_userdata( $user_id );
        $first_name = get_user_meta( $user_id, 'first_name', true );
        $login_url  = wp_login_url( home_url( '/member-portal/' ) );

        $subject = sprintf( __( 'Welcome to %s!', 'xftc-membership' ), $this->club_name );

        $message = $this->get_header( $subject );
        $message .= '<p>Hi ' . esc_html( $first_name ) . ',</p>';
        $message .= '<p>Welcome to <strong>' . esc_html( $this->club_name ) . '</strong>! Your account has been created.</p>';
        $message .= '<p>You can now log in to your parent portal to register your athletes and manage your account:</p>';
        $message .= '<p><a href="' . esc_url( $login_url ) . '" style="background:#c8102e;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Log In to Your Portal</a></p>';
        $message .= '<p>Your username: <strong>' . esc_html( $user->user_login ) . '</strong></p>';
        $message .= '<p>If you have any questions, reply to this email or contact us at ' . esc_html( $this->admin_email ) . '</p>';
        $message .= $this->get_footer();

        $this->send( $user->user_email, $subject, $message );

        // Notify admin
        $admin_subject = sprintf( __( 'New Parent Registration — %s', 'xftc-membership' ), $first_name . ' ' . get_user_meta( $user_id, 'last_name', true ) );
        $admin_message = $this->get_header( $admin_subject );
        $admin_message .= '<p>A new parent account was just registered:</p>';
        $admin_message .= '<ul>';
        $admin_message .= '<li><strong>Name:</strong> ' . esc_html( $first_name . ' ' . get_user_meta( $user_id, 'last_name', true ) ) . '</li>';
        $admin_message .= '<li><strong>Email:</strong> ' . esc_html( $user->user_email ) . '</li>';
        $admin_message .= '<li><strong>Phone:</strong> ' . esc_html( get_user_meta( $user_id, 'xftc_phone', true ) ) . '</li>';
        $admin_message .= '</ul>';
        $admin_message .= $this->get_footer();

        $this->send( $this->admin_email, $admin_subject, $admin_message );
    }

    /**
     * Send payment receipt email.
     *
     * @param int   $user_id    WP user ID (parent).
     * @param float $amount     Amount paid.
     * @param array $details    Additional details (season, athlete, etc.)
     */
    public function send_payment_receipt( int $user_id, float $amount, array $details = [] ) {
        $user       = get_userdata( $user_id );
        $first_name = get_user_meta( $user_id, 'first_name', true );

        $subject = sprintf( __( 'Payment Receipt — %s', 'xftc-membership' ), $this->club_name );
        $message = $this->get_header( $subject );
        $message .= '<p>Hi ' . esc_html( $first_name ) . ',</p>';
        $message .= '<p>We received your payment of <strong>$' . number_format( $amount, 2 ) . '</strong>. Thank you!</p>';

        if ( ! empty( $details ) ) {
            $message .= '<table style="width:100%;border-collapse:collapse;">';
            foreach ( $details as $label => $value ) {
                $message .= '<tr><td style="padding:6px;border-bottom:1px solid #eee;"><strong>' . esc_html( $label ) . '</strong></td><td style="padding:6px;border-bottom:1px solid #eee;">' . esc_html( $value ) . '</td></tr>';
            }
            $message .= '</table>';
        }

        $message .= '<p>If you have questions, contact us at ' . esc_html( $this->admin_email ) . '</p>';
        $message .= $this->get_footer();

        $this->send( $user->user_email, $subject, $message );
    }

    /**
     * Send renewal reminder email.
     *
     * @param int    $user_id
     * @param string $season_name
     */
    public function send_renewal_reminder( int $user_id, string $season_name ) {
        $user       = get_userdata( $user_id );
        $first_name = get_user_meta( $user_id, 'first_name', true );
        $portal_url = home_url( '/member-portal/' );

        $subject = sprintf( __( '%s Season Registration is Now Open!', 'xftc-membership' ), esc_html( $season_name ) );
        $message = $this->get_header( $subject );
        $message .= '<p>Hi ' . esc_html( $first_name ) . ',</p>';
        $message .= '<p>Registration for the <strong>' . esc_html( $season_name ) . '</strong> season is now open!</p>';
        $message .= '<p>Log in to your parent portal to register your athlete(s):</p>';
        $message .= '<p><a href="' . esc_url( $portal_url ) . '" style="background:#c8102e;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block;">Register Now</a></p>';
        $message .= $this->get_footer();

        $this->send( $user->user_email, $subject, $message );
    }

    // ── Private Helpers ───────────────────────────────────────────────────────

    /**
     * Send an HTML email via wp_mail.
     *
     * @param string $to
     * @param string $subject
     * @param string $body
     */
    private function send( string $to, string $subject, string $body ) {
        $headers = [
            'Content-Type: text/html; charset=UTF-8',
            'From: ' . esc_html( $this->club_name ) . ' <' . $this->admin_email . '>',
        ];
        wp_mail( $to, $subject, $body, $headers );
    }

    /** @return string HTML email header */
    private function get_header( string $title ): string {
        return '<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:0;">
        <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="background:#c8102e;padding:24px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:22px;">' . esc_html( $this->club_name ) . '</h1>
        </div>
        <div style="padding:32px;">';
    }

    /** @return string HTML email footer */
    private function get_footer(): string {
        return '</div>
        <div style="background:#f4f4f4;padding:16px;text-align:center;font-size:12px;color:#888;">
            &copy; ' . date( 'Y' ) . ' ' . esc_html( $this->club_name ) . ' &bull; <a href="' . esc_url( home_url() ) . '" style="color:#c8102e;">Visit our site</a>
        </div></div></body></html>';
    }
}
