"""
Order tracking API endpoints.
"""

from fastapi import APIRouter, HTTPException
import logging

from ..models.order import OrderLookupRequest, OrderTrackingResponse
from ..services import get_order_service

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger(__name__)


@router.get("/{order_id}", response_model=OrderTrackingResponse)
async def get_order_status(order_id: str):
    """
    Get order status and tracking information.
    
    Provide an order ID to retrieve:
    - Current order status
    - Tracking information
    - Estimated delivery date
    - Order timeline
    """
    try:
        order_service = get_order_service()
        order_info = await order_service.get_order_status(order_id)
        
        if not order_info:
            raise HTTPException(
                status_code=404,
                detail=f"Order {order_id} not found. Please check the order ID and try again."
            )
        
        return OrderTrackingResponse(**order_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching order details")


@router.post("/lookup", response_model=OrderTrackingResponse)
async def lookup_order(request: OrderLookupRequest):
    """
    Lookup order by ID (POST method for forms).
    """
    return await get_order_status(request.order_id)


@router.get("/customer/{customer_id}")
async def get_customer_orders(customer_id: str, limit: int = 5):
    """
    Get recent orders for a customer.
    
    Requires customer authentication in production.
    """
    try:
        order_service = get_order_service()
        orders = await order_service.get_customer_orders(customer_id, limit)
        
        return {
            "customer_id": customer_id,
            "orders": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Error fetching customer orders: {e}")
        raise HTTPException(status_code=500, detail="Error fetching orders")
