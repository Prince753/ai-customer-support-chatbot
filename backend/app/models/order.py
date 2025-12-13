"""
Order-related Pydantic models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class OrderItem(BaseModel):
    """Individual order item model."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    image_url: Optional[str] = None


class ShippingAddress(BaseModel):
    """Shipping address model."""
    full_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "India"
    phone: Optional[str] = None


class TrackingInfo(BaseModel):
    """Shipping tracking information."""
    carrier: str
    tracking_number: str
    tracking_url: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    last_update: Optional[str] = None
    current_location: Optional[str] = None


class Order(BaseModel):
    """Complete order model."""
    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str
    status: OrderStatus
    items: List[OrderItem]
    subtotal: float
    shipping_cost: float
    tax: float
    total: float
    payment_method: str
    payment_status: str
    shipping_address: ShippingAddress
    tracking: Optional[TrackingInfo] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "order_id": "ORD-2024-001234",
                "customer_id": "cust_xyz789",
                "status": "shipped",
                "items": [
                    {
                        "product_id": "prod_abc",
                        "product_name": "Wireless Headphones",
                        "quantity": 1,
                        "unit_price": 2999,
                        "total_price": 2999,
                        "image_url": "https://example.com/headphones.jpg"
                    }
                ],
                "subtotal": 2999,
                "shipping_cost": 99,
                "tax": 540,
                "total": 3638,
                "payment_method": "UPI",
                "payment_status": "paid",
                "shipping_address": {
                    "full_name": "John Doe",
                    "address_line1": "123 Main Street",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "postal_code": "400001",
                    "country": "India"
                },
                "tracking": {
                    "carrier": "Delhivery",
                    "tracking_number": "DL1234567890",
                    "tracking_url": "https://delhivery.com/track/DL1234567890",
                    "estimated_delivery": "2024-01-20T18:00:00Z"
                },
                "created_at": "2024-01-15T10:00:00Z",
                "shipped_at": "2024-01-16T14:00:00Z"
            }
        }


class OrderLookupRequest(BaseModel):
    """Request model for order lookup."""
    order_id: str = Field(..., min_length=5, max_length=50, description="Order ID to lookup")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD-2024-001234"
            }
        }


class OrderTrackingResponse(BaseModel):
    """Response model for order tracking."""
    order_id: str
    status: OrderStatus
    status_description: str
    items_count: int
    total: float
    tracking: Optional[TrackingInfo] = None
    timeline: List[dict] = Field(default_factory=list, description="Order status timeline")
    estimated_delivery: Optional[str] = None
    can_cancel: bool = False
    can_return: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD-2024-001234",
                "status": "shipped",
                "status_description": "Your order has been shipped and is on its way!",
                "items_count": 1,
                "total": 3638,
                "tracking": {
                    "carrier": "Delhivery",
                    "tracking_number": "DL1234567890",
                    "tracking_url": "https://delhivery.com/track/DL1234567890"
                },
                "timeline": [
                    {"status": "Order Placed", "timestamp": "2024-01-15T10:00:00Z"},
                    {"status": "Order Confirmed", "timestamp": "2024-01-15T10:05:00Z"},
                    {"status": "Shipped", "timestamp": "2024-01-16T14:00:00Z"}
                ],
                "estimated_delivery": "January 20, 2024",
                "can_cancel": False,
                "can_return": False
            }
        }
