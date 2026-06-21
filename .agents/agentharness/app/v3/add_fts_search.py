#!/usr/bin/env python3
"""
Add FTS5 full-text search index to messages table.

This enables fast keyword search across all historical conversations.
Run this once to create the index.
"""

import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


def add_fts_index():
    """Create FTS5 virtual table for message search."""
    print(f"📊 Connecting to database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("❌ Messages table not found")
            return
        
        # Check if FTS5 index already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'")
        if cursor.fetchone():
            print("✅ FTS5 index already exists (messages_fts)")
            return
        
        print("🔨 Creating FTS5 full-text search index...")
        
        # Create FTS5 virtual table
        # content=messages links it to the messages table
        # content_rowid=rowid syncs with the main table's rowid
        cursor.execute("""
            CREATE VIRTUAL TABLE messages_fts USING fts5(
                content,
                content=messages,
                content_rowid=rowid
            )
        """)
        
        print("📝 Populating FTS5 index with existing messages...")
        
        # Populate the FTS5 table with existing message content
        cursor.execute("""
            INSERT INTO messages_fts(rowid, content)
            SELECT rowid, content FROM messages
        """)
        
        # Create triggers to keep FTS5 in sync with messages table
        print("🔗 Creating triggers to keep FTS5 index synchronized...")
        
        # Trigger for new inserts
        cursor.execute("""
            CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
            END
        """)
        
        # Trigger for updates
        cursor.execute("""
            CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
                UPDATE messages_fts SET content = new.content WHERE rowid = old.rowid;
            END
        """)
        
        # Trigger for deletes
        cursor.execute("""
            CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
                DELETE FROM messages_fts WHERE rowid = old.rowid;
            END
        """)
        
        conn.commit()
        
        # Get row counts
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        message_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM messages_fts")
        fts_count = cursor.fetchone()['count']
        
        print(f"✅ FTS5 index created successfully!")
        print(f"📊 Indexed {fts_count} messages (total: {message_count})")
        print(f"🔍 Search enabled for conversations")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()


def test_search():
    """Test the FTS5 search functionality."""
    print("\n🧪 Testing search functionality...")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Test search
        test_query = "what"
        print(f"🔍 Searching for: '{test_query}'")
        
        cursor.execute("""
            SELECT 
                m.id,
                m.conversation_id,
                m.role,
                substr(m.content, 1, 100) as excerpt,
                m.created_at
            FROM messages m
            WHERE m.rowid IN (
                SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
            )
            ORDER BY m.created_at DESC
            LIMIT 5
        """, (test_query,))
        
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for row in results:
                excerpt = row['excerpt'].replace('\n', ' ')
                print(f"  - [{row['role']}] {excerpt}...")
        else:
            print(f"ℹ️  No results found for '{test_query}'")
        
    except sqlite3.Error as e:
        print(f"❌ Search test failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_fts_index()
    test_search()
