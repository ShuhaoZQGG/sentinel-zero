"""Main FastAPI application module"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from routers import processes, schedules, metrics, auth, websocket
from middleware.auth import verify_token
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting SentinelZero API")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down SentinelZero API")


app = FastAPI(
    title="SentinelZero API",
    description="REST API for SentinelZero Process Management Service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    processes.router,
    prefix="/api/processes",
    tags=["Processes"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    schedules.router,
    prefix="/api/schedules",
    tags=["Schedules"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    metrics.router,
    prefix="/api/metrics",
    tags=["Metrics"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)


@app.get("/api/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SentinelZero API",
        "version": "1.0.0"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "path": str(request.url)
            }
        }
    )