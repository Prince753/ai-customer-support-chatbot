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

# Import and include routers
try:
    from app.routers import chat_router, orders_router, faqs_router, admin_router, whatsapp_router
    
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(faqs_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(whatsapp_router, prefix="/api/v1")
    
    logger.info("All routers loaded successfully")
except ImportError as e:
    logger.error(f"Error importing routers: {e}")
    # Fallback minimal API
    pass


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
