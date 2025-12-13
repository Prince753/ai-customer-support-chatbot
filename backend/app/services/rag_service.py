"""
RAG (Retrieval-Augmented Generation) service for knowledge base queries.
"""

import os
from typing import List, Dict, Optional
import logging
from functools import lru_cache
import hashlib

from ..config import get_settings
from ..database import get_database
from .openai_service import get_openai_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based document retrieval and context generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db = get_database()
        self.openai = get_openai_service()
        self.chunk_size = self.settings.RAG_CHUNK_SIZE
        self.chunk_overlap = self.settings.RAG_CHUNK_OVERLAP
        self.top_k = self.settings.RAG_TOP_K
        logger.info("RAG service initialized")
    
    async def get_relevant_context(
        self,
        query: str,
        top_k: int = None
    ) -> str:
        """
        Retrieve relevant context from knowledge base for a query.
        
        Args:
            query: User's question/message
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Concatenated context string from relevant documents
        """
        try:
            k = top_k or self.top_k
            
            # Generate query embedding
            query_embedding = await self.openai.generate_embedding(query)
            
            # Search for similar documents
            results = await self.db.search_similar_documents(
                query_embedding=query_embedding,
                limit=k,
                threshold=0.7
            )
            
            if not results:
                logger.debug(f"No relevant documents found for: {query[:50]}...")
                return ""
            
            # Format context
            context_parts = []
            for i, doc in enumerate(results, 1):
                source = doc.get("metadata", {}).get("source", "Unknown")
                content = doc.get("content", "")
                context_parts.append(f"[Source {i}: {source}]\n{content}")
            
            context = "\n\n---\n\n".join(context_parts)
            logger.debug(f"Found {len(results)} relevant documents")
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    async def index_document(
        self,
        content: str,
        metadata: Dict
    ) -> int:
        """
        Index a document by chunking and storing embeddings.
        
        Args:
            content: Document text content
            metadata: Document metadata (source, type, etc.)
        
        Returns:
            Number of chunks indexed
        """
        try:
            # Split into chunks
            chunks = self._split_into_chunks(content)
            
            if not chunks:
                logger.warning("No chunks generated from document")
                return 0
            
            # Generate embeddings for all chunks
            embeddings = await self.openai.generate_embeddings_batch(chunks)
            
            # Store each chunk with its embedding
            indexed = 0
            for chunk, embedding in zip(chunks, embeddings):
                chunk_metadata = {
                    **metadata,
                    "chunk_hash": hashlib.md5(chunk.encode()).hexdigest()
                }
                await self.db.store_embedding(
                    content=chunk,
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                indexed += 1
            
            logger.info(f"Indexed {indexed} chunks from {metadata.get('source', 'unknown')}")
            return indexed
            
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise
    
    async def index_directory(self, directory_path: str) -> Dict:
        """
        Index all documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
        
        Returns:
            Summary of indexed documents
        """
        summary = {
            "total_files": 0,
            "indexed_files": 0,
            "total_chunks": 0,
            "errors": []
        }
        
        supported_extensions = {'.txt', '.md', '.pdf', '.json'}
        
        try:
            for root, _, files in os.walk(directory_path):
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in supported_extensions:
                        continue
                    
                    summary["total_files"] += 1
                    filepath = os.path.join(root, filename)
                    
                    try:
                        content = self._read_file(filepath)
                        if content:
                            chunks = await self.index_document(
                                content=content,
                                metadata={
                                    "source": filename,
                                    "path": filepath,
                                    "type": ext[1:]
                                }
                            )
                            summary["indexed_files"] += 1
                            summary["total_chunks"] += chunks
                    except Exception as e:
                        summary["errors"].append(f"{filename}: {str(e)}")
            
            logger.info(f"Directory indexing complete: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error indexing directory: {e}")
            raise
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence end
                for sep in ['. ', '.\n', '? ', '?\n', '! ', '!\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start < 0:
                start = end
        
        return chunks
    
    def _read_file(self, filepath: str) -> Optional[str]:
        """Read file content based on extension."""
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext in ['.txt', '.md']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.json':
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, indent=2)
            elif ext == '.pdf':
                # Requires pypdf
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(filepath)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except ImportError:
                    logger.warning("pypdf not installed, skipping PDF")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None


@lru_cache()
def get_rag_service() -> RAGService:
    """Get cached RAG service instance."""
    return RAGService()
