"""
Pydantic models for request/response validation.
"""

from .chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationStatus
)
from .faq import (
    FAQ,
    FAQCreate,
    FAQUpdate,
    FAQCategory
)
from .order import (
    Order,
    OrderStatus,
    OrderTrackingResponse
)
from .admin import (
    AnalyticsResponse,
    ConversationSummary,
    DashboardStats
)

__all__ = [
    # Chat models
    "ChatMessage",
    "ChatRequest", 
    "ChatResponse",
    "ConversationHistory",
    "ConversationStatus",
    # FAQ models
    "FAQ",
    "FAQCreate",
    "FAQUpdate",
    "FAQCategory",
    # Order models
    "Order",
    "OrderStatus",
    "OrderTrackingResponse",
    # Admin models
    "AnalyticsResponse",
    "ConversationSummary",
    "DashboardStats",
]
