"""Main FastAPI application module with database authentication and Prometheus metrics"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import time

from routers import processes, schedules, metrics, websocket
from routers.auth_db import router as auth_router
from prometheus_metrics import metrics_endpoint, api_requests, api_request_duration
from middleware.auth_db import verify_token, initialize_admin_user
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
    logger.info("Initializing admin user...")
    initialize_admin_user()
    yield
    # Shutdown
    logger.info("Shutting down SentinelZero API")


app = FastAPI(
    title="SentinelZero API",
    description="REST API for SentinelZero Process Management Service with DB Auth and Prometheus Metrics",
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

# Middleware to track API metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track API request metrics for Prometheus"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Track request metrics
    duration = time.time() - start_time
    
    # Record metrics
    api_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=str(response.status_code)
    ).inc()
    
    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
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


@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    """Expose metrics for Prometheus scraping"""
    return await metrics_endpoint()


@app.get("/api/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SentinelZero API",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SentinelZero API",
        "version": "1.0.0",
        "features": [
            "Database-backed authentication",
            "Process management",
            "Schedule management",
            "Prometheus metrics",
            "WebSocket real-time updates",
            "Docker support"
        ],
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/api/health"
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