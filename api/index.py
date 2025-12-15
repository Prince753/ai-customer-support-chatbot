"""
Vercel Serverless Function Entry Point

This module wraps the FastAPI application for Vercel serverless deployment
using Mangum as the ASGI adapter.
"""

import os
import sys
import traceback

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Track initialization errors
init_error = None
init_traceback = None

try:
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
    router_status = {"loaded": False, "error": None, "traceback": None}

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
                "response": f"AI service initialization failed: {router_status.get('error', 'Unknown error')}",
                "session_id": request.session_id or "fallback",
                "status": "error",
                "error_detail": router_status.get("error", "Unknown error"),
                "traceback": router_status.get("traceback", "")[:500]
            }


    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "name": "AI Customer Support Chatbot API",
            "version": "1.0.0",
            "status": "running",
            "router_loaded": router_status["loaded"],
            "router_error": router_status.get("error"),
            "docs": "/docs",
            "health": "/health"
        }


    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy" if router_status["loaded"] else "degraded",
            "router_loaded": router_status["loaded"],
            "router_error": router_status.get("error"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0"
        }


    @app.get("/api/v1/health")
    async def api_health():
        """API health check."""
        return {
            "status": "healthy" if router_status["loaded"] else "degraded",
            "router_loaded": router_status["loaded"]
        }


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
        
        # Try to load settings
        settings_info = {}
        try:
            from app.config import get_settings
            settings = get_settings()
            settings_info = {
                "is_configured": settings.is_configured(),
                "missing_vars": settings.get_missing_vars()
            }
        except Exception as e:
            settings_info = {"error": str(e)}
        
        return {
            "router_status": router_status,
            "environment_variables": env_status,
            "settings_info": settings_info,
            "backend_path": backend_path,
            "python_path": sys.path[:5],
            "hint": "All environment variables must be set in Vercel Dashboard -> Settings -> Environment Variables"
        }


    # Error handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )


    # Mangum handler for Vercel
    handler = Mangum(app, lifespan="off")

except Exception as e:
    # Catch any error during initialization and create a minimal app
    init_error = str(e)
    init_traceback = traceback.format_exc()
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from mangum import Mangum
    
    app = FastAPI(title="Error App")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def error_root():
        return {
            "status": "initialization_failed",
            "error": init_error,
            "traceback": init_traceback
        }
    
    @app.get("/health")
    async def error_health():
        return {
            "status": "initialization_failed",
            "error": init_error
        }
    
    @app.get("/api/v1/health")
    async def error_api_health():
        return {
            "status": "initialization_failed",
            "error": init_error
        }
    
    @app.get("/api/v1/debug")
    async def error_debug():
        return {
            "status": "initialization_failed",
            "error": init_error,
            "traceback": init_traceback,
            "backend_path": backend_path,
            "env_vars": {
                "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
                "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
                "SUPABASE_KEY": bool(os.getenv("SUPABASE_KEY")),
            }
        }
    
    from pydantic import BaseModel
    from typing import Optional
    
    class FallbackChatRequest(BaseModel):
        message: str
        session_id: Optional[str] = None
    
    @app.post("/api/v1/chat/")
    async def error_chat(request: FallbackChatRequest):
        return {
            "response": f"Service initialization failed: {init_error}",
            "session_id": request.session_id or "error",
            "status": "error"
        }
    
    handler = Mangum(app, lifespan="off")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
