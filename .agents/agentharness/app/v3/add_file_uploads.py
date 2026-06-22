#!/usr/bin/env python3
"""
Database migration for file uploads feature.

Creates tables for:
- uploaded_files: File metadata and storage paths
- file_chunks: Document embeddings for RAG retrieval
"""

import sqlite3
from pathlib import Path

# Resolve database path
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"


def create_file_tables(conn: sqlite3.Connection) -> None:
    """Create tables for file upload and document RAG."""
    
    cursor = conn.cursor()
    
    # Table: uploaded_files
    # Stores metadata for all uploaded files
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            file_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,  -- 'pdf', 'image', 'spreadsheet', 'document'
            mime_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            storage_path TEXT NOT NULL,
            parsed_content TEXT,  -- Extracted text/analysis
            parsing_status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'complete', 'failed'
            parsing_error TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_via TEXT DEFAULT 'ios',  -- 'ios', 'desktop', 'api'
            conversation_id TEXT,  -- Optional: link to conversation
            message_id TEXT,  -- Optional: link to specific message
            metadata_json TEXT,  -- JSON: page_count, dimensions, columns, etc.
            
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Table: file_chunks
    # Stores document chunks with embeddings for RAG retrieval
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_chunks (
            chunk_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            chunk_tokens INTEGER DEFAULT 0,
            page_number INTEGER,  -- For PDFs
            embedding_vector TEXT,  -- JSON array of floats
            embedding_model TEXT DEFAULT 'text-embedding-3-small',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (file_id) REFERENCES uploaded_files (file_id) ON DELETE CASCADE,
            UNIQUE (file_id, chunk_index)
        )
    """)
    
    # Indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_user_uploaded 
        ON uploaded_files (user_id, uploaded_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_conversation 
        ON uploaded_files (conversation_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_parsing_status 
        ON uploaded_files (parsing_status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chunks_file 
        ON file_chunks (file_id, chunk_index)
    """)
    
    conn.commit()
    print("✅ Created uploaded_files and file_chunks tables")


def main():
    """Run the migration."""
    print(f"📂 Database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        create_file_tables(conn)
        print("\n✅ File upload migration complete!")
        
        # Show table info
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%file%'")
        tables = cursor.fetchall()
        print("\n📊 File-related tables:")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
