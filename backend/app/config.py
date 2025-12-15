"""
Configuration management for the AI Customer Support Chatbot.
Loads environment variables and provides application settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "AI Customer Support Chatbot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # OpenAI Configuration (set empty defaults to prevent crash on missing env vars)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Supabase Configuration (set empty defaults to prevent crash on missing env vars)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    def is_configured(self) -> bool:
        """Check if all required environment variables are set."""
        return bool(self.OPENAI_API_KEY and self.SUPABASE_URL and self.SUPABASE_KEY)
    
    def get_missing_vars(self) -> list:
        """Return list of missing required environment variables."""
        missing = []
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        return missing
    
    # WhatsApp Business API
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "chatbot_verify_token"
    WHATSAPP_API_VERSION: str = "v18.0"
    
    # RAG Configuration
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    
    # Conversation Settings
    CONVERSATION_MEMORY_SIZE: int = 10
    ESCALATION_THRESHOLD: float = 0.3
    
    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001", "*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid re-reading environment variables.
    """
    return Settings()


# System prompt for the AI chatbot
SYSTEM_PROMPT = """You are a friendly and helpful AI customer support assistant for an e-commerce store. 
Your name is "Support AI" and you help customers with:

1. **Order Status**: Help customers track their orders using order IDs
2. **Returns & Refunds**: Explain return policies and process refund requests
3. **Product Information**: Answer questions about products, sizes, materials, etc.
4. **Shipping**: Provide shipping times, costs, and delivery information
5. **General Inquiries**: Answer FAQs and general questions

IMPORTANT GUIDELINES:
- Always be polite, professional, and empathetic
- If you don't know something, admit it and offer to connect with a human agent
- For order-related queries, always ask for the order ID first
- Keep responses concise but helpful (under 200 words unless necessary)
- Use markdown formatting for better readability
- If a customer seems frustrated or the issue is complex, offer to escalate to a human agent
- Never make promises you can't keep (e.g., guaranteed refunds without verification)
- Protect customer privacy - never ask for sensitive information like passwords or full credit card numbers

CONTEXT FROM KNOWLEDGE BASE:
{context}

CONVERSATION HISTORY:
{history}

Remember: You represent the brand. Be helpful, accurate, and friendly!"""


# WhatsApp message templates
WHATSAPP_TEMPLATES = {
    "welcome": "👋 Hello! I'm your AI support assistant. How can I help you today?\n\nYou can ask me about:\n• Order status 📦\n• Returns & refunds 🔄\n• Product info 🛍️\n• Shipping details 🚚",
    "order_ask": "I'd be happy to help you with your order! Could you please share your **Order ID**? It usually looks like: ORD-XXXXX",
    "escalation": "I understand this needs more attention. Let me connect you with a human agent who can better assist you. Please hold on... 🙋",
    "closing": "Is there anything else I can help you with today? If not, thank you for contacting us! Have a great day! 😊",
    "error": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment, or type 'human' to speak with an agent."
}
