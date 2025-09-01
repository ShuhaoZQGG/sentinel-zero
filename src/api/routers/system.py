"""System status and health API endpoints."""

import time
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
import psutil
import structlog

from src.api.models.responses import (
    SystemStatusResponse,
    HealthResponse,
    LogEntry
)

router = APIRouter()
logger = structlog.get_logger()

# Track service start time
SERVICE_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        from src.api.deps import get_process_manager, get_scheduler
        process_manager = get_process_manager()
        scheduler = get_scheduler()
        
        # Check database
        db_status = "ok"
        try:
            # Simple database check
            from src.models.base import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
        except Exception:
            db_status = "error"
        
        # Check scheduler
        scheduler_status = "ok" if scheduler and scheduler.running else "error"
        
        return HealthResponse(
            status="healthy" if db_status == "ok" and scheduler_status == "ok" else "degraded",
            timestamp=datetime.now(),
            database=db_status,
            scheduler=scheduler_status
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            database="error",
            scheduler="error"
        )


@router.get("/status", response_model=SystemStatusResponse)
async def system_status():
    """Get system status information."""
    try:
        from src.api.deps import get_process_manager, get_scheduler
        
        process_manager = get_process_manager()
        scheduler = get_scheduler()
        
        # Get process stats
        all_processes = process_manager.get_all_processes()
        running_processes = [p for p in all_processes if p.status == "running"]
        
        # Get schedule stats
        all_schedules = scheduler.get_all_schedules()
        active_schedules = [s for s in all_schedules if s.enabled]
        
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Calculate uptime
        uptime_seconds = int(time.time() - SERVICE_START_TIME)
        
        return SystemStatusResponse(
            total_processes=len(all_processes),
            running_processes=len(running_processes),
            total_schedules=len(all_schedules),
            active_schedules=len(active_schedules),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            uptime_seconds=uptime_seconds
        )
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries to return"),
    level: str = Query(None, description="Filter by log level"),
    process_name: str = Query(None, description="Filter by process name")
):
    """Get recent log entries."""
    try:
        logs = get_recent_logs(limit, level, process_name)
        return logs
    except Exception as e:
        logger.error("Failed to get logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def get_recent_logs(limit: int, level: str = None, process_name: str = None) -> List[LogEntry]:
    """Get recent log entries from the log file or database.
    
    This is a placeholder implementation. In production, you would
    read from actual log files or a log aggregation system.
    """
    # Placeholder implementation
    logs = []
    
    # In a real implementation, you would:
    # 1. Read from log files in the configured log directory
    # 2. Parse structured logs
    # 3. Apply filters
    # 4. Return the most recent entries
    
    # For now, return some sample data
    from datetime import datetime, timedelta
    
    sample_messages = [
        ("INFO", "Process started", "web_server"),
        ("INFO", "Schedule executed", "backup_script"),
        ("WARNING", "High memory usage detected", "worker"),
        ("ERROR", "Process crashed", "data_processor"),
        ("INFO", "Process restarted", "data_processor"),
    ]
    
    now = datetime.now()
    for i in range(min(limit, len(sample_messages))):
        level_sample, message, proc = sample_messages[i % len(sample_messages)]
        
        # Apply filters
        if level and level_sample != level.upper():
            continue
        if process_name and proc != process_name:
            continue
        
        logs.append(LogEntry(
            timestamp=now - timedelta(minutes=i * 5),
            level=level_sample,
            message=message,
            process_name=proc
        ))
    
    return logs[:limit]