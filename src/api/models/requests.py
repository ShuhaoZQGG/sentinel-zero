"""Request models for API endpoints."""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class ProcessCreateRequest(BaseModel):
    """Request model for creating a process."""
    
    name: str = Field(..., min_length=1, description="Unique process name")
    command: str = Field(..., min_length=1, description="Command to execute")
    working_directory: Optional[str] = Field(None, description="Working directory")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    auto_start: bool = Field(False, description="Start automatically on service startup")
    enabled: bool = Field(True, description="Whether the process is enabled")


class ScheduleCreateRequest(BaseModel):
    """Request model for creating a schedule."""
    
    name: str = Field(..., min_length=1, description="Unique schedule name")
    process_name: str = Field(..., description="Name of the process to schedule")
    schedule_type: str = Field(..., description="Type: 'cron' or 'interval'")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    interval_seconds: Optional[int] = Field(None, gt=0, description="Interval in seconds")
    enabled: bool = Field(True, description="Whether the schedule is enabled")


class RestartPolicyCreateRequest(BaseModel):
    """Request model for creating a restart policy."""
    
    process_name: str = Field(..., description="Process name")
    max_retries: int = Field(3, ge=0, description="Maximum restart attempts")
    retry_delay_seconds: int = Field(1, ge=0, description="Delay between restarts")
    exponential_backoff: bool = Field(False, description="Use exponential backoff")
    restart_on_failure: bool = Field(True, description="Restart on non-zero exit")
    restart_on_success: bool = Field(False, description="Restart on zero exit")
    success_codes: List[int] = Field([0], description="Success exit codes")
    failure_codes: List[int] = Field([], description="Failure exit codes to trigger restart")


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    
    global_config: Optional[Dict] = Field(None, description="Global configuration")
    processes: Optional[List[Dict]] = Field(None, description="Process configurations")
    schedules: Optional[List[Dict]] = Field(None, description="Schedule configurations")
    restart_policies: Optional[List[Dict]] = Field(None, description="Restart policies")