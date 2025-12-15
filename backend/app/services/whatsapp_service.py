"""
WhatsApp Business API integration service.
"""

import httpx
from typing import Optional, Dict, List
import logging
from functools import lru_cache

from ..config import get_settings, WHATSAPP_TEMPLATES

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for WhatsApp Business API integration."""
    
    def __init__(self):
        self._initialized = False
        self.token = None
        self.phone_id = None
        self.api_version = "v18.0"
        self.verify_token = "chatbot_verify_token"
        self.base_url = None
        self.enabled = False
    
    def _ensure_initialized(self):
        """Lazy initialization of dependencies."""
        if not self._initialized:
            settings = get_settings()
            self.token = settings.WHATSAPP_TOKEN
            self.phone_id = settings.WHATSAPP_PHONE_ID
            self.api_version = settings.WHATSAPP_API_VERSION
            self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
            self.base_url = f"https://graph.facebook.com/{self.api_version}"
            self.enabled = bool(self.token and self.phone_id)
            self._initialized = True
            
            if self.enabled:
                logger.info("WhatsApp service initialized")
            else:
                logger.warning("WhatsApp service disabled - missing credentials")
    
    async def send_message(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> Optional[Dict]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to: Recipient phone number (with country code)
            message: Message text
            preview_url: Whether to show URL previews
        
        Returns:
            API response or None on failure
        """
        self._ensure_initialized()
        if not self.enabled:
            logger.warning("WhatsApp not configured, message not sent")
            return None
        
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": preview_url,
                    "body": message
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Message sent to {to[:6]}***")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return None
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en",
        components: List[Dict] = None
    ) -> Optional[Dict]:
        """Send a pre-approved template message."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language},
                    "components": components or []
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            return None
    
    async def send_interactive_buttons(
        self,
        to: str,
        body: str,
        buttons: List[Dict],
        header: str = None,
        footer: str = None
    ) -> Optional[Dict]:
        """Send interactive message with buttons."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            interactive = {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                        for b in buttons[:3]
                    ]
                }
            }
            
            if header:
                interactive["header"] = {"type": "text", "text": header}
            if footer:
                interactive["footer"] = {"text": footer}
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": interactive
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            return None
    
    async def send_list(
        self,
        to: str,
        body: str,
        button_text: str,
        sections: List[Dict]
    ) -> Optional[Dict]:
        """Send interactive list message."""
        if not self.enabled:
            return None
        
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {"text": body},
                    "action": {
                        "button": button_text,
                        "sections": sections
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error sending list message: {e}")
            return None
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/{self.phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook subscription."""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("WhatsApp webhook verified")
            return challenge
        logger.warning("WhatsApp webhook verification failed")
        return None
    
    def parse_webhook_message(self, payload: Dict) -> Optional[Dict]:
        """Parse incoming webhook message."""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            contact = value.get("contacts", [{}])[0]
            
            return {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "from_name": contact.get("profile", {}).get("name"),
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
                "text": message.get("text", {}).get("body") if message.get("type") == "text" else None,
                "button_reply": message.get("interactive", {}).get("button_reply") if message.get("type") == "interactive" else None
            }
            
        except Exception as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    def get_welcome_message(self) -> str:
        """Get welcome message template."""
        return WHATSAPP_TEMPLATES.get("welcome", "Hello! How can I help?")


@lru_cache()
def get_whatsapp_service() -> WhatsAppService:
    """Get cached WhatsApp service instance."""
    return WhatsAppService()
