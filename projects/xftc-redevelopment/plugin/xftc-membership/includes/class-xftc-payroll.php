<?php
/**
 * Class XFTC_Payroll
 *
 * Manages staff records, payroll period entry,
 * gross/net pay calculation, and CSV export.
 *
 * @package XFTC_Membership
 * @since   0.2.0
 */

if ( ! defined( 'ABSPATH' ) ) exit;

class XFTC_Payroll {

    private string $staff_table;
    private string $payroll_table;

    public function __construct() {
        global $wpdb;
        $this->staff_table   = $wpdb->prefix . 'xftc_staff';
        $this->payroll_table = $wpdb->prefix . 'xftc_payroll';
    }

    /** ─── STAFF CRUD ────────────────────────────────────────── */

    public function add_staff( array $data ): int|false {
        global $wpdb;
        $inserted = $wpdb->insert( $this->staff_table, [
            'user_id'     => (int) $data['user_id'],
            'role'        => sanitize_text_field( $data['role'] ?? '' ),
            'hourly_wage' => (float) $data['hourly_wage'],
            'hire_date'   => sanitize_text_field( $data['hire_date'] ?? current_time( 'Y-m-d' ) ),
            'status'      => 'active',
            'created_at'  => current_time( 'mysql' ),
        ] );
        return $inserted ? $wpdb->insert_id : false;
    }

    public function get_staff( int $id ): ?array {
        global $wpdb;
        $row = $wpdb->get_row( $wpdb->prepare(
            "SELECT s.*, u.display_name, u.user_email
             FROM {$this->staff_table} s
             JOIN {$wpdb->users} u ON s.user_id = u.ID
             WHERE s.id = %d", $id
        ), ARRAY_A );
        return $row ?: null;
    }

    public function get_all_staff( string $status = 'active' ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT s.*, u.display_name, u.user_email
             FROM {$this->staff_table} s
             JOIN {$wpdb->users} u ON s.user_id = u.ID
             WHERE s.status = %s
             ORDER BY u.display_name",
            $status
        ), ARRAY_A ) ?: [];
    }

    public function update_staff( int $id, array $data ): bool {
        global $wpdb;
        $update = [];
        if ( isset( $data['role'] ) )        $update['role']        = sanitize_text_field( $data['role'] );
        if ( isset( $data['hourly_wage'] ) )  $update['hourly_wage'] = (float) $data['hourly_wage'];
        if ( isset( $data['hire_date'] ) )    $update['hire_date']   = sanitize_text_field( $data['hire_date'] );
        if ( isset( $data['status'] ) )       $update['status']      = sanitize_text_field( $data['status'] );
        return (bool) $wpdb->update( $this->staff_table, $update, [ 'id' => $id ] );
    }

    public function deactivate_staff( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->staff_table, [ 'status' => 'inactive' ], [ 'id' => $id ] );
    }

    public function get_staff_by_user( int $user_id ): ?array {
        global $wpdb;
        return $wpdb->get_row( $wpdb->prepare(
            "SELECT * FROM {$this->staff_table} WHERE user_id = %d", $user_id
        ), ARRAY_A ) ?: null;
    }

    /** ─── PAYROLL CRUD ──────────────────────────────────────── */

    public function create_payroll_entry( array $data ): int|false {
        global $wpdb;

        $staff = $this->get_staff( (int) $data['staff_id'] );
        if ( ! $staff ) return false;

        $hours      = (float) $data['hours_worked'];
        $wage       = (float) ( $data['hourly_wage'] ?? $staff['hourly_wage'] );
        $gross      = round( $hours * $wage, 2 );
        $deductions = (float) ( $data['deductions'] ?? 0.00 );
        $net        = round( $gross - $deductions, 2 );

        $inserted = $wpdb->insert( $this->payroll_table, [
            'staff_id'     => (int) $data['staff_id'],
            'period_start' => sanitize_text_field( $data['period_start'] ),
            'period_end'   => sanitize_text_field( $data['period_end'] ),
            'hours_worked' => $hours,
            'gross_pay'    => $gross,
            'deductions'   => $deductions,
            'net_pay'      => $net,
            'status'       => 'pending',
            'notes'        => sanitize_textarea_field( $data['notes'] ?? '' ),
            'created_at'   => current_time( 'mysql' ),
        ] );
        return $inserted ? $wpdb->insert_id : false;
    }

    public function get_payroll_entry( int $id ): ?array {
        global $wpdb;
        return $wpdb->get_row( $wpdb->prepare(
            "SELECT p.*, s.role, u.display_name
             FROM {$this->payroll_table} p
             JOIN {$this->staff_table} s ON p.staff_id = s.id
             JOIN {$wpdb->users} u ON s.user_id = u.ID
             WHERE p.id = %d", $id
        ), ARRAY_A ) ?: null;
    }

    public function get_staff_payroll( int $staff_id ): array {
        global $wpdb;
        return $wpdb->get_results( $wpdb->prepare(
            "SELECT * FROM {$this->payroll_table}
             WHERE staff_id = %d ORDER BY period_start DESC",
            $staff_id
        ), ARRAY_A ) ?: [];
    }

    public function get_all_payroll( string $status = '' ): array {
        global $wpdb;
        $sql = "SELECT p.*, s.role, u.display_name
                FROM {$this->payroll_table} p
                JOIN {$this->staff_table} s ON p.staff_id = s.id
                JOIN {$wpdb->users} u ON s.user_id = u.ID";
        if ( $status ) {
            $sql .= $wpdb->prepare( " WHERE p.status = %s", $status );
        }
        $sql .= " ORDER BY p.period_end DESC";
        return $wpdb->get_results( $sql, ARRAY_A ) ?: [];
    }

    public function get_pending_payroll(): array {
        return $this->get_all_payroll( 'pending' );
    }

    public function mark_paid( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->payroll_table, [
            'status'  => 'paid',
            'paid_at' => current_time( 'mysql' ),
        ], [ 'id' => $id ] );
    }

    public function void_entry( int $id ): bool {
        global $wpdb;
        return (bool) $wpdb->update( $this->payroll_table, [ 'status' => 'voided' ], [ 'id' => $id ] );
    }

    public function update_payroll_entry( int $id, array $data ): bool {
        global $wpdb;
        $update = [];
        if ( isset( $data['hours_worked'] ) ) {
            $entry  = $this->get_payroll_entry( $id );
            $staff  = $this->get_staff( $entry['staff_id'] );
            $hours  = (float) $data['hours_worked'];
            $gross  = round( $hours * $staff['hourly_wage'], 2 );
            $ded    = (float) ( $data['deductions'] ?? $entry['deductions'] );
            $update['hours_worked'] = $hours;
            $update['gross_pay']    = $gross;
            $update['deductions']   = $ded;
            $update['net_pay']      = round( $gross - $ded, 2 );
        }
        if ( isset( $data['notes'] ) ) $update['notes'] = sanitize_textarea_field( $data['notes'] );
        return (bool) $wpdb->update( $this->payroll_table, $update, [ 'id' => $id ] );
    }

    /** ─── TOTALS & SUMMARIES ────────────────────────────────── */

    public function get_period_totals( string $period_start, string $period_end ): array {
        global $wpdb;
        $rows = $wpdb->get_results( $wpdb->prepare(
            "SELECT p.*, u.display_name
             FROM {$this->payroll_table} p
             JOIN {$this->staff_table} s ON p.staff_id = s.id
             JOIN {$wpdb->users} u ON s.user_id = u.ID
             WHERE p.period_start >= %s AND p.period_end <= %s AND p.status != 'voided'",
            $period_start, $period_end
        ), ARRAY_A ) ?: [];

        return [
            'entries'      => $rows,
            'total_gross'  => array_sum( array_column( $rows, 'gross_pay' ) ),
            'total_net'    => array_sum( array_column( $rows, 'net_pay' ) ),
            'total_hours'  => array_sum( array_column( $rows, 'hours_worked' ) ),
            'staff_count'  => count( $rows ),
        ];
    }

    public function get_pending_count(): int {
        global $wpdb;
        return (int) $wpdb->get_var(
            "SELECT COUNT(*) FROM {$this->payroll_table} WHERE status = 'pending'"
        );
    }

    /** ─── CSV EXPORT ────────────────────────────────────────── */

    public function export_payroll_csv( string $period_start = '', string $period_end = '' ): void {
        $data = $period_start && $period_end
            ? $this->get_period_totals( $period_start, $period_end )['entries']
            : $this->get_all_payroll();

        $filename = 'xftc-payroll-' . ( $period_start ?: date( 'Y-m-d' ) ) . '.csv';
        header( 'Content-Type: text/csv' );
        header( "Content-Disposition: attachment; filename=\"{$filename}\"" );

        $out = fopen( 'php://output', 'w' );
        fputcsv( $out, [ 'Staff Name', 'Role', 'Period Start', 'Period End', 'Hours', 'Gross Pay', 'Deductions', 'Net Pay', 'Status', 'Notes' ] );
        foreach ( $data as $row ) {
            fputcsv( $out, [
                $row['display_name'],
                $row['role'],
                $row['period_start'],
                $row['period_end'],
                $row['hours_worked'],
                '$' . number_format( $row['gross_pay'], 2 ),
                '$' . number_format( $row['deductions'], 2 ),
                '$' . number_format( $row['net_pay'], 2 ),
                ucfirst( $row['status'] ),
                $row['notes'],
            ] );
        }
        fclose( $out );
        exit;
    }
}
