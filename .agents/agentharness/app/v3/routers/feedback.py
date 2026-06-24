from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.config import DB_PATH

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("feedback")
router = APIRouter()

@router.post("/messages/{message_id}/feedback")
async def submit_feedback(message_id: str, request: dict, current_user: dict = Depends(get_current_user)):
    """Submit thumbs up/down feedback on a message."""
    try:
        rating = request.get("rating")  # 1 or -1
        feedback_text = request.get("feedback_text", "")
        category = request.get("category", "other")
        user_id = current_user.get("username", "default_user")
        
        if rating not in [1, -1]:
            raise HTTPException(status_code=400, detail="Rating must be 1 or -1")
        
        # Store feedback
        feedback_id = str(uuid.uuid4())
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            
            # Get conversation_id from message
            cursor.execute("SELECT conversation_id FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            conversation_id = row[0] if row else None
            
            # Insert or update feedback
            cursor.execute("""
                INSERT INTO message_feedback (
                    feedback_id, message_id, user_id, conversation_id,
                    rating, feedback_text, category, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id, user_id) DO UPDATE SET
                    rating = excluded.rating,
                    feedback_text = excluded.feedback_text,
                    category = excluded.category,
                    created_at = excluded.created_at
            """, (
                feedback_id, message_id, user_id, conversation_id,
                rating, feedback_text, category, datetime.utcnow().isoformat()
            ))
            conn.commit()
            
            logger.info(f"Feedback submitted: {message_id} = {'👍' if rating == 1 else '👎'}")
            
            return {
                "success": True,
                "feedback_id": feedback_id,
                "rating": rating
            }
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/corrections")
async def submit_correction(request: dict, current_user: dict = Depends(get_current_user)):
    """Submit a user correction to learn from."""
    try:
        message_id = request.get("message_id")
        corrected_intent = request.get("corrected_intent")
        correction_text = request.get("correction_text")
        user_id = current_user.get("username", "default_user")
        correction_type = request.get("correction_type", "clarification")
        
        if not all([message_id, corrected_intent, correction_text]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        correction_id = str(uuid.uuid4())
        conn = sqlite3.connect(str(DB_PATH))
        try:
            cursor = conn.cursor()
            
            # Get conversation_id and original message
            cursor.execute("""
                SELECT conversation_id, content 
                FROM messages 
                WHERE id = ? AND role = 'user'
            """, (message_id,))
            row = cursor.fetchone()
            conversation_id, original_intent = row if row else (None, None)
            
            # Insert correction
            cursor.execute("""
                INSERT INTO corrections (
                    correction_id, message_id, user_id, conversation_id,
                    original_intent, corrected_intent, correction_text,
                    correction_type, applied, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                correction_id, message_id, user_id, conversation_id,
                original_intent, corrected_intent, correction_text,
                correction_type, datetime.utcnow().isoformat()
            ))
            conn.commit()
            
            logger.info(f"Correction captured: {message_id}")
            
            return {
                "success": True,
                "correction_id": correction_id,
                "message": "Correction learned"
            }
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit correction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/stats")
async def get_feedback_stats(current_user: dict = Depends(get_current_user)):
    """Get feedback statistics for a user."""
    try:
        user_id = current_user.get("username", "default_user")
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative_count
                FROM message_feedback
                WHERE user_id = ?
            """, (user_id,))
            stats = dict(cursor.fetchone())
            
            # Recent feedback
            cursor.execute("""
                SELECT message_id, rating, category, feedback_text, created_at
                FROM message_feedback
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (user_id,))
            recent = [dict(row) for row in cursor.fetchall()]
            
            # Corrections count
            cursor.execute("""
                SELECT COUNT(*) as correction_count
                FROM corrections
                WHERE user_id = ?
            """, (user_id,))
            corrections = dict(cursor.fetchone())
            
            return {
                "success": True,
                "stats": {**stats, **corrections},
                "recent_feedback": recent
            }
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Get feedback stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/analyze")
async def analyze_feedback(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Analyze feedback patterns and generate learning insights."""
    try:
        user_id = current_user.get("username", "default_user")
        from feedback_learner import FeedbackLearner
        
        learner = FeedbackLearner(DB_PATH)
        result = await learner.analyze_feedback(days=days, user_id=user_id)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Feedback analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get learned style preferences for a user."""
    try:
        user_id = current_user.get("username", "default_user")
        from feedback_learner import FeedbackLearner
        
        learner = FeedbackLearner(DB_PATH)
        preferences = learner.get_user_preferences(user_id)
        
        return {
            "success": True,
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
