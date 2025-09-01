"""Main FastAPI application for SentinelZero."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from .middleware.logging import LoggingMiddleware
from . import deps

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting SentinelZero API")
    
    # Initialize managers
    deps.initialize_managers()
    
    process_manager = deps.get_process_manager()
    scheduler = deps.get_scheduler()
    config_manager = deps.get_config_manager()
    
    # Load configuration
    try:
        config = config_manager.load_config()
        logger.info("Configuration loaded", 
                   processes=len(config.processes),
                   schedules=len(config.schedules))
    except Exception as e:
        logger.error("Failed to load configuration", error=str(e))
        config = config_manager.get_config()  # Get default config
    
    # Start auto-start processes
    for process_config in config.processes:
        if process_config.auto_start:
            try:
                process_manager.start_process(process_config.name)
                logger.info("Started auto-start process", name=process_config.name)
            except Exception as e:
                logger.error("Failed to start process", name=process_config.name, error=str(e))
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SentinelZero API")
    
    # Stop scheduler
    scheduler.stop()
    
    # Stop all processes
    for process in process_manager.get_all_processes():
        try:
            process_manager.stop_process(process.name)
        except Exception as e:
            logger.error("Error stopping process", name=process.name, error=str(e))


app = FastAPI(
    title="SentinelZero API",
    description="REST API for SentinelZero process management service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)

# Import routers after app is created to avoid circular imports
from .routers import processes, schedules, system, config, restart_policies

# Include routers
app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])
app.include_router(restart_policies.router, prefix="/api/restart-policies", tags=["restart-policies"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SentinelZero API",
        "version": "1.0.0",
        "status": "running"
    }