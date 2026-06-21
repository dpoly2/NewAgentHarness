#!/usr/bin/env python3
"""
Email Cleanup Executor - Safely executes approved email cleanup actions.

Integrates with existing email_connectors OAuth system.
"""

import imaplib
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


class EmailCleanupExecutor:
    """Executes approved email cleanup actions."""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    def execute_cleanup(self, plan_id: str) -> Dict:
        """
        Execute all approved items in a cleanup plan.
        
        Returns statistics about the cleanup.
        """
        print(f"\n🧹 Executing cleanup plan: {plan_id}")
        
        # Get plan and approved items
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get plan
            cursor.execute("SELECT * FROM email_cleanup_plans WHERE id = ?", (plan_id,))
            plan_row = cursor.fetchone()
            
            if not plan_row:
                raise ValueError(f"Plan {plan_id} not found")
            
            plan = dict(plan_row)
            connector_id = plan['account_id']
            
            # Get approved items
            cursor.execute("""
                SELECT * FROM email_cleanup_items
                WHERE plan_id = ? AND approved = 1 AND executed = 0
                ORDER BY category
            """, (plan_id,))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            if not items:
                print("No approved items to execute")
                return {
                    'total': 0,
                    'archived': 0,
                    'deleted': 0,
                    'errors': 0,
                    'space_recovered_mb': 0
                }
            
            print(f"Found {len(items)} approved items to cleanup")
            
            # Connect to email via IMAP
            import hub_db
            import oauth_connector
            
            connector = hub_db.get_connector(connector_id)
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            provider = connector.get('provider', 'imap')
            auth_type = connector.get('auth_type', 'password')
            email_address = connector.get('email_address', '')
            imap_host = connector.get('imap_host', '')
            imap_port = int(connector.get('imap_port', 993))
            
            # Authenticate
            if auth_type == 'oauth2':
                access_token = oauth_connector.get_valid_access_token(connector_id)
                auth_string = oauth_connector._xoauth2_string(email_address, access_token)
            else:
                creds = connector.get('credentials', {})
                if isinstance(creds, str):
                    creds = json.loads(creds)
                password = creds.get('password', '')
                auth_string = None
            
            # Connect
            print(f"📧 Connecting to {imap_host}:{imap_port}...")
            
            if imap_port == 993:
                imap = imaplib.IMAP4_SSL(imap_host, imap_port)
            else:
                imap = imaplib.IMAP4(imap_host, imap_port)
            
            if auth_string:
                imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
            else:
                username = connector.get('username', email_address)
                imap.login(username, password)
            
            imap.select('INBOX')
            
            # Execute cleanup
            results = {
                'total': 0,
                'archived': 0,
                'deleted': 0,
                'errors': 0,
                'space_recovered_mb': 0,
                'failed_ids': []
            }
            
            now = datetime.utcnow().isoformat()
            
            for item in items:
                email_id = item['email_id']
                action = item['action']
                
                try:
                    if action == 'archive':
                        # Move to [Gmail]/All Mail or archive folder
                        # For Gmail: remove INBOX label
                        if provider == 'gmail':
                            imap.store(email_id, '+X-GM-LABELS', '\\Archive')
                            imap.store(email_id, '-X-GM-LABELS', '\\Inbox')
                        else:
                            # For others: move to Archive folder
                            try:
                                imap.copy(email_id, 'Archive')
                                imap.store(email_id, '+FLAGS', '\\Deleted')
                                imap.expunge()
                            except:
                                # If Archive doesn't exist, just delete from INBOX
                                imap.store(email_id, '+FLAGS', '\\Deleted')
                        
                        results['archived'] += 1
                    
                    elif action == 'delete':
                        # Soft delete - move to trash
                        if provider == 'gmail':
                            imap.store(email_id, '+X-GM-LABELS', '\\Trash')
                        else:
                            imap.store(email_id, '+FLAGS', '\\Deleted')
                        
                        results['deleted'] += 1
                    
                    results['total'] += 1
                    results['space_recovered_mb'] += item['size_bytes'] / (1024 * 1024)
                    
                    # Mark as executed in database
                    cursor.execute("""
                        UPDATE email_cleanup_items
                        SET executed = 1, executed_at = ?
                        WHERE id = ?
                    """, (now, item['id']))
                    
                    if results['total'] % 10 == 0:
                        print(f"Processed {results['total']}/{len(items)}...")
                    
                except Exception as e:
                    print(f"❌ Failed to cleanup email {email_id}: {e}")
                    results['errors'] += 1
                    results['failed_ids'].append(email_id)
            
            # Expunge deleted messages (commit changes)
            try:
                imap.expunge()
            except:
                pass
            
            imap.logout()
            
            # Round space recovered
            results['space_recovered_mb'] = round(results['space_recovered_mb'], 2)
            
            # Update plan status
            cursor.execute("""
                UPDATE email_cleanup_plans
                SET status = ?, executed_at = ?
                WHERE id = ?
            """, ('executed', now, plan_id))
            
            conn.commit()
            
            print(f"\n✅ Cleanup complete!")
            print(f"   Total: {results['total']}")
            print(f"   Archived: {results['archived']}")
            print(f"   Deleted: {results['deleted']}")
            print(f"   Errors: {results['errors']}")
            print(f"   Space recovered: {results['space_recovered_mb']} MB")
            
            return results
            
        finally:
            conn.close()
    
    def rollback_cleanup(self, plan_id: str) -> Dict:
        """
        Rollback a cleanup plan (within 30 days).
        
        Restores emails from trash/archive back to INBOX.
        """
        print(f"\n↩️  Rolling back cleanup plan: {plan_id}")
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get plan
            cursor.execute("SELECT * FROM email_cleanup_plans WHERE id = ?", (plan_id,))
            plan_row = cursor.fetchone()
            
            if not plan_row:
                raise ValueError(f"Plan {plan_id} not found")
            
            plan = dict(plan_row)
            
            # Check if within rollback window (30 days)
            if plan['executed_at']:
                executed_date = datetime.fromisoformat(plan['executed_at'])
                days_ago = (datetime.utcnow() - executed_date).days
                
                if days_ago > 30:
                    raise ValueError(f"Rollback window expired ({days_ago} days > 30 days)")
            
            # Get executed items
            cursor.execute("""
                SELECT * FROM email_cleanup_items
                WHERE plan_id = ? AND executed = 1
            """, (plan_id,))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            if not items:
                print("No executed items to rollback")
                return {'total': 0, 'restored': 0, 'errors': 0}
            
            print(f"Rolling back {len(items)} items...")
            
            # Connect to email
            import hub_db
            import oauth_connector
            
            connector_id = plan['account_id']
            connector = hub_db.get_connector(connector_id)
            
            if not connector:
                raise ValueError(f"Connector {connector_id} not found")
            
            provider = connector.get('provider', 'imap')
            auth_type = connector.get('auth_type', 'password')
            email_address = connector.get('email_address', '')
            imap_host = connector.get('imap_host', '')
            imap_port = int(connector.get('imap_port', 993))
            
            # Authenticate
            if auth_type == 'oauth2':
                access_token = oauth_connector.get_valid_access_token(connector_id)
                auth_string = oauth_connector._xoauth2_string(email_address, access_token)
            else:
                creds = connector.get('credentials', {})
                if isinstance(creds, str):
                    creds = json.loads(creds)
                password = creds.get('password', '')
                auth_string = None
            
            # Connect
            if imap_port == 993:
                imap = imaplib.IMAP4_SSL(imap_host, imap_port)
            else:
                imap = imaplib.IMAP4(imap_host, imap_port)
            
            if auth_string:
                imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
            else:
                username = connector.get('username', email_address)
                imap.login(username, password)
            
            # Rollback each item
            results = {
                'total': 0,
                'restored': 0,
                'errors': 0
            }
            
            for item in items:
                email_id = item['email_id']
                
                try:
                    if provider == 'gmail':
                        # Restore from trash/archive to INBOX
                        imap.select('[Gmail]/All Mail')
                        imap.store(email_id, '+X-GM-LABELS', '\\Inbox')
                        imap.store(email_id, '-X-GM-LABELS', '\\Trash')
                        imap.store(email_id, '-X-GM-LABELS', '\\Archive')
                    else:
                        # Move from Trash back to INBOX
                        imap.select('Trash')
                        imap.copy(email_id, 'INBOX')
                        imap.store(email_id, '-FLAGS', '\\Deleted')
                    
                    results['restored'] += 1
                    results['total'] += 1
                    
                except Exception as e:
                    print(f"❌ Failed to restore email {email_id}: {e}")
                    results['errors'] += 1
            
            imap.logout()
            
            # Update plan status
            cursor.execute("""
                UPDATE email_cleanup_plans
                SET status = 'rolled_back'
                WHERE id = ?
            """, (plan_id,))
            
            # Mark items as not executed
            cursor.execute("""
                UPDATE email_cleanup_items
                SET executed = 0, executed_at = NULL
                WHERE plan_id = ?
            """, (plan_id,))
            
            conn.commit()
            
            print(f"✅ Rollback complete: {results['restored']} emails restored")
            
            return results
            
        finally:
            conn.close()


if __name__ == "__main__":
    # Test executor
    executor = EmailCleanupExecutor()
    
    # List plans
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, status, suggested_cleanup_count, created_at
        FROM email_cleanup_plans
        WHERE status = 'pending'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    plan = cursor.fetchone()
    conn.close()
    
    if plan:
        plan_id = plan['id']
        print(f"Found pending plan: {plan_id}")
        print(f"Suggested cleanup: {plan['suggested_cleanup_count']} emails")
        print(f"\nTo execute, approve items first:")
        print(f"  UPDATE email_cleanup_items SET approved = 1 WHERE plan_id = '{plan_id}' AND category IN ('newsletter', 'promotion');")
        print(f"\nThen run:")
        print(f"  python3 email_executor.py {plan_id}")
    else:
        print("No pending cleanup plans found")
