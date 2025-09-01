"""Pydantic schemas for API requests and responses"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProcessStatus(str, Enum):
    """Process status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    STARTING = "starting"
    STOPPING = "stopping"


class ProcessCreate(BaseModel):
    """Schema for creating a new process"""
    name: str = Field(..., min_length=1, max_length=100)
    command: str = Field(..., min_length=1)
    args: Optional[str] = None
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    restart_policy_id: Optional[int] = None
    schedule_id: Optional[int] = None


class ProcessUpdate(BaseModel):
    """Schema for updating a process"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    command: Optional[str] = Field(None, min_length=1)
    args: Optional[str] = None
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    restart_policy_id: Optional[int] = None


class ProcessResponse(BaseModel):
    """Schema for process response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    command: str
    args: Optional[str]
    working_dir: Optional[str]
    env_vars: Optional[Dict[str, str]]
    status: ProcessStatus
    pid: Optional[int]
    created_at: datetime
    updated_at: datetime
    restart_count: int = 0
    last_started_at: Optional[datetime]
    last_stopped_at: Optional[datetime]


class ProcessMetrics(BaseModel):
    """Schema for process metrics"""
    process_id: int
    cpu_percent: float
    memory_mb: float
    timestamp: datetime
    uptime_seconds: Optional[int]


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


class ScheduleCreate(BaseModel):
    """Schema for creating a schedule"""
    process_id: int
    schedule_type: ScheduleType
    schedule_expr: str
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule"""
    schedule_type: Optional[ScheduleType]
    schedule_expr: Optional[str]
    enabled: Optional[bool]


class ScheduleResponse(BaseModel):
    """Schema for schedule response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    process_id: int
    schedule_type: ScheduleType
    schedule_expr: str
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime


class RestartPolicyCreate(BaseModel):
    """Schema for creating a restart policy"""
    name: str = Field(..., min_length=1, max_length=100)
    max_retries: int = Field(3, ge=0, le=100)
    retry_delay: int = Field(5, ge=0)
    backoff_multiplier: float = Field(1.5, ge=1.0, le=10.0)
    restart_on_codes: Optional[List[int]] = None


class RestartPolicyResponse(BaseModel):
    """Schema for restart policy response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    max_retries: int
    retry_delay: int
    backoff_multiplier: float
    restart_on_codes: Optional[List[int]]
    created_at: datetime


class LogEntry(BaseModel):
    """Schema for log entry"""
    process_id: int
    log_type: str
    message: str
    timestamp: datetime


class TokenRequest(BaseModel):
    """Schema for token request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """Schema for creating a user"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class HealthStatus(BaseModel):
    """Schema for health status"""
    status: str
    service: str
    version: str
    uptime_seconds: Optional[int]
    database_connected: bool = True
    scheduler_running: bool = True


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: Dict[str, Any]