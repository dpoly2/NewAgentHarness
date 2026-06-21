#!/usr/bin/env python3
"""
Add prompt_templates table to database.

This enables saved, reusable prompts for common workflows.
Run this once to create the table and seed initial templates.
"""

import sqlite3
from pathlib import Path
import json

# Path to the database
DB_PATH = Path(__file__).parent.parent.parent / "memory" / "runs_v3.db"


def add_prompt_templates_table():
    """Create prompt_templates table."""
    print(f"📊 Connecting to database: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_templates'")
        if cursor.fetchone():
            print("✅ prompt_templates table already exists")
            return
        
        print("🔨 Creating prompt_templates table...")
        
        # Create table
        cursor.execute("""
            CREATE TABLE prompt_templates (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                prompt_text TEXT NOT NULL,
                agent_id TEXT DEFAULT 'inez',
                project_slug TEXT DEFAULT '',
                is_system INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        
        print("✅ Table created successfully!")
        
        # Seed initial templates
        print("🌱 Seeding initial templates...")
        seed_templates(conn)
        
        cursor.execute("SELECT COUNT(*) as count FROM prompt_templates")
        count = cursor.fetchone()['count']
        print(f"✅ Seeded {count} templates")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()


def seed_templates(conn):
    """Seed initial prompt templates for common workflows."""
    from datetime import datetime
    import uuid
    
    now = datetime.utcnow().isoformat() + 'Z'
    
    templates = [
        # Markets Division
        {
            'id': str(uuid.uuid4()),
            'title': 'Generate Weekly Market Brief',
            'category': 'markets',
            'prompt_text': 'Generate a comprehensive weekly market briefing for the HP Engineering portfolio. Include: (1) Key market movements in tech/AI sector, (2) Portfolio performance summary, (3) Notable news for TSLA, NVDA, META, (4) Economic indicators, (5) Strategic recommendations for next week.',
            'agent_id': 'inez',
            'project_slug': 'markets',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Market Sector Analysis',
            'category': 'markets',
            'prompt_text': 'Analyze the current state of [SECTOR] sector. Include: (1) Top performers and underperformers, (2) Key trends and catalysts, (3) Valuation metrics, (4) Investment opportunities, (5) Risk factors to watch.',
            'agent_id': 'inez',
            'project_slug': 'markets',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        
        # Grants / PBS Foundation
        {
            'id': str(uuid.uuid4()),
            'title': 'Grant Proposal Outline',
            'category': 'grants',
            'prompt_text': 'Create a grant proposal outline for [PROJECT NAME]. Include: (1) Executive summary template, (2) Need statement structure, (3) Project description sections, (4) Budget narrative framework, (5) Evaluation plan, (6) Sustainability strategy. Tailor for [FUNDER NAME].',
            'agent_id': 'inez',
            'project_slug': 'pbs-foundation',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Research Grant Opportunities',
            'category': 'grants',
            'prompt_text': 'Research available grants for [PROGRAM/PROJECT AREA]. Search for: (1) Federal grants (Grants.gov), (2) Foundation grants, (3) Corporate giving programs, (4) State/local opportunities. Provide: grant name, funder, amount, deadline, eligibility, and fit score.',
            'agent_id': 'inez',
            'project_slug': 'pbs-foundation',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        
        # Development / Engineering
        {
            'id': str(uuid.uuid4()),
            'title': 'Sprint Planning Agenda',
            'category': 'development',
            'prompt_text': 'Create a sprint planning agenda for [PROJECT] week of [DATE]. Include: (1) Previous sprint review summary, (2) Backlog items ready for sprint, (3) Priority ranking, (4) Capacity planning, (5) Dependencies and blockers, (6) Sprint goal statement.',
            'agent_id': 'inez',
            'project_slug': 'xftc',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Technical Architecture Review',
            'category': 'development',
            'prompt_text': 'Review the technical architecture for [FEATURE/SYSTEM]. Analyze: (1) Current architecture diagram, (2) Scalability considerations, (3) Security vulnerabilities, (4) Performance bottlenecks, (5) Technology choices, (6) Recommendations for improvement.',
            'agent_id': 'inez',
            'project_slug': 'xftc',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'WordPress Plugin Feature Spec',
            'category': 'development',
            'prompt_text': 'Write a feature specification for [FEATURE NAME] in the PBS Event Commerce plugin. Include: (1) User story and use case, (2) Functional requirements, (3) UI/UX mockup description, (4) Database schema changes, (5) API endpoints needed, (6) Testing scenarios.',
            'agent_id': 'inez',
            'project_slug': 'xftc',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        
        # Finance
        {
            'id': str(uuid.uuid4()),
            'title': 'Monthly Financial Report',
            'category': 'finance',
            'prompt_text': 'Generate monthly financial report for [MONTH YEAR]. Include: (1) Revenue summary by division, (2) Expense breakdown, (3) Cash flow analysis, (4) Budget variance report, (5) Key metrics and KPIs, (6) Financial outlook for next month.',
            'agent_id': 'inez',
            'project_slug': '',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        
        # General / Operations
        {
            'id': str(uuid.uuid4()),
            'title': 'Morning Operations Briefing',
            'category': 'operations',
            'prompt_text': 'Provide a comprehensive morning operations briefing covering: (1) Urgent items requiring attention today, (2) Status of active missions, (3) Agent activity summary, (4) Notable events from overnight, (5) Priority recommendations for today.',
            'agent_id': 'inez',
            'project_slug': '',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Meeting Agenda Generator',
            'category': 'operations',
            'prompt_text': 'Create a meeting agenda for [MEETING TYPE] with [PARTICIPANTS]. Include: (1) Meeting objectives, (2) Time-boxed agenda items, (3) Pre-reading materials needed, (4) Discussion questions, (5) Decision points, (6) Action items template.',
            'agent_id': 'inez',
            'project_slug': '',
            'is_system': 1,
            'usage_count': 0,
            'created_at': now,
            'updated_at': now
        },
    ]
    
    cursor = conn.cursor()
    for template in templates:
        cursor.execute("""
            INSERT INTO prompt_templates 
            (id, title, category, prompt_text, agent_id, project_slug, is_system, usage_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template['id'],
            template['title'],
            template['category'],
            template['prompt_text'],
            template['agent_id'],
            template['project_slug'],
            template['is_system'],
            template['usage_count'],
            template['created_at'],
            template['updated_at']
        ))
    
    conn.commit()


if __name__ == "__main__":
    add_prompt_templates_table()
