"""
add_citations_schema.py — Database Migration for Web Search Citations
========================================================================
Adds citation support to the messages table for storing web search sources.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "memory" / "runs_v3.db"

def migrate():
    """Add citations columns to messages table."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("🔄 Checking messages table schema...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cursor.fetchall()]
    
    migrations_needed = []
    
    if "has_citations" not in columns:
        migrations_needed.append("has_citations BOOLEAN DEFAULT FALSE")
    
    if "citations" not in columns:
        migrations_needed.append("citations TEXT")  # JSON
    
    if "search_query" not in columns:
        migrations_needed.append("search_query TEXT")  # Original search query if web search was used
    
    if migrations_needed:
        print(f"📝 Adding {len(migrations_needed)} new columns...")
        for col in migrations_needed:
            try:
                cursor.execute(f"ALTER TABLE messages ADD COLUMN {col}")
                print(f"  ✅ Added column: {col.split()[0]}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"  ⏭️  Column already exists: {col.split()[0]}")
                else:
                    raise
        
        conn.commit()
        print("✅ Migration completed successfully!")
    else:
        print("✅ Schema already up to date, no migration needed")
    
    conn.close()

if __name__ == "__main__":
    migrate()
