"""
API Routers package.
"""

from .chat import router as chat_router
from .orders import router as orders_router
from .faqs import router as faqs_router
from .admin import router as admin_router
from .whatsapp import router as whatsapp_router

__all__ = [
    "chat_router",
    "orders_router", 
    "faqs_router",
    "admin_router",
    "whatsapp_router",
]
