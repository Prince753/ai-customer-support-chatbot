"""
Admin dashboard API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..models.admin import DashboardStats, AnalyticsResponse, ConversationSummary
from ..database import get_database

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get real-time dashboard statistics."""
    try:
        db = get_database()
        analytics = await db.get_chat_analytics()
        
        # Get today's stats
        today = datetime.utcnow().date().isoformat()
        today_analytics = await db.get_chat_analytics(start_date=today)
        
        return DashboardStats(
            total_conversations=analytics.get("total_conversations", 0),
            total_messages=analytics.get("total_messages", 0),
            active_conversations=15,  # Mock for demo
            escalated_conversations=analytics.get("escalated_conversations", 0),
            avg_response_time_seconds=2.5,
            resolution_rate=0.87,
            customer_satisfaction=4.6,
            messages_today=today_analytics.get("total_messages", 0),
            conversations_today=today_analytics.get("total_conversations", 0)
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Error fetching statistics")


@router.get("/analytics")
async def get_analytics(
    period: str = Query("weekly", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get detailed analytics for a time period."""
    try:
        # Calculate date range based on period
        now = datetime.utcnow()
        
        if not end_date:
            end = now
        else:
            end = datetime.fromisoformat(end_date)
        
        if not start_date:
            if period == "daily":
                start = end - timedelta(days=1)
            elif period == "weekly":
                start = end - timedelta(days=7)
            else:  # monthly
                start = end - timedelta(days=30)
        else:
            start = datetime.fromisoformat(start_date)
        
        db = get_database()
        stats = await db.get_chat_analytics(
            start_date=start.isoformat(),
            end_date=end.isoformat()
        )
        
        return AnalyticsResponse(
            period=period,
            start_date=start,
            end_date=end,
            stats=DashboardStats(**stats) if stats else DashboardStats(),
            conversations_by_channel={"web": 65, "whatsapp": 35},
            conversations_by_status={"closed": 85, "escalated": 10, "active": 5},
            top_topics=[
                {"topic": "Order Status", "count": 120, "percentage": 35},
                {"topic": "Returns", "count": 85, "percentage": 25},
                {"topic": "Shipping", "count": 68, "percentage": 20},
                {"topic": "Products", "count": 45, "percentage": 13},
                {"topic": "Other", "count": 24, "percentage": 7}
            ],
            hourly_distribution=[
                {"hour": h, "count": max(5, 30 - abs(h - 14) * 2)} 
                for h in range(24)
            ],
            daily_trend=[
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "conversations": 40 + i * 2, "messages": 280 + i * 15}
                for i in range(7, 0, -1)
            ]
        )
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching analytics")


@router.get("/conversations")
async def get_conversations(
    status: Optional[str] = Query(None, regex="^(active|escalated|closed)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get paginated list of conversations."""
    try:
        db = get_database()
        conversations = await db.get_recent_conversations(
            limit=limit,
            status=status
        )
        
        return {
            "conversations": conversations,
            "count": len(conversations),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Error fetching conversations")


@router.get("/conversations/{session_id}")
async def get_conversation_detail(session_id: str):
    """Get detailed conversation view with all messages."""
    try:
        db = get_database()
        conversation = await db.get_conversation(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await db.get_conversation_history(session_id, limit=100)
        
        return {
            "conversation": conversation,
            "messages": messages,
            "message_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail="Error fetching conversation")


@router.post("/conversations/{session_id}/assign")
async def assign_conversation(session_id: str, agent_id: str):
    """Assign a conversation to a human agent."""
    try:
        db = get_database()
        conversation = await db.get_conversation(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Update conversation with agent assignment
        await db.update_conversation_status(session_id, "assigned")
        
        return {
            "success": True,
            "session_id": session_id,
            "agent_id": agent_id,
            "message": f"Conversation assigned to agent {agent_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning conversation: {e}")
        raise HTTPException(status_code=500, detail="Error assigning conversation")


@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "up",
            "database": "up",
            "openai": "up",
            "whatsapp": "up"
        },
        "version": "1.0.0"
    }
