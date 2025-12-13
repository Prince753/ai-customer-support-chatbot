"""
Order service for order tracking and management.
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
import random
from functools import lru_cache

from ..database import get_database
from ..models.order import OrderStatus

logger = logging.getLogger(__name__)


class OrderService:
    """Service for order-related operations."""
    
    def __init__(self):
        self.db = get_database()
        logger.info("Order service initialized")
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get order status and tracking information.
        
        Args:
            order_id: The order ID to lookup
        
        Returns:
            Order details with tracking info, or None if not found
        """
        try:
            # Try database first
            order = await self.db.get_order(order_id)
            
            if order:
                return self._format_order_response(order)
            
            # For demo: generate mock order if starts with valid prefix
            if order_id.upper().startswith(("ORD-", "ORD")):
                return self._generate_mock_order(order_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None
    
    async def get_customer_orders(
        self,
        customer_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get recent orders for a customer."""
        try:
            orders = await self.db.get_customer_orders(customer_id, limit)
            return [self._format_order_response(o) for o in orders]
        except Exception as e:
            logger.error(f"Error fetching customer orders: {e}")
            return []
    
    def _format_order_response(self, order: Dict) -> Dict:
        """Format order data for response."""
        status = order.get("status", "unknown")
        
        return {
            "order_id": order.get("order_id"),
            "status": status,
            "status_description": self._get_status_description(status),
            "items_count": len(order.get("items", [])),
            "items": order.get("items", []),
            "total": order.get("total", 0),
            "tracking": order.get("tracking"),
            "timeline": self._generate_timeline(order),
            "estimated_delivery": self._get_estimated_delivery(order),
            "can_cancel": status in ["pending", "confirmed"],
            "can_return": status == "delivered",
            "created_at": order.get("created_at"),
            "shipped_at": order.get("shipped_at"),
            "delivered_at": order.get("delivered_at")
        }
    
    def _generate_mock_order(self, order_id: str) -> Dict:
        """Generate mock order data for demonstration."""
        # Use order_id to seed random for consistent results
        seed = sum(ord(c) for c in order_id)
        random.seed(seed)
        
        statuses = [
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED
        ]
        status = random.choice(statuses)
        
        products = [
            {"name": "Wireless Bluetooth Headphones", "price": 2999},
            {"name": "Smart Watch Pro", "price": 4999},
            {"name": "Portable Power Bank 20000mAh", "price": 1299},
            {"name": "USB-C Hub 7-in-1", "price": 1899},
            {"name": "Mechanical Keyboard RGB", "price": 3499}
        ]
        
        product = random.choice(products)
        quantity = random.randint(1, 2)
        
        created = datetime.now() - timedelta(days=random.randint(2, 7))
        shipped = created + timedelta(days=1) if status != OrderStatus.PROCESSING else None
        
        carriers = ["Delhivery", "BlueDart", "DTDC", "Ecom Express"]
        carrier = random.choice(carriers)
        tracking_num = f"{carrier[:2].upper()}{random.randint(1000000000, 9999999999)}"
        
        order = {
            "order_id": order_id.upper(),
            "status": status.value,
            "items": [{
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": product["price"] * quantity
            }],
            "subtotal": product["price"] * quantity,
            "shipping_cost": 99 if product["price"] * quantity < 500 else 0,
            "tax": int(product["price"] * quantity * 0.18),
            "total": int(product["price"] * quantity * 1.18) + (99 if product["price"] * quantity < 500 else 0),
            "created_at": created.isoformat(),
            "shipped_at": shipped.isoformat() if shipped else None,
            "tracking": {
                "carrier": carrier,
                "tracking_number": tracking_num,
                "tracking_url": f"https://{carrier.lower()}.com/track/{tracking_num}",
                "current_location": random.choice(["Mumbai Hub", "Delhi Hub", "Local Facility", "Out for Delivery"])
            } if shipped else None
        }
        
        return self._format_order_response(order)
    
    def _get_status_description(self, status: str) -> str:
        """Get human-readable status description."""
        descriptions = {
            "pending": "Your order is being processed and will be confirmed shortly.",
            "confirmed": "Your order has been confirmed! We're preparing it for shipment.",
            "processing": "Your order is being packed and will be shipped soon.",
            "shipped": "Great news! Your order has been shipped and is on its way!",
            "out_for_delivery": "Your order is out for delivery today! 🚚",
            "delivered": "Your order has been delivered. Enjoy! 🎉",
            "cancelled": "This order has been cancelled.",
            "returned": "This order has been returned.",
            "refunded": "This order has been refunded to your original payment method."
        }
        return descriptions.get(status, "Status unknown. Please contact support.")
    
    def _generate_timeline(self, order: Dict) -> List[Dict]:
        """Generate order status timeline."""
        timeline = []
        created = order.get("created_at")
        
        if created:
            timeline.append({
                "status": "Order Placed",
                "timestamp": created,
                "description": "Your order was successfully placed"
            })
        
        status = order.get("status", "")
        
        if status not in ["pending"]:
            timeline.append({
                "status": "Order Confirmed",
                "timestamp": created,
                "description": "Order confirmed and payment verified"
            })
        
        shipped_at = order.get("shipped_at")
        if shipped_at:
            timeline.append({
                "status": "Shipped",
                "timestamp": shipped_at,
                "description": "Your order has been handed to the courier"
            })
        
        if status == "out_for_delivery":
            timeline.append({
                "status": "Out for Delivery",
                "timestamp": datetime.now().isoformat(),
                "description": "Package is with the delivery agent"
            })
        
        delivered_at = order.get("delivered_at")
        if delivered_at:
            timeline.append({
                "status": "Delivered",
                "timestamp": delivered_at,
                "description": "Package was delivered successfully"
            })
        
        return timeline
    
    def _get_estimated_delivery(self, order: Dict) -> Optional[str]:
        """Calculate estimated delivery date."""
        status = order.get("status", "")
        
        if status == "delivered":
            return None
        
        shipped_at = order.get("shipped_at")
        if shipped_at:
            if isinstance(shipped_at, str):
                shipped_at = datetime.fromisoformat(shipped_at.replace('Z', '+00:00'))
            est = shipped_at + timedelta(days=random.randint(2, 5))
            return est.strftime("%B %d, %Y")
        
        created = order.get("created_at")
        if created:
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace('Z', '+00:00'))
            est = created + timedelta(days=random.randint(5, 7))
            return est.strftime("%B %d, %Y")
        
        return None


@lru_cache()
def get_order_service() -> OrderService:
    """Get cached order service instance."""
    return OrderService()
