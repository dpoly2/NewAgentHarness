#!/usr/bin/env python3
"""
Learning Feedback Loop for ArchonHub.

Analyzes user feedback patterns to improve agent responses:
- Aggregates positive vs negative feedback
- Identifies patterns (response length, tone, format preferences)
- Generates prompt adjustments
- A/B tests changes
- Rolls back if performance degrades

Runs weekly or on-demand.
"""

import asyncio
import json
import logging
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup paths
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
DB_PATH = HARNESS / "memory" / "runs_v3.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackLearner:
    """Analyzes feedback and generates learning insights."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def analyze_feedback(self, days: int = 7, user_id: str = "default_user") -> Dict[str, Any]:
        """Analyze feedback patterns from the last N days."""
        
        logger.info(f"Analyzing feedback from last {days} days for user {user_id}")
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get all feedback
            cursor.execute("""
                SELECT mf.*, m.content as message_content, m.role
                FROM message_feedback mf
                LEFT JOIN messages m ON mf.message_id = m.id
                WHERE mf.user_id = ? AND mf.created_at > ?
                ORDER BY mf.created_at DESC
            """, (user_id, cutoff))
            
            feedback_items = [dict(row) for row in cursor.fetchall()]
            
            if not feedback_items:
                logger.info("No feedback found in time period")
                return {
                    "period_days": days,
                    "total_feedback": 0,
                    "insights": [],
                    "recommendations": []
                }
            
            # Analyze patterns
            insights = []
            
            # 1. Overall sentiment
            positive_count = sum(1 for f in feedback_items if f['rating'] == 1)
            negative_count = sum(1 for f in feedback_items if f['rating'] == -1)
            sentiment_ratio = positive_count / len(feedback_items) if feedback_items else 0
            
            insights.append({
                "type": "sentiment",
                "positive": positive_count,
                "negative": negative_count,
                "ratio": sentiment_ratio,
                "status": "good" if sentiment_ratio > 0.7 else "needs_improvement"
            })
            
            # 2. Category analysis
            category_ratings = defaultdict(lambda: {"positive": 0, "negative": 0})
            for item in feedback_items:
                cat = item.get('category') or 'other'
                if item['rating'] == 1:
                    category_ratings[cat]["positive"] += 1
                else:
                    category_ratings[cat]["negative"] += 1
            
            problem_categories = []
            for cat, counts in category_ratings.items():
                total = counts["positive"] + counts["negative"]
                if total >= 3:  # At least 3 ratings
                    ratio = counts["positive"] / total
                    if ratio < 0.5:  # More negative than positive
                        problem_categories.append({
                            "category": cat,
                            "positive": counts["positive"],
                            "negative": counts["negative"],
                            "ratio": ratio
                        })
            
            if problem_categories:
                insights.append({
                    "type": "problem_categories",
                    "categories": problem_categories
                })
            
            # 3. Response length analysis
            negative_messages = [f for f in feedback_items if f['rating'] == -1 and f['message_content']]
            positive_messages = [f for f in feedback_items if f['rating'] == 1 and f['message_content']]
            
            if negative_messages and positive_messages:
                avg_negative_length = sum(len(f['message_content'].split()) for f in negative_messages) / len(negative_messages)
                avg_positive_length = sum(len(f['message_content'].split()) for f in positive_messages) / len(positive_messages)
                
                length_diff = avg_negative_length - avg_positive_length
                
                if abs(length_diff) > 50:  # Significant difference
                    insights.append({
                        "type": "response_length",
                        "avg_negative_words": int(avg_negative_length),
                        "avg_positive_words": int(avg_positive_length),
                        "difference": int(length_diff),
                        "recommendation": "shorter" if length_diff > 0 else "longer"
                    })
            
            # 4. Feedback text analysis
            negative_feedback_texts = [f['feedback_text'] for f in feedback_items 
                                      if f['rating'] == -1 and f.get('feedback_text')]
            
            common_complaints = self._extract_common_phrases(negative_feedback_texts)
            if common_complaints:
                insights.append({
                    "type": "common_complaints",
                    "phrases": common_complaints[:5]  # Top 5
                })
            
            # 5. Get corrections
            cursor.execute("""
                SELECT correction_type, COUNT(*) as count
                FROM corrections
                WHERE user_id = ? AND created_at > ?
                GROUP BY correction_type
                ORDER BY count DESC
            """, (user_id, cutoff))
            
            corrections = [dict(row) for row in cursor.fetchall()]
            if corrections:
                insights.append({
                    "type": "corrections",
                    "breakdown": corrections
                })
            
            # Generate recommendations
            recommendations = self._generate_recommendations(insights)
            
            # Update user style preferences
            await self._update_style_preferences(user_id, insights, conn)
            
            return {
                "period_days": days,
                "total_feedback": len(feedback_items),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "insights": insights,
                "recommendations": recommendations,
                "analyzed_at": datetime.now().isoformat()
            }
        
        finally:
            conn.close()
    
    def _extract_common_phrases(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Extract common complaint phrases from feedback text."""
        
        if not texts:
            return []
        
        # Common complaint keywords
        keywords = {
            "too long": "Response length",
            "too verbose": "Response length",
            "too short": "Response length",
            "too technical": "Technical complexity",
            "confusing": "Clarity",
            "wrong": "Accuracy",
            "not helpful": "Helpfulness",
            "didn't answer": "Relevance",
            "missed": "Completeness",
            "tone": "Communication tone"
        }
        
        phrase_counts = Counter()
        
        for text in texts:
            text_lower = text.lower()
            for phrase, category in keywords.items():
                if phrase in text_lower:
                    phrase_counts[category] += 1
        
        return [
            {"issue": category, "count": count}
            for category, count in phrase_counts.most_common()
        ]
    
    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations from insights."""
        
        recommendations = []
        
        for insight in insights:
            insight_type = insight.get("type")
            
            if insight_type == "sentiment":
                if insight["status"] == "needs_improvement":
                    recommendations.append(
                        f"Overall satisfaction is low ({insight['ratio']:.0%}). "
                        f"Review negative feedback categories and adjust response style."
                    )
            
            elif insight_type == "problem_categories":
                for cat in insight["categories"]:
                    recommendations.append(
                        f"Category '{cat['category']}' needs improvement "
                        f"({cat['ratio']:.0%} positive). Focus on addressing user concerns in this area."
                    )
            
            elif insight_type == "response_length":
                if insight["recommendation"] == "shorter":
                    recommendations.append(
                        f"Responses are too long (avg {insight['avg_negative_words']} words in negative feedback "
                        f"vs {insight['avg_positive_words']} in positive). Aim for more concise responses."
                    )
                else:
                    recommendations.append(
                        f"Responses are too short (avg {insight['avg_negative_words']} words in negative feedback "
                        f"vs {insight['avg_positive_words']} in positive). Provide more detailed explanations."
                    )
            
            elif insight_type == "common_complaints":
                top_issues = [p['issue'] for p in insight['phrases'][:3]]
                recommendations.append(
                    f"Most common issues: {', '.join(top_issues)}. "
                    f"Consider prompt adjustments to address these concerns."
                )
            
            elif insight_type == "corrections":
                top_correction = insight['breakdown'][0]['correction_type']
                recommendations.append(
                    f"Most frequent correction type: '{top_correction}'. "
                    f"Review these corrections to improve understanding."
                )
        
        if not recommendations:
            recommendations.append("Feedback is positive overall. Continue current approach.")
        
        return recommendations
    
    async def _update_style_preferences(
        self, 
        user_id: str, 
        insights: List[Dict[str, Any]], 
        conn: sqlite3.Connection
    ):
        """Update user style preferences based on insights."""
        
        cursor = conn.cursor()
        
        # Get or create preferences
        cursor.execute("""
            SELECT * FROM user_style_preferences WHERE user_id = ?
        """, (user_id,))
        
        existing = cursor.fetchone()
        
        # Determine preferred length
        preferred_length = "medium"  # default
        for insight in insights:
            if insight.get("type") == "response_length":
                if insight.get("recommendation") == "shorter":
                    preferred_length = "concise"
                elif insight.get("recommendation") == "longer":
                    preferred_length = "detailed"
        
        # Count feedback
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative
            FROM message_feedback
            WHERE user_id = ?
        """, (user_id,))
        
        counts = cursor.fetchone()
        positive_total = counts[0] if counts else 0
        negative_total = counts[1] if counts else 0
        
        # Update or insert
        if existing:
            cursor.execute("""
                UPDATE user_style_preferences
                SET preferred_length = ?,
                    total_positive_feedback = ?,
                    total_negative_feedback = ?,
                    last_updated = ?
                WHERE user_id = ?
            """, (
                preferred_length,
                positive_total,
                negative_total,
                datetime.now().isoformat(),
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_style_preferences (
                    user_id, preferred_length, total_positive_feedback,
                    total_negative_feedback, last_updated
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, preferred_length, positive_total,
                negative_total, datetime.now().isoformat()
            ))
        
        conn.commit()
        logger.info(f"Updated style preferences for {user_id}: {preferred_length}")
    
    def get_user_preferences(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Get learned style preferences for a user."""
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_style_preferences WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Return defaults
            return {
                "user_id": user_id,
                "preferred_length": "medium",
                "preferred_formality": "professional",
                "use_emojis": True,
                "citation_density": "medium",
                "code_style": "explained"
            }
        
        finally:
            conn.close()


async def main():
    """Run feedback analysis."""
    
    learner = FeedbackLearner(DB_PATH)
    
    print("🔍 Analyzing feedback patterns...\n")
    
    result = await learner.analyze_feedback(days=30)
    
    print(f"📊 Analysis Results (last {result['period_days']} days)")
    print(f"=" * 60)
    print(f"Total Feedback: {result['total_feedback']}")
    print(f"Positive: {result['positive_count']} ({result['positive_count']/result['total_feedback']:.0%})" if result['total_feedback'] else "Positive: 0")
    print(f"Negative: {result['negative_count']} ({result['negative_count']/result['total_feedback']:.0%})" if result['total_feedback'] else "Negative: 0")
    
    print(f"\n💡 Insights:")
    for i, insight in enumerate(result['insights'], 1):
        print(f"\n{i}. {insight['type'].replace('_', ' ').title()}")
        print(f"   {json.dumps(insight, indent=3)}")
    
    print(f"\n📋 Recommendations:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Show current preferences
    prefs = learner.get_user_preferences()
    print(f"\n⚙️  Current Style Preferences:")
    print(f"   Length: {prefs['preferred_length']}")
    print(f"   Formality: {prefs['preferred_formality']}")
    print(f"   Emojis: {'Yes' if prefs.get('use_emojis') else 'No'}")


if __name__ == "__main__":
    asyncio.run(main())
