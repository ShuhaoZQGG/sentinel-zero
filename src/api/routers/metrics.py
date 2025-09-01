"""Metrics and logging router for API"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.api.models.schemas import ProcessMetrics, LogEntry
from src.models.database import get_db
from src.models.process import Process
from src.models.metrics import Metric
from src.models.log import ProcessLog

router = APIRouter()


@router.get("/processes/{process_id}/metrics", response_model=List[ProcessMetrics])
async def get_process_metrics(
    process_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get metrics for a specific process"""
    # Verify process exists
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    # Build query
    query = db.query(Metric).filter(Metric.process_id == process_id)
    
    # Apply time filters
    if start_time:
        query = query.filter(Metric.timestamp >= start_time)
    else:
        # Default to last 24 hours
        query = query.filter(
            Metric.timestamp >= datetime.now() - timedelta(hours=24)
        )
    
    if end_time:
        query = query.filter(Metric.timestamp <= end_time)
    
    # Order by timestamp descending and limit
    metrics = query.order_by(Metric.timestamp.desc()).limit(limit).all()
    
    # Calculate uptime if process is running
    result = []
    for metric in metrics:
        uptime_seconds = None
        if process.last_started_at:
            uptime_seconds = int(
                (metric.timestamp - process.last_started_at).total_seconds()
            )
        
        result.append(ProcessMetrics(
            process_id=metric.process_id,
            cpu_percent=metric.cpu_percent,
            memory_mb=metric.memory_mb,
            timestamp=metric.timestamp,
            uptime_seconds=uptime_seconds
        ))
    
    return result


@router.get("/processes/{process_id}/logs", response_model=List[LogEntry])
async def get_process_logs(
    process_id: int,
    log_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get logs for a specific process"""
    # Verify process exists
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    # Build query
    query = db.query(ProcessLog).filter(ProcessLog.process_id == process_id)
    
    # Apply filters
    if log_type:
        query = query.filter(ProcessLog.log_type == log_type)
    
    if since:
        query = query.filter(ProcessLog.timestamp >= since)
    else:
        # Default to last 24 hours
        query = query.filter(
            ProcessLog.timestamp >= datetime.now() - timedelta(hours=24)
        )
    
    if search:
        query = query.filter(ProcessLog.message.contains(search))
    
    # Order by timestamp descending and limit
    logs = query.order_by(ProcessLog.timestamp.desc()).limit(limit).all()
    
    return [
        LogEntry(
            process_id=log.process_id,
            log_type=log.log_type,
            message=log.message,
            timestamp=log.timestamp
        )
        for log in logs
    ]


@router.get("/system", response_model=dict)
async def get_system_metrics():
    """Get overall system metrics"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total / (1024 * 1024),  # MB
            "available": psutil.virtual_memory().available / (1024 * 1024),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total / (1024 * 1024 * 1024),  # GB
            "free": psutil.disk_usage('/').free / (1024 * 1024 * 1024),
            "percent": psutil.disk_usage('/').percent
        },
        "boot_time": datetime.fromtimestamp(psutil.boot_time()),
        "timestamp": datetime.now()
    }


@router.delete("/processes/{process_id}/logs", status_code=status.HTTP_204_NO_CONTENT)
async def clear_process_logs(
    process_id: int,
    before: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Clear logs for a specific process"""
    # Verify process exists
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    # Build delete query
    query = db.query(ProcessLog).filter(ProcessLog.process_id == process_id)
    
    if before:
        query = query.filter(ProcessLog.timestamp < before)
    
    # Delete logs
    query.delete()
    db.commit()


@router.delete("/processes/{process_id}/metrics", status_code=status.HTTP_204_NO_CONTENT)
async def clear_process_metrics(
    process_id: int,
    before: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Clear metrics for a specific process"""
    # Verify process exists
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    # Build delete query
    query = db.query(Metric).filter(Metric.process_id == process_id)
    
    if before:
        query = query.filter(Metric.timestamp < before)
    
    # Delete metrics
    query.delete()
    db.commit()