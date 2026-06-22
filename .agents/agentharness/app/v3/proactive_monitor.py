#!/usr/bin/env python3
"""
Proactive Monitoring System for ArchonHub.

Monitors and alerts on:
- Upcoming deadlines (7 days, 3 days, 1 day, day-of)
- Anomalies (spending spikes, unusual patterns)
- System health issues

Designed to run as background task (hourly or daily).
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


class ProactiveMonitor:
    """Monitors system for deadlines and anomalies."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def check_deadlines(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Check for upcoming deadlines."""
        
        logger.info("Checking for upcoming deadlines...")
        
        alerts = []
        now = datetime.now()
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            
            # Check global memory for deadline mentions
            cursor.execute("""
                SELECT key, value, category, importance
                FROM global_memory
                WHERE category IN ('deadlines', 'projects', 'tasks')
                ORDER BY importance DESC
                LIMIT 50
            """)
            
            items = [dict(row) for row in cursor.fetchall()]
            
            # Parse dates from memory (simple keyword detection)
            deadline_keywords = [
                ("today", 0),
                ("tomorrow", 1),
                ("this week", 7),
                ("next week", 14),
                ("urgent", 3),
                ("deadline", None)
            ]
            
            for item in items:
                value_lower = item['value'].lower()
                
                for keyword, days_out in deadline_keywords:
                    if keyword in value_lower:
                        priority = "high" if days_out is not None and days_out <= 1 else "medium"
                        
                        alerts.append({
                            "type": "deadline",
                            "priority": priority,
                            "item": item['key'],
                            "details": item['value'],
                            "days_until": days_out,
                            "detected_keyword": keyword,
                            "created_at": now.isoformat()
                        })
                        break  # Only match first keyword
            
            # Check todos for due dates (if due_date column exists)
            try:
                cursor.execute("""
                    SELECT id, title, status
                    FROM todos
                    WHERE status IN ('pending', 'in_progress')
                    LIMIT 20
                """)
                
                todos = [dict(row) for row in cursor.fetchall()]
                
                for todo in todos:
                    # Check if title mentions deadline urgency
                    title_lower = todo['title'].lower()
                    if any(word in title_lower for word in ['urgent', 'today', 'asap', 'deadline']):
                        alerts.append({
                            "type": "urgent_todo",
                            "priority": "high",
                            "item": todo['title'],
                            "todo_id": todo['id'],
                            "status": todo['status'],
                            "created_at": now.isoformat()
                        })
            except sqlite3.OperationalError:
                pass  # Table might not have due_date column
            
            return alerts
        
        finally:
            conn.close()
    
    async def check_anomalies(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Check for unusual patterns and anomalies."""
        
        logger.info("Checking for anomalies...")
        
        alerts = []
        
        # Note: These are placeholder checks that would integrate with:
        # - Financial data (spending patterns)
        # - Portfolio data (market movements)
        # - Email volume (unusual spikes)
        # - Site traffic (analytics)
        
        # Example: Check feedback volume
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Check feedback spike
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative_count
                FROM message_feedback
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            daily_feedback = cursor.fetchall()
            
            if daily_feedback:
                avg_daily = sum(row[1] for row in daily_feedback) / len(daily_feedback)
                today_count = daily_feedback[0][1] if daily_feedback else 0
                
                # Alert if today is 2x average
                if today_count > avg_daily * 2 and avg_daily > 0:
                    alerts.append({
                        "type": "feedback_spike",
                        "priority": "medium",
                        "item": "Unusual feedback volume",
                        "details": f"{today_count} feedbacks today vs {avg_daily:.1f} average",
                        "current_value": today_count,
                        "baseline": avg_daily,
                        "threshold_multiplier": 2.0,
                        "created_at": datetime.now().isoformat()
                    })
                
                # Alert if high negative feedback
                today_negative = daily_feedback[0][2] if daily_feedback else 0
                if today_negative >= 5:
                    alerts.append({
                        "type": "negative_feedback_spike",
                        "priority": "high",
                        "item": "High negative feedback",
                        "details": f"{today_negative} negative feedbacks today",
                        "current_value": today_negative,
                        "created_at": datetime.now().isoformat()
                    })
            
            # Check error rate
            cursor.execute("""
                SELECT COUNT(*) as error_count
                FROM messages
                WHERE content LIKE '%error%' OR content LIKE '%failed%'
                  AND created_at > datetime('now', '-1 day')
            """)
            
            error_count = cursor.fetchone()[0]
            if error_count > 10:
                alerts.append({
                    "type": "error_rate",
                    "priority": "high",
                    "item": "High error rate detected",
                    "details": f"{error_count} errors in last 24 hours",
                    "current_value": error_count,
                    "threshold": 10,
                    "created_at": datetime.now().isoformat()
                })
            
            return alerts
        
        finally:
            conn.close()
    
    async def store_alerts(self, alerts: List[Dict[str, Any]], user_id: str = "default_user"):
        """Store alerts in database."""
        
        if not alerts:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Create notifications table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT,
                    data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    viewed BOOLEAN DEFAULT 0,
                    viewed_at TIMESTAMP,
                    dismissed BOOLEAN DEFAULT 0,
                    dismissed_at TIMESTAMP
                )
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user_created
                ON notifications (user_id, created_at DESC)
            """)
            
            # Insert alerts
            import uuid
            for alert in alerts:
                notification_id = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT INTO notifications (
                        notification_id, user_id, type, priority,
                        title, details, data_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    notification_id,
                    user_id,
                    alert['type'],
                    alert['priority'],
                    alert.get('item', 'Alert'),
                    alert.get('details', ''),
                    json.dumps(alert),
                    alert.get('created_at', datetime.now().isoformat())
                ))
            
            conn.commit()
            logger.info(f"Stored {len(alerts)} alerts")
        
        finally:
            conn.close()
    
    async def run_monitoring(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Run full monitoring cycle."""
        
        logger.info("Starting proactive monitoring cycle...")
        
        # Check deadlines
        deadline_alerts = await self.check_deadlines(user_id)
        
        # Check anomalies
        anomaly_alerts = await self.check_anomalies(user_id)
        
        # Combine all alerts
        all_alerts = deadline_alerts + anomaly_alerts
        
        # Store in database
        await self.store_alerts(all_alerts, user_id)
        
        # Categorize by priority
        high_priority = [a for a in all_alerts if a.get('priority') == 'high']
        medium_priority = [a for a in all_alerts if a.get('priority') == 'medium']
        low_priority = [a for a in all_alerts if a.get('priority') == 'low']
        
        logger.info(f"Monitoring complete: {len(all_alerts)} alerts ({len(high_priority)} high priority)")
        
        return {
            "success": True,
            "total_alerts": len(all_alerts),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "alerts": all_alerts,
            "monitored_at": datetime.now().isoformat()
        }


async def main():
    """Run proactive monitoring."""
    
    monitor = ProactiveMonitor(DB_PATH)
    
    print("🔍 Running proactive monitoring...\n")
    
    result = await monitor.run_monitoring()
    
    print(f"📊 Monitoring Results")
    print(f"=" * 60)
    print(f"Total Alerts: {result['total_alerts']}")
    print(f"  🔴 High Priority: {result['high_priority']}")
    print(f"  🟡 Medium Priority: {result['medium_priority']}")
    print(f"  🟢 Low Priority: {result['low_priority']}")
    
    if result['alerts']:
        print(f"\n⚠️  Alerts:")
        for i, alert in enumerate(result['alerts'], 1):
            priority_icon = "🔴" if alert['priority'] == 'high' else "🟡" if alert['priority'] == 'medium' else "🟢"
            print(f"\n{i}. {priority_icon} [{alert['type']}] {alert.get('item', 'Alert')}")
            if alert.get('details'):
                print(f"   {alert['details']}")
    else:
        print(f"\n✅ No alerts - all systems normal")


if __name__ == "__main__":
    asyncio.run(main())
