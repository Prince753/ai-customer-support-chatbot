"""
Chat-related Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConversationStatus(str, Enum):
    """Conversation status enumeration."""
    ACTIVE = "active"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ChatMessage(BaseModel):
    """Individual chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What's the status of my order ORD-12345?",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {}
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    customer_id: Optional[str] = Field(None, description="Customer ID if authenticated")
    channel: str = Field(default="web", description="Communication channel: 'web', 'whatsapp'")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I want to return my order",
                "session_id": "sess_abc123",
                "customer_id": "cust_xyz789",
                "channel": "web",
                "metadata": {"page": "order-history"}
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI assistant response")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE)
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Response confidence score")
    sources: Optional[List[str]] = Field(default_factory=list, description="RAG source documents used")
    suggested_actions: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, 
        description="Suggested quick actions for the user"
    )
    escalate: bool = Field(default=False, description="Whether to escalate to human agent")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'd be happy to help with your return! Could you please provide your order ID?",
                "session_id": "sess_abc123",
                "status": "active",
                "confidence": 0.92,
                "sources": ["return_policy.pdf"],
                "suggested_actions": [
                    {"label": "View Return Policy", "action": "show_policy"},
                    {"label": "Track Order", "action": "track_order"}
                ],
                "escalate": False,
                "metadata": {}
            }
        }


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    session_id: str
    messages: List[ChatMessage]
    status: ConversationStatus
    channel: str
    customer_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "messages": [
                    {"role": "user", "content": "Hello", "timestamp": "2024-01-15T10:30:00Z"},
                    {"role": "assistant", "content": "Hi! How can I help you today?", "timestamp": "2024-01-15T10:30:01Z"}
                ],
                "status": "active",
                "channel": "web",
                "customer_id": "cust_xyz789",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:01Z"
            }
        }


class FeedbackRequest(BaseModel):
    """Request model for message feedback."""
    session_id: str = Field(..., description="Session ID")
    message_id: str = Field(..., description="Message ID to rate")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=500, description="Optional feedback text")


class EscalationRequest(BaseModel):
    """Request model for conversation escalation."""
    session_id: str = Field(..., description="Session ID")
    reason: Optional[str] = Field(None, description="Reason for escalation")
    priority: str = Field(default="normal", description="Priority: 'low', 'normal', 'high', 'urgent'")
