"""
OpenAI service for chat completions and embeddings.
"""

import openai
from typing import List, Dict, Optional
import logging
from functools import lru_cache

from ..config import get_settings, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        self._client = None
        self._initialized = False
        self.model = None
        self.embedding_model = None
        self.max_tokens = None
        self.temperature = None
    
    def _ensure_initialized(self):
        """Ensure the OpenAI client is initialized."""
        if not self._initialized:
            settings = get_settings()
            if not settings.OPENAI_API_KEY:
                raise Exception("OpenAI not configured: OPENAI_API_KEY required")
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
            self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
            self.max_tokens = settings.OPENAI_MAX_TOKENS
            self.temperature = settings.OPENAI_TEMPERATURE
            self._initialized = True
            logger.info(f"OpenAI service initialized with model: {self.model}")
    
    @property
    def client(self):
        """Get the OpenAI client."""
        self._ensure_initialized()
        return self._client
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        context: str = "",
        system_prompt: str = None
    ) -> Dict:
        """
        Generate a chat response using OpenAI.
        
        Args:
            user_message: The user's current message
            conversation_history: Previous messages in the conversation
            context: RAG context from knowledge base
            system_prompt: Custom system prompt (optional)
        
        Returns:
            Dict with response text and metadata
        """
        try:
            # Ensure the service is initialized
            self._ensure_initialized()
            
            # Build messages array
            messages = []
            
            # System prompt with context
            final_system_prompt = (system_prompt or SYSTEM_PROMPT).format(
                context=context or "No additional context available.",
                history=self._format_history(conversation_history)
            )
            messages.append({"role": "system", "content": final_system_prompt})
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            assistant_message = response.choices[0].message.content
            
            # Analyze for escalation signals
            should_escalate = self._check_escalation(user_message, assistant_message)
            
            return {
                "response": assistant_message,
                "model": self.model,
                "tokens_used": response.usage.total_tokens,
                "escalate": should_escalate,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise Exception("Service is busy. Please try again in a moment.")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception("AI service temporarily unavailable.")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for system prompt."""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history[-5:]:  # Last 5 messages
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")[:200]  # Truncate
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _check_escalation(self, user_msg: str, assistant_msg: str) -> bool:
        """Check if conversation should be escalated."""
        escalation_keywords = [
            "speak to human", "talk to agent", "real person",
            "manager", "supervisor", "complaint", "lawsuit",
            "frustrated", "angry", "unacceptable", "ridiculous"
        ]
        
        user_lower = user_msg.lower()
        for keyword in escalation_keywords:
            if keyword in user_lower:
                return True
        
        # Check if bot admits inability
        inability_phrases = [
            "i cannot help", "i'm unable", "beyond my capabilities",
            "need human assistance", "connect you with"
        ]
        
        assistant_lower = assistant_msg.lower()
        for phrase in inability_phrases:
            if phrase in assistant_lower:
                return True
        
        return False


@lru_cache()
def get_openai_service() -> OpenAIService:
    """Get cached OpenAI service instance."""
    return OpenAIService()
