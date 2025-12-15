"""
Database connection and management using Supabase.
Provides async database operations for the chatbot application.
"""

from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """Supabase database client wrapper."""
    
    _instance: Optional['Database'] = None
    _client: Optional[Client] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Lazy initialization - don't connect until actually needed
        pass
    
    def _ensure_connected(self):
        """Ensure database connection is established."""
        if self._client is None:
            settings = get_settings()
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise Exception("Database not configured: SUPABASE_URL and SUPABASE_KEY required")
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            self._initialized = True
            logger.info("Supabase client initialized")
    
    @property
    def client(self) -> Client:
        """Get the Supabase client."""
        self._ensure_connected()
        return self._client
    
    # ==================== Conversation Operations ====================
    
    async def create_conversation(
        self,
        session_id: str,
        channel: str = "web",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create a new conversation session."""
        try:
            data = {
                "session_id": session_id,
                "channel": channel,
                "customer_id": customer_id,
                "metadata": metadata or {},
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            result = self._client.table("conversations").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get conversation by session ID."""
        try:
            result = self._client.table("conversations")\
                .select("*")\
                .eq("session_id", session_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching conversation: {e}")
            return None
    
    async def update_conversation_status(
        self,
        session_id: str,
        status: str
    ) -> bool:
        """Update conversation status (active, escalated, closed)."""
        try:
            self._client.table("conversations")\
                .update({"status": status, "updated_at": datetime.utcnow().isoformat()})\
                .eq("session_id", session_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating conversation status: {e}")
            return False
    
    # ==================== Message Operations ====================
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Save a chat message."""
        try:
            data = {
                "session_id": session_id,
                "role": role,  # 'user', 'assistant', 'system'
                "content": content,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            result = self._client.table("messages").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent messages for a conversation."""
        try:
            result = self._client.table("messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            # Return in chronological order
            return list(reversed(result.data)) if result.data else []
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []
    
    # ==================== FAQ Operations ====================
    
    async def get_faqs(self, category: Optional[str] = None) -> List[Dict]:
        """Get all FAQs, optionally filtered by category."""
        try:
            query = self._client.table("faqs").select("*").eq("is_active", True)
            if category:
                query = query.eq("category", category)
            result = query.order("priority", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching FAQs: {e}")
            return []
    
    async def create_faq(
        self,
        question: str,
        answer: str,
        category: str,
        keywords: List[str] = None,
        priority: int = 0
    ) -> Dict:
        """Create a new FAQ entry."""
        try:
            data = {
                "question": question,
                "answer": answer,
                "category": category,
                "keywords": keywords or [],
                "priority": priority,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
            result = self._client.table("faqs").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating FAQ: {e}")
            raise
    
    async def update_faq(self, faq_id: str, updates: Dict) -> bool:
        """Update an existing FAQ."""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            self._client.table("faqs")\
                .update(updates)\
                .eq("id", faq_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating FAQ: {e}")
            return False
    
    async def delete_faq(self, faq_id: str) -> bool:
        """Soft delete an FAQ (set is_active to False)."""
        return await self.update_faq(faq_id, {"is_active": False})
    
    # ==================== Order Operations ====================
    
    async def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order details by order ID."""
        try:
            result = self._client.table("orders")\
                .select("*")\
                .eq("order_id", order_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            return None
    
    async def get_customer_orders(
        self,
        customer_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get recent orders for a customer."""
        try:
            result = self._client.table("orders")\
                .select("*")\
                .eq("customer_id", customer_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching customer orders: {e}")
            return []
    
    # ==================== Analytics Operations ====================
    
    async def get_chat_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get chat analytics for the admin dashboard."""
        try:
            # Total conversations
            conv_query = self._client.table("conversations").select("*", count="exact")
            if start_date:
                conv_query = conv_query.gte("created_at", start_date)
            if end_date:
                conv_query = conv_query.lte("created_at", end_date)
            conv_result = conv_query.execute()
            
            # Total messages
            msg_query = self._client.table("messages").select("*", count="exact")
            if start_date:
                msg_query = msg_query.gte("created_at", start_date)
            if end_date:
                msg_query = msg_query.lte("created_at", end_date)
            msg_result = msg_query.execute()
            
            # Escalated conversations
            esc_result = self._client.table("conversations")\
                .select("*", count="exact")\
                .eq("status", "escalated")\
                .execute()
            
            return {
                "total_conversations": conv_result.count or 0,
                "total_messages": msg_result.count or 0,
                "escalated_conversations": esc_result.count or 0,
                "avg_messages_per_conversation": (
                    (msg_result.count or 0) / (conv_result.count or 1)
                )
            }
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {}
    
    async def get_recent_conversations(
        self,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get recent conversations for admin dashboard."""
        try:
            query = self._client.table("conversations")\
                .select("*, messages(count)")\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching recent conversations: {e}")
            return []
    
    # ==================== Document Embeddings ====================
    
    async def store_embedding(
        self,
        content: str,
        embedding: List[float],
        metadata: Dict
    ) -> Dict:
        """Store document embedding for RAG."""
        try:
            data = {
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat()
            }
            result = self._client.table("document_embeddings").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            raise
    
    async def search_similar_documents(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """Search for similar documents using vector similarity."""
        try:
            # Using Supabase's pgvector extension
            result = self._client.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []



# Use lru_cache for lazy singleton instead of module-level instantiation
from functools import lru_cache

@lru_cache()
def get_database() -> Database:
    """Get the database singleton instance (lazy loaded)."""
    return Database()
