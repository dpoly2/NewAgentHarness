#!/usr/bin/env python3
"""
Database migration for feedback and learning system.

Creates tables for:
- message_feedback: Thumbs up/down ratings on messages
- corrections: User corrections to capture learning
- user_style_preferences: Learned style preferences
"""

import sqlite3
from pathlib import Path

# Resolve database path
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"


def create_feedback_tables(conn: sqlite3.Connection) -> None:
    """Create tables for feedback and learning system."""
    
    cursor = conn.cursor()
    
    # Table: message_feedback
    # Stores user ratings (thumbs up/down) on assistant messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_feedback (
            feedback_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            conversation_id TEXT,
            rating INTEGER NOT NULL,  -- 1 = thumbs up, -1 = thumbs down
            feedback_text TEXT,  -- Optional comment
            category TEXT,  -- 'helpful', 'accurate', 'tone', 'length', 'other'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE,
            UNIQUE (message_id, user_id)
        )
    """)
    
    # Table: corrections
    # Captures user corrections to learn from mistakes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            correction_id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            conversation_id TEXT,
            original_intent TEXT,  -- What user originally asked
            corrected_intent TEXT NOT NULL,  -- What user actually meant
            correction_text TEXT NOT NULL,  -- Full correction message
            correction_type TEXT DEFAULT 'clarification',  -- 'clarification', 'error', 'misunderstanding'
            applied BOOLEAN DEFAULT 0,  -- Whether correction has been incorporated into learning
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
        )
    """)
    
    # Table: user_style_preferences
    # Learned preferences from feedback patterns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_style_preferences (
            user_id TEXT PRIMARY KEY,
            preferred_length TEXT DEFAULT 'medium',  -- 'concise', 'medium', 'detailed'
            preferred_formality TEXT DEFAULT 'professional',  -- 'casual', 'professional', 'formal'
            use_emojis BOOLEAN DEFAULT 1,
            citation_density TEXT DEFAULT 'medium',  -- 'none', 'low', 'medium', 'high'
            code_style TEXT DEFAULT 'explained',  -- 'minimal', 'explained', 'verbose'
            avg_positive_response_tokens INTEGER DEFAULT 0,
            avg_negative_response_tokens INTEGER DEFAULT 0,
            total_positive_feedback INTEGER DEFAULT 0,
            total_negative_feedback INTEGER DEFAULT 0,
            total_corrections INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            preferences_json TEXT  -- JSON: additional learned preferences
        )
    """)
    
    # Indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_message 
        ON message_feedback (message_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_user_created 
        ON message_feedback (user_id, created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_rating 
        ON message_feedback (rating, created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_corrections_user 
        ON corrections (user_id, created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_corrections_applied 
        ON corrections (applied, created_at DESC)
    """)
    
    conn.commit()
    print("✅ Created message_feedback, corrections, and user_style_preferences tables")


def main():
    """Run the migration."""
    print(f"📂 Database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        create_feedback_tables(conn)
        print("\n✅ Feedback system migration complete!")
        
        # Show table info
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%feedback%' OR name LIKE '%correction%' OR name LIKE '%preference%')")
        tables = cursor.fetchall()
        print("\n📊 Feedback-related tables:")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
