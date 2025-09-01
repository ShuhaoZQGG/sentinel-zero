"""Response models for API endpoints."""

from typing import Dict, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProcessResponse(BaseModel):
    """Response model for process information."""
    
    id: Optional[int] = Field(None, description="Process ID in database")
    name: str = Field(..., description="Process name")
    command: str = Field(..., description="Command")
    status: str = Field(..., description="Process status")
    pid: Optional[int] = Field(None, description="System process ID")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    memory_mb: Optional[float] = Field(None, description="Memory usage in MB")
    uptime_seconds: Optional[int] = Field(None, description="Uptime in seconds")
    restart_count: int = Field(0, description="Number of restarts")
    last_started: Optional[datetime] = Field(None, description="Last start time")


class ScheduleResponse(BaseModel):
    """Response model for schedule information."""
    
    id: Optional[int] = Field(None, description="Schedule ID in database")
    name: str = Field(..., description="Schedule name")
    process_name: str = Field(..., description="Process to run")
    schedule_type: str = Field(..., description="Schedule type")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    interval_seconds: Optional[int] = Field(None, description="Interval")
    enabled: bool = Field(..., description="Is enabled")
    next_run: Optional[str] = Field(None, description="Next scheduled run")
    last_run: Optional[datetime] = Field(None, description="Last run time")


class RestartPolicyResponse(BaseModel):
    """Response model for restart policy information."""
    
    process_name: str = Field(..., description="Process name")
    max_retries: int = Field(..., description="Maximum retries")
    retry_delay_seconds: int = Field(..., description="Retry delay")
    exponential_backoff: bool = Field(..., description="Exponential backoff")
    restart_on_failure: bool = Field(..., description="Restart on failure")
    restart_on_success: bool = Field(..., description="Restart on success")
    success_codes: List[int] = Field(..., description="Success codes")
    failure_codes: List[int] = Field(..., description="Failure codes")


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    
    total_processes: int = Field(..., description="Total processes")
    running_processes: int = Field(..., description="Running processes")
    total_schedules: int = Field(..., description="Total schedules")
    active_schedules: int = Field(..., description="Active schedules")
    cpu_percent: float = Field(..., description="System CPU usage")
    memory_percent: float = Field(..., description="System memory usage")
    uptime_seconds: int = Field(..., description="Service uptime")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    database: str = Field("ok", description="Database status")
    scheduler: str = Field("ok", description="Scheduler status")


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str = Field(..., description="Response message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation."""
    
    valid: bool = Field(..., description="Is configuration valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")


class LogEntry(BaseModel):
    """Log entry model."""
    
    timestamp: datetime = Field(..., description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    process_name: Optional[str] = Field(None, description="Related process")