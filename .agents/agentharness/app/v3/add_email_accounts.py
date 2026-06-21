#!/usr/bin/env python3
"""
Add email_accounts, email_cleanup_plans, and email_cleanup_items tables.

Phase 1 of Email Inbox Cleanup system:
- Email account OAuth integration (Gmail, Outlook, iCloud)
- Secure token storage with encryption
- Cleanup plan tracking
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import secrets

# Path to the database
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


def add_email_tables():
    """Create email-related tables."""
    print(f"📊 Connecting to database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_accounts'")
        if cursor.fetchone():
            print("✅ Email tables already exist")
            return
        
        print("🔨 Creating email_accounts table...")
        
        # Create email_accounts table
        cursor.execute("""
            CREATE TABLE email_accounts (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL DEFAULT 1,
                provider TEXT NOT NULL,
                email_address TEXT NOT NULL,
                display_name TEXT,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                token_expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                last_sync TEXT,
                total_emails INTEGER DEFAULT 0,
                unread_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, email_address)
            )
        """)
        print("✅ Created email_accounts table")
        
        print("🔨 Creating email_cleanup_plans table...")
        
        # Create email_cleanup_plans table
        cursor.execute("""
            CREATE TABLE email_cleanup_plans (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                total_emails INTEGER DEFAULT 0,
                suggested_cleanup_count INTEGER DEFAULT 0,
                estimated_space_mb INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                executed_at TEXT,
                FOREIGN KEY (account_id) REFERENCES email_accounts(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created email_cleanup_plans table")
        
        print("🔨 Creating email_cleanup_items table...")
        
        # Create email_cleanup_items table
        cursor.execute("""
            CREATE TABLE email_cleanup_items (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                email_id TEXT NOT NULL,
                category TEXT NOT NULL,
                subject TEXT,
                from_address TEXT,
                email_date TEXT,
                size_bytes INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0.0,
                reason TEXT,
                approved INTEGER DEFAULT 0,
                executed INTEGER DEFAULT 0,
                action TEXT DEFAULT 'archive',
                executed_at TEXT,
                FOREIGN KEY (plan_id) REFERENCES email_cleanup_plans(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created email_cleanup_items table")
        
        print("🔨 Creating indexes...")
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_email_accounts_user ON email_accounts(user_id)")
        cursor.execute("CREATE INDEX idx_email_accounts_provider ON email_accounts(provider)")
        cursor.execute("CREATE INDEX idx_cleanup_plans_account ON email_cleanup_plans(account_id)")
        cursor.execute("CREATE INDEX idx_cleanup_plans_status ON email_cleanup_plans(status)")
        cursor.execute("CREATE INDEX idx_cleanup_items_plan ON email_cleanup_items(plan_id)")
        cursor.execute("CREATE INDEX idx_cleanup_items_category ON email_cleanup_items(category)")
        cursor.execute("CREATE INDEX idx_cleanup_items_approved ON email_cleanup_items(approved)")
        
        print("✅ Created indexes")
        
        # Commit changes
        conn.commit()
        print("✅ Migration complete!")
        
        # Show table info
        cursor.execute("SELECT COUNT(*) as count FROM email_accounts")
        count = cursor.fetchone()['count']
        print(f"\n📊 email_accounts: {count} rows")
        
        cursor.execute("SELECT COUNT(*) as count FROM email_cleanup_plans")
        count = cursor.fetchone()['count']
        print(f"📊 email_cleanup_plans: {count} rows")
        
        cursor.execute("SELECT COUNT(*) as count FROM email_cleanup_items")
        count = cursor.fetchone()['count']
        print(f"📊 email_cleanup_items: {count} rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    add_email_tables()
