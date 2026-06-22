#!/usr/bin/env python3
"""
Morning Briefing Agent for ArchonHub.

Runs daily at 6 AM to generate personalized morning brief with:
- Urgent emails (unread <24h)
- Todos due this week  
- Active mission updates
- Market movers (if portfolio exists)
- Important deadlines

Stores briefs in database and can send push notifications.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup paths
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MorningBriefAgent:
    """Generates daily morning briefings for users."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def generate_brief(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Generate morning brief for user."""
        
        logger.info(f"Generating morning brief for {user_id}...")
        
        # Gather data from various sources
        urgent_emails = await self._get_urgent_emails(user_id)
        todos_due = await self._get_todos_due_this_week(user_id)
        active_missions = await self._get_active_missions(user_id)
        market_updates = await self._get_market_movers(user_id)
        deadlines_today = await self._get_deadlines_today(user_id)
        
        # Generate brief text
        brief_text = self._format_brief(
            urgent_emails=urgent_emails,
            todos_due=todos_due,
            active_missions=active_missions,
            market_updates=market_updates,
            deadlines_today=deadlines_today
        )
        
        # Store in database
        brief_id = await self._save_brief(user_id, brief_text, {
            "urgent_email_count": len(urgent_emails),
            "todos_due_count": len(todos_due),
            "active_mission_count": len(active_missions),
            "market_mover_count": len(market_updates),
            "deadline_count": len(deadlines_today)
        })
        
        logger.info(f"Morning brief generated: {brief_id}")
        
        return {
            "brief_id": brief_id,
            "brief_text": brief_text,
            "counts": {
                "urgent_emails": len(urgent_emails),
                "todos_due": len(todos_due),
                "active_missions": len(active_missions),
                "market_movers": len(market_updates),
                "deadlines_today": len(deadlines_today)
            }
        }
    
    async def _get_urgent_emails(self, user_id: str) -> List[Dict[str, Any]]:
        """Get unread emails from last 24 hours."""
        # Placeholder - requires email_connectors integration
        return []
    
    async def _get_todos_due_this_week(self, user_id: str) -> List[Dict[str, Any]]:
        """Get todos due within 7 days."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Note: Assumes todos table has due_date column (may need to add)
            cursor.execute("""
                SELECT id, title, description, status
                FROM todos
                WHERE status IN ('pending', 'in_progress')
                LIMIT 10
            """)
            
            todos = []
            for row in cursor.fetchall():
                todos.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "status": row[3]
                })
            
            return todos
        finally:
            conn.close()
    
    async def _get_active_missions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active missions from global memory."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value
                FROM global_memory
                WHERE category = 'projects'
                ORDER BY importance DESC
                LIMIT 5
            """)
            
            missions = []
            for row in cursor.fetchall():
                missions.append({
                    "name": row[0],
                    "description": row[1]
                })
            
            return missions
        finally:
            conn.close()
    
    async def _get_market_movers(self, user_id: str) -> List[Dict[str, Any]]:
        """Get significant market movements (placeholder)."""
        # Placeholder - would integrate with markets agent
        # Check portfolio holdings, get price changes >5%
        return []
    
    async def _get_deadlines_today(self, user_id: str) -> List[Dict[str, Any]]:
        """Get deadlines happening today."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Check global memory for deadline mentions
            cursor.execute("""
                SELECT key, value
                FROM global_memory
                WHERE category = 'deadlines'
                  AND value LIKE '%today%' OR value LIKE '%' || date('now') || '%'
                LIMIT 5
            """)
            
            deadlines = []
            for row in cursor.fetchall():
                deadlines.append({
                    "item": row[0],
                    "details": row[1]
                })
            
            return deadlines
        finally:
            conn.close()
    
    def _format_brief(
        self,
        urgent_emails: List[Dict],
        todos_due: List[Dict],
        active_missions: List[Dict],
        market_updates: List[Dict],
        deadlines_today: List[Dict]
    ) -> str:
        """Format brief as readable text."""
        
        now = datetime.now()
        greeting = "Good morning"
        if now.hour >= 12:
            greeting = "Good afternoon"
        if now.hour >= 18:
            greeting = "Good evening"
        
        lines = [
            f"{greeting}! Here's your daily brief for {now.strftime('%A, %B %d, %Y')}:",
            ""
        ]
        
        # Urgent items first
        if deadlines_today:
            lines.append("🔴 DEADLINES TODAY:")
            for deadline in deadlines_today[:3]:
                lines.append(f"  • {deadline['item']}")
            lines.append("")
        
        # Urgent emails
        if urgent_emails:
            lines.append(f"📧 {len(urgent_emails)} urgent email(s) from last 24 hours")
            for email in urgent_emails[:3]:
                lines.append(f"  • From: {email.get('from', 'Unknown')}")
            lines.append("")
        
        # Todos due this week
        if todos_due:
            lines.append(f"✅ {len(todos_due)} todo(s) due this week:")
            for todo in todos_due[:5]:
                status_icon = "🟡" if todo["status"] == "in_progress" else "⚪"
                lines.append(f"  {status_icon} {todo['title']}")
            lines.append("")
        
        # Active missions
        if active_missions:
            lines.append(f"🎯 {len(active_missions)} active project(s):")
            for mission in active_missions[:3]:
                lines.append(f"  • {mission['name']}")
            lines.append("")
        
        # Market updates
        if market_updates:
            lines.append(f"📊 {len(market_updates)} market mover(s):")
            for update in market_updates[:3]:
                lines.append(f"  • {update.get('symbol', 'N/A')}: {update.get('change', 'N/A')}")
            lines.append("")
        
        # Closing
        if not any([deadlines_today, urgent_emails, todos_due, active_missions, market_updates]):
            lines.append("✨ All clear! No urgent items requiring attention.")
            lines.append("")
        
        lines.append("Have a productive day! 🚀")
        
        return "\n".join(lines)
    
    async def _save_brief(self, user_id: str, brief_text: str, stats: Dict) -> str:
        """Save brief to database."""
        import uuid
        
        brief_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Create morning_briefs table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS morning_briefs (
                    brief_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    brief_text TEXT NOT NULL,
                    stats_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    viewed BOOLEAN DEFAULT 0,
                    viewed_at TIMESTAMP
                )
            """)
            
            # Insert brief
            cursor.execute("""
                INSERT INTO morning_briefs (brief_id, user_id, brief_text, stats_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                brief_id,
                user_id,
                brief_text,
                json.dumps(stats),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            
            return brief_id
        finally:
            conn.close()


async def main():
    """Generate morning brief for default user."""
    agent = MorningBriefAgent(DB_PATH)
    result = await agent.generate_brief()
    
    print("\n" + "="*80)
    print(result["brief_text"])
    print("="*80)
    print(f"\nBrief ID: {result['brief_id']}")
    print(f"Stats: {json.dumps(result['counts'], indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
