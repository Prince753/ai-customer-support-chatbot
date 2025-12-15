"""
Vercel Serverless Function Entry Point

This module wraps the FastAPI application for Vercel serverless deployment
using Mangum as the ASGI adapter.
"""

import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Customer Support Chatbot API",
    description="AI-powered customer support chatbot with GPT-4, RAG, and WhatsApp integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track router loading status
router_status = {"loaded": False, "error": None}

# Import and include routers
try:
    from app.routers import chat_router, orders_router, faqs_router, admin_router, whatsapp_router
    
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(faqs_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(whatsapp_router, prefix="/api/v1")
    
    router_status["loaded"] = True
    logger.info("All routers loaded successfully")
except Exception as e:
    import traceback
    error_detail = traceback.format_exc()
    router_status["error"] = str(e)
    router_status["traceback"] = error_detail
    logger.error(f"Error importing routers: {e}\n{error_detail}")
    
    # Add fallback chat endpoint
    from pydantic import BaseModel
    from typing import Optional
    
    class FallbackChatRequest(BaseModel):
        message: str
        session_id: Optional[str] = None
    
    @app.post("/api/v1/chat/")
    async def fallback_chat(request: FallbackChatRequest):
        """Fallback chat endpoint when full routers fail to load."""
        return {
            "response": "I'm sorry, but the AI service is currently unavailable. Please try again later or contact support directly.",
            "session_id": request.session_id or "fallback",
            "status": "error",
            "error_detail": router_status.get("error", "Unknown error"),
            "message": "Backend services failed to initialize. Check environment variables: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY"
        }


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AI Customer Support Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }


@app.get("/api/v1/health")
async def api_health():
    """API health check."""
    return {"status": "healthy"}


@app.get("/api/v1/debug")
async def debug_info():
    """Debug endpoint to check configuration status."""
    # Check environment variables (only show if they exist, not their values)
    env_status = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "not set"),
    }
    
    return {
        "router_status": router_status,
        "environment_variables": env_status,
        "python_path": os.environ.get("PYTHONPATH", "not set"),
        "hint": "If router_status shows an error, check the environment variables above. All should be True."
    }


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") == "true" else "An error occurred"
        }
    )


# Mangum handler for Vercel
handler = Mangum(app, lifespan="off")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
