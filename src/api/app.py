"""FastAPI application for SentinelZero REST API."""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.process_manager import ProcessManager
from core.restart_policy import RestartPolicyManager
from core.scheduler import ProcessScheduler, ScheduleType
from models.base import get_session, init_db
from models.models import Process as ProcessModel


# Pydantic models for API
class ProcessCreate(BaseModel):
    """Request model for creating a process."""
    name: str = Field(..., min_length=1, max_length=100)
    command: str = Field(..., min_length=1)
    args: Optional[List[str]] = None
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    group: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response model for process information."""
    id: int
    name: str
    command: str
    args: Optional[List[str]] = None
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    group: Optional[str] = None
    status: str
    pid: Optional[int] = None
    restart_count: int = 0


class ProcessMetrics(BaseModel):
    """Response model for process metrics."""
    cpu_percent: float
    memory_mb: float
    threads: int
    status: str


class ScheduleCreate(BaseModel):
    """Request model for creating a schedule."""
    process_name: str
    schedule_type: str = Field(..., pattern="^(cron|interval|once)$")
    expression: str
    enabled: bool = True


class ScheduleResponse(BaseModel):
    """Response model for schedule information."""
    id: int
    process_id: int
    process_name: str
    schedule_type: str
    expression: str
    enabled: bool
    next_run: Optional[str] = None
    last_run: Optional[str] = None


class RestartPolicyCreate(BaseModel):
    """Request model for creating a restart policy."""
    process_name: str
    policy_type: str = Field(default="standard")
    max_retries: int = Field(default=3, ge=0, le=100)
    retry_delay: float = Field(default=5.0, ge=0)
    backoff_multiplier: float = Field(default=1.5, ge=1.0, le=10.0)
    restart_on_codes: Optional[List[int]] = None


class RestartPolicyResponse(BaseModel):
    """Response model for restart policy information."""
    process_id: int
    process_name: str
    policy_type: str
    max_retries: int
    retry_delay: float
    backoff_multiplier: float
    restart_on_codes: Optional[List[int]] = None


class LogEntry(BaseModel):
    """Response model for log entries."""
    timestamp: str
    level: str
    message: str
    process_name: Optional[str] = None


# Global instances
process_manager: Optional[ProcessManager] = None
scheduler: Optional[ProcessScheduler] = None
policy_manager: Optional[RestartPolicyManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global process_manager, scheduler, policy_manager
    
    # Initialize database
    init_db()
    
    # Initialize managers
    process_manager = ProcessManager()
    scheduler = ProcessScheduler()
    policy_manager = RestartPolicyManager()
    
    # Connect scheduler to process manager
    scheduler.set_process_manager(process_manager)
    
    # Start scheduler
    scheduler.start()
    
    yield
    
    # Cleanup
    scheduler.stop()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="SentinelZero API",
        description="Process monitoring and management service",
        version="0.1.0",
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
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Check if the service is healthy."""
        return {"status": "healthy", "service": "SentinelZero"}
    
    # Process endpoints
    @app.post("/processes", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED)
    async def create_process(process: ProcessCreate):
        """Create a new process."""
        try:
            with get_session() as session:
                # Check if process already exists
                existing = session.query(ProcessModel).filter_by(name=process.name).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Process '{process.name}' already exists"
                    )
                
                # Create process
                db_process = ProcessModel(
                    name=process.name,
                    command=process.command,
                    args=' '.join(process.args) if process.args else None,
                    working_dir=process.working_dir,
                    env_vars=process.env_vars,
                    group=process.group,
                    status='stopped'
                )
                session.add(db_process)
                session.commit()
                session.refresh(db_process)
                
                return ProcessResponse(
                    id=db_process.id,
                    name=db_process.name,
                    command=db_process.command,
                    args=db_process.args.split() if db_process.args else None,
                    working_dir=db_process.working_dir,
                    env_vars=db_process.env_vars,
                    group=db_process.group,
                    status=db_process.status,
                    pid=db_process.pid,
                    restart_count=db_process.restart_count
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/processes", response_model=List[ProcessResponse])
    async def list_processes(group: Optional[str] = None):
        """List all processes."""
        try:
            with get_session() as session:
                query = session.query(ProcessModel)
                if group:
                    query = query.filter_by(group=group)
                
                processes = query.all()
                return [
                    ProcessResponse(
                        id=p.id,
                        name=p.name,
                        command=p.command,
                        args=p.args.split() if p.args else None,
                        working_dir=p.working_dir,
                        env_vars=p.env_vars,
                        group=p.group,
                        status=p.status,
                        pid=p.pid,
                        restart_count=p.restart_count
                    )
                    for p in processes
                ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/processes/{name}", response_model=ProcessResponse)
    async def get_process(name: str):
        """Get a specific process by name."""
        try:
            with get_session() as session:
                process = session.query(ProcessModel).filter_by(name=name).first()
                if not process:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Process '{name}' not found"
                    )
                
                return ProcessResponse(
                    id=process.id,
                    name=process.name,
                    command=process.command,
                    args=process.args.split() if process.args else None,
                    working_dir=process.working_dir,
                    env_vars=process.env_vars,
                    group=process.group,
                    status=process.status,
                    pid=process.pid,
                    restart_count=process.restart_count
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.post("/processes/{name}/start")
    async def start_process(name: str):
        """Start a process."""
        try:
            info = process_manager.start_process(name)
            return {"message": f"Process '{name}' started", "pid": info.get('pid')}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.post("/processes/{name}/stop")
    async def stop_process(name: str, force: bool = False):
        """Stop a process."""
        try:
            process_manager.stop_process(name, force=force)
            return {"message": f"Process '{name}' stopped"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.post("/processes/{name}/restart")
    async def restart_process(name: str):
        """Restart a process."""
        try:
            process_manager.restart_process(name)
            return {"message": f"Process '{name}' restarted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/processes/{name}/metrics", response_model=ProcessMetrics)
    async def get_process_metrics(name: str):
        """Get process metrics."""
        try:
            metrics = process_manager.get_process_metrics(name)
            if not metrics:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No metrics available for process '{name}'"
                )
            
            return ProcessMetrics(**metrics)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/processes/{name}/logs", response_model=List[LogEntry])
    async def get_process_logs(name: str, limit: int = 100):
        """Get process logs."""
        try:
            logs = process_manager.get_process_logs(name, limit=limit)
            return [
                LogEntry(
                    timestamp=log.get('timestamp', ''),
                    level=log.get('level', 'info'),
                    message=log.get('message', ''),
                    process_name=name
                )
                for log in logs
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.delete("/processes/{name}")
    async def delete_process(name: str):
        """Delete a process."""
        try:
            with get_session() as session:
                process = session.query(ProcessModel).filter_by(name=name).first()
                if not process:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Process '{name}' not found"
                    )
                
                # Stop process if running
                if process.status == 'running':
                    process_manager.stop_process(name, force=True)
                
                # Delete from database
                session.delete(process)
                session.commit()
                
                return {"message": f"Process '{name}' deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Schedule endpoints
    @app.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
    async def create_schedule(schedule: ScheduleCreate):
        """Create a new schedule for a process."""
        try:
            with get_session() as session:
                # Get process
                process = session.query(ProcessModel).filter_by(name=schedule.process_name).first()
                if not process:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Process '{schedule.process_name}' not found"
                    )
                
                # Create schedule
                db_schedule = scheduler.add_schedule(
                    process_id=process.id,
                    schedule_type=schedule.schedule_type,
                    expression=schedule.expression,
                    enabled=schedule.enabled
                )
                
                return ScheduleResponse(
                    id=db_schedule.id,
                    process_id=process.id,
                    process_name=process.name,
                    schedule_type=db_schedule.schedule_type,
                    expression=db_schedule.expression,
                    enabled=db_schedule.enabled,
                    next_run=str(db_schedule.next_run) if db_schedule.next_run else None,
                    last_run=str(db_schedule.last_run) if db_schedule.last_run else None
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/schedules", response_model=List[ScheduleResponse])
    async def list_schedules():
        """List all schedules."""
        try:
            schedules = scheduler.list_schedules()
            result = []
            
            with get_session() as session:
                for schedule in schedules:
                    process = session.query(ProcessModel).filter_by(id=schedule.process_id).first()
                    if process:
                        result.append(ScheduleResponse(
                            id=schedule.id,
                            process_id=schedule.process_id,
                            process_name=process.name,
                            schedule_type=schedule.schedule_type,
                            expression=schedule.expression,
                            enabled=schedule.enabled,
                            next_run=str(schedule.next_run) if schedule.next_run else None,
                            last_run=str(schedule.last_run) if schedule.last_run else None
                        ))
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.delete("/schedules/{schedule_id}")
    async def delete_schedule(schedule_id: int):
        """Delete a schedule."""
        try:
            scheduler.remove_schedule(schedule_id)
            return {"message": f"Schedule {schedule_id} deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Restart policy endpoints
    @app.post("/policies", response_model=RestartPolicyResponse, status_code=status.HTTP_201_CREATED)
    async def create_restart_policy(policy: RestartPolicyCreate):
        """Create a restart policy for a process."""
        try:
            with get_session() as session:
                # Get process
                process = session.query(ProcessModel).filter_by(name=policy.process_name).first()
                if not process:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Process '{policy.process_name}' not found"
                    )
                
                # Create policy
                db_policy = policy_manager.create_custom_policy(
                    process_id=process.id,
                    max_retries=policy.max_retries,
                    retry_delay=policy.retry_delay,
                    backoff_multiplier=policy.backoff_multiplier,
                    restart_on_codes=policy.restart_on_codes
                )
                
                return RestartPolicyResponse(
                    process_id=process.id,
                    process_name=process.name,
                    policy_type=policy.policy_type,
                    max_retries=db_policy.max_retries,
                    retry_delay=db_policy.retry_delay,
                    backoff_multiplier=db_policy.backoff_multiplier,
                    restart_on_codes=db_policy.restart_on_codes
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @app.get("/policies/{process_name}", response_model=RestartPolicyResponse)
    async def get_restart_policy(process_name: str):
        """Get restart policy for a process."""
        try:
            with get_session() as session:
                process = session.query(ProcessModel).filter_by(name=process_name).first()
                if not process:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Process '{process_name}' not found"
                    )
                
                policy = policy_manager.get_policy(process.id)
                if not policy:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No policy found for process '{process_name}'"
                    )
                
                return RestartPolicyResponse(
                    process_id=process.id,
                    process_name=process.name,
                    policy_type=policy.policy_type.value if hasattr(policy.policy_type, 'value') else str(policy.policy_type),
                    max_retries=policy.max_retries,
                    retry_delay=policy.retry_delay,
                    backoff_multiplier=policy.backoff_multiplier,
                    restart_on_codes=policy.restart_on_codes
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    return app


# Create app instance
app = create_app()