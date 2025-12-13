"""
Admin dashboard Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    total_conversations: int = 0
    total_messages: int = 0
    active_conversations: int = 0
    escalated_conversations: int = 0
    avg_response_time_seconds: float = 0.0
    resolution_rate: float = 0.0
    customer_satisfaction: float = 0.0
    messages_today: int = 0
    conversations_today: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_conversations": 1250,
                "total_messages": 8750,
                "active_conversations": 15,
                "escalated_conversations": 3,
                "avg_response_time_seconds": 2.5,
                "resolution_rate": 0.87,
                "customer_satisfaction": 4.6,
                "messages_today": 145,
                "conversations_today": 32
            }
        }


class ConversationSummary(BaseModel):
    """Summary of a conversation for admin view."""
    session_id: str
    customer_id: Optional[str] = None
    channel: str
    status: str
    message_count: int
    first_message: str
    last_message: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    sentiment: Optional[str] = None  # positive, neutral, negative
    topics: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "customer_id": "cust_xyz789",
                "channel": "web",
                "status": "closed",
                "message_count": 8,
                "first_message": "I need help with my order",
                "last_message": "Thank you for your help!",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:15:00Z",
                "duration_minutes": 15,
                "sentiment": "positive",
                "topics": ["order_status", "shipping"]
            }
        }


class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoint."""
    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    stats: DashboardStats
    conversations_by_channel: Dict[str, int] = Field(default_factory=dict)
    conversations_by_status: Dict[str, int] = Field(default_factory=dict)
    top_topics: List[Dict[str, Any]] = Field(default_factory=list)
    hourly_distribution: List[Dict[str, Any]] = Field(default_factory=list)
    daily_trend: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": "weekly",
                "start_date": "2024-01-08T00:00:00Z",
                "end_date": "2024-01-15T00:00:00Z",
                "stats": {
                    "total_conversations": 320,
                    "total_messages": 2240
                },
                "conversations_by_channel": {
                    "web": 200,
                    "whatsapp": 120
                },
                "conversations_by_status": {
                    "closed": 280,
                    "escalated": 25,
                    "active": 15
                },
                "top_topics": [
                    {"topic": "order_status", "count": 95},
                    {"topic": "returns", "count": 72},
                    {"topic": "shipping", "count": 58}
                ]
            }
        }


class AgentPerformance(BaseModel):
    """Human agent performance metrics."""
    agent_id: str
    agent_name: str
    conversations_handled: int
    avg_resolution_time_minutes: float
    customer_satisfaction: float
    escalations_received: int
    
    
class BotPerformance(BaseModel):
    """Bot performance metrics."""
    total_queries: int
    successful_resolutions: int
    escalation_rate: float
    avg_confidence_score: float
    most_common_intents: List[Dict[str, Any]]
    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Topics where bot frequently fails or escalates"
    )


class SystemHealth(BaseModel):
    """System health status."""
    status: str  # healthy, degraded, down
    api_latency_ms: float
    database_status: str
    openai_status: str
    whatsapp_status: str
    last_check: datetime
    uptime_percentage: float
    error_rate: float
