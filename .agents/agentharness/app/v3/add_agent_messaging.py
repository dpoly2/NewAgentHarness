#!/usr/bin/env python3
"""
Database migration for inter-agent messaging system.

Creates tables for:
- agent_messages: Messages between agents
- agent_conversations: Multi-agent conversation threads
- agent_capabilities: What each agent can do
"""

import sqlite3
from pathlib import Path

# Resolve database path
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"


def create_agent_messaging_tables(conn: sqlite3.Connection) -> None:
    """Create tables for inter-agent messaging."""
    
    cursor = conn.cursor()
    
    # Table: agent_messages
    # Stores messages between agents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            sender_agent TEXT NOT NULL,
            recipient_agent TEXT NOT NULL,
            message_type TEXT NOT NULL,  -- 'request', 'response', 'broadcast', 'error'
            payload_json TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- 'pending', 'delivered', 'processing', 'completed', 'failed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivered_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            timeout_seconds INTEGER DEFAULT 30,
            retry_count INTEGER DEFAULT 0
        )
    """)
    
    # Table: agent_conversations
    # Tracks multi-agent conversation threads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_conversations (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            initiator_agent TEXT NOT NULL,
            participant_agents TEXT NOT NULL,  -- JSON array of agent names
            goal TEXT NOT NULL,
            status TEXT DEFAULT 'active',  -- 'active', 'completed', 'failed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            message_count INTEGER DEFAULT 0,
            result_json TEXT
        )
    """)
    
    # Table: agent_capabilities
    # Defines what each agent can do
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_capabilities (
            agent_name TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            description TEXT,
            capabilities_json TEXT NOT NULL,  -- JSON: ["analyze_market", "fetch_prices", etc]
            dependencies TEXT,  -- JSON: other agents this agent depends on
            response_time_avg_ms INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            total_requests INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation 
        ON agent_messages (conversation_id, created_at)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_recipient_status 
        ON agent_messages (recipient_agent, status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user 
        ON agent_conversations (user_id, created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_status 
        ON agent_conversations (status, created_at DESC)
    """)
    
    conn.commit()
    print("✅ Created agent_messages, agent_conversations, and agent_capabilities tables")


def seed_agent_capabilities(conn: sqlite3.Connection) -> None:
    """Seed initial agent capabilities."""
    
    import json
    from datetime import datetime
    
    cursor = conn.cursor()
    
    # Define standard agents with their capabilities
    agents = [
        {
            "agent_name": "inez",
            "display_name": "Inez - Chief of Staff",
            "description": "Orchestrates all agents and handles general queries",
            "capabilities": ["orchestrate", "general_query", "delegate_tasks", "summarize_results"],
            "dependencies": []
        },
        {
            "agent_name": "markets",
            "display_name": "Markets Agent",
            "description": "Analyzes markets, tracks portfolios, provides investment recommendations",
            "capabilities": ["analyze_market", "track_portfolio", "get_stock_price", "investment_recommendation"],
            "dependencies": []
        },
        {
            "agent_name": "finance",
            "display_name": "Finance CFO",
            "description": "Manages financial data, budgets, and reports",
            "capabilities": ["check_balance", "analyze_spending", "budget_forecast", "financial_report"],
            "dependencies": []
        },
        {
            "agent_name": "legal",
            "display_name": "Legal Counsel",
            "description": "Reviews contracts, provides legal analysis",
            "capabilities": ["review_contract", "legal_analysis", "compliance_check"],
            "dependencies": []
        },
        {
            "agent_name": "research",
            "display_name": "Research Agent",
            "description": "Conducts research, gathers information",
            "capabilities": ["web_search", "document_research", "data_analysis"],
            "dependencies": []
        },
        {
            "agent_name": "grants",
            "display_name": "Grants Agent",
            "description": "Researches grants, writes proposals",
            "capabilities": ["search_grants", "analyze_rfp", "draft_proposal"],
            "dependencies": ["research"]
        },
        {
            "agent_name": "ministry",
            "display_name": "Ministry AI",
            "description": "Sermon preparation, theological exploration",
            "capabilities": ["sermon_prep", "biblical_analysis", "theological_research"],
            "dependencies": ["research"]
        }
    ]
    
    for agent in agents:
        # Check if exists
        cursor.execute("SELECT agent_name FROM agent_capabilities WHERE agent_name = ?", (agent["agent_name"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO agent_capabilities (
                    agent_name, display_name, description, capabilities_json,
                    dependencies, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent["agent_name"],
                agent["display_name"],
                agent["description"],
                json.dumps(agent["capabilities"]),
                json.dumps(agent["dependencies"]),
                datetime.utcnow().isoformat()
            ))
    
    conn.commit()
    print(f"✅ Seeded {len(agents)} agent capabilities")


def main():
    """Run the migration."""
    print(f"📂 Database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        create_agent_messaging_tables(conn)
        seed_agent_capabilities(conn)
        
        print("\n✅ Agent messaging migration complete!")
        
        # Show table info
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%agent%'")
        tables = cursor.fetchall()
        print("\n📊 Agent-related tables:")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
