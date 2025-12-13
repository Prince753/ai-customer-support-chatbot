"""
WhatsApp webhook API endpoints.
"""

from fastapi import APIRouter, HTTPException, Request, Query
import logging

from ..services import get_whatsapp_service, get_openai_service, get_rag_service
from ..database import get_database

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    WhatsApp webhook verification endpoint.
    Called by Meta when setting up the webhook.
    """
    whatsapp = get_whatsapp_service()
    
    result = whatsapp.verify_webhook(hub_mode, hub_token, hub_challenge)
    
    if result:
        return int(result)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle incoming WhatsApp messages.
    
    This endpoint receives:
    - Text messages
    - Button replies
    - List selections
    """
    try:
        payload = await request.json()
        logger.debug(f"WhatsApp webhook: {payload}")
        
        whatsapp = get_whatsapp_service()
        openai = get_openai_service()
        rag = get_rag_service()
        db = get_database()
        
        # Parse the incoming message
        message_data = whatsapp.parse_webhook_message(payload)
        
        if not message_data:
            return {"status": "no_message"}
        
        user_phone = message_data.get("from")
        user_name = message_data.get("from_name", "Customer")
        message_text = message_data.get("text")
        message_id = message_data.get("message_id")
        
        if not message_text:
            # Handle non-text messages
            await whatsapp.send_message(
                to=user_phone,
                message="I can only process text messages at the moment. Please type your question."
            )
            return {"status": "non_text_handled"}
        
        # Mark message as read
        await whatsapp.mark_as_read(message_id)
        
        # Create/get session for this phone number
        session_id = f"wa_{user_phone}"
        
        conversation = await db.get_conversation(session_id)
        if not conversation:
            await db.create_conversation(
                session_id=session_id,
                channel="whatsapp",
                metadata={"phone": user_phone, "name": user_name}
            )
            # Send welcome message
            welcome = whatsapp.get_welcome_message()
            await whatsapp.send_message(to=user_phone, message=welcome)
        
        # Get conversation history
        history = await db.get_conversation_history(session_id, limit=10)
        
        # Save user message
        await db.save_message(
            session_id=session_id,
            role="user",
            content=message_text,
            metadata={"whatsapp_message_id": message_id}
        )
        
        # Get RAG context
        context = await rag.get_relevant_context(message_text)
        
        # Generate AI response
        result = await openai.generate_response(
            user_message=message_text,
            conversation_history=[
                {"role": m["role"], "content": m["content"]}
                for m in history
            ],
            context=context
        )
        
        response_text = result["response"]
        
        # Save assistant response
        await db.save_message(
            session_id=session_id,
            role="assistant",
            content=response_text
        )
        
        # Check if escalation needed
        if result.get("escalate"):
            await whatsapp.send_message(
                to=user_phone,
                message=response_text
            )
            await whatsapp.send_interactive_buttons(
                to=user_phone,
                body="Would you like to speak with a human agent?",
                buttons=[
                    {"id": "yes_agent", "title": "Yes, Connect Me"},
                    {"id": "no_agent", "title": "No, I'm Fine"}
                ]
            )
            await db.update_conversation_status(session_id, "escalated")
        else:
            # Send response
            await whatsapp.send_message(
                to=user_phone,
                message=response_text
            )
        
        return {"status": "success", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/send")
async def send_message(to: str, message: str):
    """
    Send a message to a WhatsApp number.
    For admin/agent use.
    """
    try:
        whatsapp = get_whatsapp_service()
        result = await whatsapp.send_message(to=to, message=message)
        
        if result:
            return {"success": True, "message_id": result.get("messages", [{}])[0].get("id")}
        
        raise HTTPException(status_code=500, detail="Failed to send message")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
