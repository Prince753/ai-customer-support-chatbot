"""
FAQ-related Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FAQCategory(str, Enum):
    """FAQ category enumeration."""
    ORDERS = "orders"
    SHIPPING = "shipping"
    RETURNS = "returns"
    REFUNDS = "refunds"
    PRODUCTS = "products"
    PAYMENTS = "payments"
    ACCOUNT = "account"
    GENERAL = "general"


class FAQBase(BaseModel):
    """Base FAQ model."""
    question: str = Field(..., min_length=10, max_length=500, description="FAQ question")
    answer: str = Field(..., min_length=10, max_length=5000, description="FAQ answer")
    category: FAQCategory = Field(..., description="FAQ category")
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    priority: int = Field(default=0, ge=0, le=100, description="Display priority")


class FAQCreate(FAQBase):
    """Model for creating a new FAQ."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I return a product?",
                "answer": "To return a product, log in to your account, go to 'My Orders', select the order, and click 'Request Return'. You have 30 days from delivery to initiate a return.",
                "category": "returns",
                "keywords": ["return", "refund", "send back", "exchange"],
                "priority": 10
            }
        }


class FAQUpdate(BaseModel):
    """Model for updating an existing FAQ."""
    question: Optional[str] = Field(None, min_length=10, max_length=500)
    answer: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[FAQCategory] = None
    keywords: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class FAQ(FAQBase):
    """Complete FAQ model with database fields."""
    id: str
    is_active: bool = True
    view_count: int = 0
    helpful_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "faq_123abc",
                "question": "How do I return a product?",
                "answer": "To return a product...",
                "category": "returns",
                "keywords": ["return", "refund"],
                "priority": 10,
                "is_active": True,
                "view_count": 150,
                "helpful_count": 45,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }


class FAQSearchResult(BaseModel):
    """Model for FAQ search results."""
    faqs: List[FAQ]
    total_count: int
    query: str
    category_filter: Optional[FAQCategory] = None
