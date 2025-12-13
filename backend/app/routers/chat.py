"""
Chat API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
import logging

from ..models.chat import ChatRequest, ChatResponse, ConversationStatus
from ..services import get_openai_service, get_rag_service, get_order_service
from ..database import get_database

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI chatbot and receive a response.
    
    This endpoint handles:
    - Natural language understanding
    - Order status lookups
    - FAQ matching
    - RAG-based knowledge retrieval
    - Conversation memory
    """
    try:
        db = get_database()
        openai_service = get_openai_service()
        rag_service = get_rag_service()
        order_service = get_order_service()
        
        # Generate or use existing session ID
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
        
        # Create or get conversation
        conversation = await db.get_conversation(session_id)
        if not conversation:
            await db.create_conversation(
                session_id=session_id,
                channel=request.channel,
                customer_id=request.customer_id,
                metadata=request.metadata
            )
        
        # Get conversation history
        history = await db.get_conversation_history(session_id, limit=10)
        
        # Save user message
        await db.save_message(
            session_id=session_id,
            role="user",
            content=request.message,
            metadata=request.metadata
        )
        
        # Check for order lookup intent
        order_context = ""
        order_id = _extract_order_id(request.message)
        if order_id:
            order_info = await order_service.get_order_status(order_id)
            if order_info:
                order_context = _format_order_context(order_info)
        
        # Get RAG context
        rag_context = await rag_service.get_relevant_context(request.message)
        
        # Combine contexts
        full_context = "\n\n".join(filter(None, [order_context, rag_context]))
        
        # Generate AI response
        result = await openai_service.generate_response(
            user_message=request.message,
            conversation_history=[
                {"role": m["role"], "content": m["content"]} 
                for m in history
            ],
            context=full_context
        )
        
        response_text = result["response"]
        should_escalate = result.get("escalate", False)
        
        # Save assistant response
        await db.save_message(
            session_id=session_id,
            role="assistant",
            content=response_text,
            metadata={"tokens_used": result.get("tokens_used", 0)}
        )
        
        # Update status if escalating
        status = ConversationStatus.ACTIVE
        if should_escalate:
            status = ConversationStatus.ESCALATED
            await db.update_conversation_status(session_id, "escalated")
        
        # Generate suggested actions
        suggested_actions = _generate_suggested_actions(request.message)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            status=status,
            confidence=0.9,
            sources=["knowledge_base"] if rag_context else [],
            suggested_actions=suggested_actions,
            escalate=should_escalate,
            metadata={"tokens_used": result.get("tokens_used", 0)}
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 20):
    """Get conversation history for a session."""
    try:
        db = get_database()
        messages = await db.get_conversation_history(session_id, limit)
        conversation = await db.get_conversation(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "session_id": session_id,
            "status": conversation.get("status", "unknown"),
            "channel": conversation.get("channel", "web"),
            "messages": messages,
            "created_at": conversation.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalate/{session_id}")
async def escalate_conversation(session_id: str, reason: Optional[str] = None):
    """Escalate a conversation to human support."""
    try:
        db = get_database()
        conversation = await db.get_conversation(session_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.update_conversation_status(session_id, "escalated")
        
        # Add system message about escalation
        await db.save_message(
            session_id=session_id,
            role="system",
            content=f"Conversation escalated to human agent. Reason: {reason or 'Customer request'}",
            metadata={"escalation_reason": reason}
        )
        
        return {
            "success": True,
            "message": "Conversation has been escalated to a human agent",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{session_id}")
async def close_conversation(session_id: str):
    """Close a conversation."""
    try:
        db = get_database()
        await db.update_conversation_status(session_id, "closed")
        
        return {
            "success": True,
            "message": "Conversation closed",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_order_id(message: str) -> Optional[str]:
    """Extract order ID from message."""
    import re
    patterns = [
        r'ORD[-_]?\d{4,}[-_]?\d*',
        r'order\s*#?\s*(\d{6,})',
        r'#(\d{6,})'
    ]
    
    message_upper = message.upper()
    for pattern in patterns:
        match = re.search(pattern, message_upper, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None


def _format_order_context(order_info: dict) -> str:
    """Format order info as context for AI."""
    return f"""
ORDER INFORMATION:
- Order ID: {order_info.get('order_id')}
- Status: {order_info.get('status')} - {order_info.get('status_description')}
- Items: {order_info.get('items_count')} item(s)
- Total: ₹{order_info.get('total')}
- Estimated Delivery: {order_info.get('estimated_delivery') or 'N/A'}
- Can Cancel: {'Yes' if order_info.get('can_cancel') else 'No'}
- Can Return: {'Yes' if order_info.get('can_return') else 'No'}
"""


def _generate_suggested_actions(message: str) -> list:
    """Generate contextual suggested actions."""
    actions = []
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['order', 'track', 'status']):
        actions.append({"label": "Track Another Order", "action": "track_order"})
    
    if any(word in message_lower for word in ['return', 'exchange', 'refund']):
        actions.append({"label": "View Return Policy", "action": "show_return_policy"})
    
    if any(word in message_lower for word in ['ship', 'deliver', 'when']):
        actions.append({"label": "Shipping Info", "action": "show_shipping_info"})
    
    if not actions:
        actions = [
            {"label": "Track Order", "action": "track_order"},
            {"label": "FAQs", "action": "show_faqs"}
        ]
    
    return actions[:3]
