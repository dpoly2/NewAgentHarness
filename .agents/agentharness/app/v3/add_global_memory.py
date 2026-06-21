#!/usr/bin/env python3
"""
Add global_memory table for persistent cross-conversation memory.

This enables facts, preferences, and context to persist across all conversations
and be available to all agents (Inez, Ministry AI, etc.).
"""

import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


def add_global_memory_table():
    """Create global_memory table."""
    print(f"📊 Connecting to database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='global_memory'")
        if cursor.fetchone():
            print("✅ global_memory table already exists")
            return
        
        print("🔨 Creating global_memory table...")
        
        # Create table
        cursor.execute("""
            CREATE TABLE global_memory (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT DEFAULT 'user',
                confidence REAL DEFAULT 1.0,
                importance INTEGER DEFAULT 5,
                last_verified TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(category, key)
            )
        """)
        
        # Create index for fast category queries
        cursor.execute("""
            CREATE INDEX idx_global_memory_category ON global_memory(category)
        """)
        
        # Create index for importance ranking
        cursor.execute("""
            CREATE INDEX idx_global_memory_importance ON global_memory(importance DESC, usage_count DESC)
        """)
        
        conn.commit()
        
        print("✅ Table created successfully!")
        print("📊 Schema:")
        print("  - id: unique identifier")
        print("  - category: preferences, projects, people, deadlines, ministry, technical")
        print("  - key: fact label (e.g., 'communication_style', 'primary_project')")
        print("  - value: fact content")
        print("  - source: chatgpt_import, user, agent_learned, manual")
        print("  - confidence: 0.0-1.0 (how sure we are)")
        print("  - importance: 1-10 (priority for injection)")
        print("  - usage_count: how often this fact is used")
        
        # Seed example facts
        print("\n🌱 Seeding example facts...")
        seed_examples(conn)
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()


def seed_examples(conn):
    """Seed example facts."""
    from datetime import datetime
    import uuid
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    examples = [
        {
            'id': str(uuid.uuid4()),
            'category': 'preferences',
            'key': 'communication_style',
            'value': 'Prefers concise, direct responses without excessive pleasantries',
            'source': 'manual',
            'confidence': 1.0,
            'importance': 9,
            'last_verified': now,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'category': 'projects',
            'key': 'primary_focus',
            'value': 'XFTC WordPress plugin development, PBS Event Commerce',
            'source': 'manual',
            'confidence': 1.0,
            'importance': 10,
            'last_verified': now,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'category': 'projects',
            'key': 'secondary_focus',
            'value': 'HP Engineering portfolio management (TSLA, NVDA, META)',
            'source': 'manual',
            'confidence': 1.0,
            'importance': 8,
            'last_verified': now,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'category': 'people',
            'key': 'role',
            'value': 'Technical leader across multiple divisions: HP Engineering (CTO), XFTC (Lead Dev), S2T Designs (Tech Director), PBS Foundation (Tech Advisor), Markets (Portfolio Manager)',
            'source': 'manual',
            'confidence': 1.0,
            'importance': 10,
            'last_verified': now,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
    ]
    
    cursor = conn.cursor()
    for fact in examples:
        cursor.execute("""
            INSERT INTO global_memory 
            (id, category, key, value, source, confidence, importance, last_verified, usage_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fact['id'],
            fact['category'],
            fact['key'],
            fact['value'],
            fact['source'],
            fact['confidence'],
            fact['importance'],
            fact['last_verified'],
            fact['usage_count'],
            fact['created_at'],
            fact['updated_at']
        ))
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) as count FROM global_memory")
    count = cursor.fetchone()['count']
    print(f"✅ Seeded {count} example facts")


if __name__ == "__main__":
    add_global_memory_table()
