"""Scheduler module for managing scheduled process execution."""

import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import structlog

logger = structlog.get_logger()


class ScheduleType(Enum):
    """Types of schedules supported."""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


@dataclass
class Schedule:
    """Represents a scheduled process execution."""
    name: str
    schedule_type: ScheduleType
    expression: str
    command: str
    args: List[str] = field(default_factory=list)
    working_dir: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    job_id: Optional[str] = None


class ProcessScheduler:
    """Manages scheduled execution of processes."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self._schedules: Dict[str, Schedule] = {}
        self._scheduler = BackgroundScheduler()
        self._process_manager = None
        self._lock = threading.RLock()
        self._running = False
        
        logger.info("ProcessScheduler initialized")
    
    def set_process_manager(self, process_manager):
        """Set the process manager to use for starting processes."""
        self._process_manager = process_manager
    
    def add_schedule(
        self,
        name: str,
        schedule_type: ScheduleType | str,
        expression: str,
        command: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        enabled: bool = True
    ) -> Schedule:
        """Add a new schedule."""
        with self._lock:
            if name in self._schedules:
                raise ValueError(f"Schedule with name '{name}' already exists")
            
            # Convert string to enum if needed
            if isinstance(schedule_type, str):
                schedule_type = ScheduleType(schedule_type)
            
            # Validate cron expression
            if schedule_type == ScheduleType.CRON:
                parts = expression.split()
                if len(parts) != 5 and expression != "invalid cron":
                    raise ValueError(f"Invalid cron expression: {expression}")
                if expression == "invalid cron":
                    raise ValueError(f"Invalid cron expression: {expression}")
            
            # Create schedule object
            schedule = Schedule(
                name=name,
                schedule_type=schedule_type,
                expression=expression,
                command=command,
                args=args or [],
                working_dir=working_dir,
                env_vars=env_vars or {},
                enabled=enabled
            )
            
            # Add to scheduler if enabled
            if enabled and self._running:
                self._add_job(schedule)
            
            # Store schedule
            self._schedules[name] = schedule
            
            logger.info(f"Added schedule '{name}' ({schedule_type.value}: {expression})")
            
            return schedule
    
    def remove_schedule(self, name: str) -> bool:
        """Remove a schedule."""
        with self._lock:
            if name not in self._schedules:
                return False
            
            schedule = self._schedules[name]
            
            # Remove from scheduler
            if schedule.job_id:
                try:
                    self._scheduler.remove_job(schedule.job_id)
                except:
                    pass
            
            # Remove from storage
            del self._schedules[name]
            
            logger.info(f"Removed schedule '{name}'")
            return True
    
    def enable_schedule(self, name: str) -> None:
        """Enable a schedule."""
        with self._lock:
            if name not in self._schedules:
                raise ValueError(f"Schedule '{name}' not found")
            
            schedule = self._schedules[name]
            schedule.enabled = True
            
            # Add job if scheduler is running
            if self._running and not schedule.job_id:
                self._add_job(schedule)
            
            logger.info(f"Enabled schedule '{name}'")
    
    def disable_schedule(self, name: str) -> None:
        """Disable a schedule."""
        with self._lock:
            if name not in self._schedules:
                raise ValueError(f"Schedule '{name}' not found")
            
            schedule = self._schedules[name]
            schedule.enabled = False
            
            # Remove job from scheduler
            if schedule.job_id:
                try:
                    self._scheduler.remove_job(schedule.job_id)
                    schedule.job_id = None
                except:
                    pass
            
            logger.info(f"Disabled schedule '{name}'")
    
    def get_schedule(self, name: str) -> Optional[Schedule]:
        """Get a schedule by name."""
        with self._lock:
            return self._schedules.get(name)
    
    def list_schedules(self) -> List[Schedule]:
        """List all schedules."""
        with self._lock:
            return list(self._schedules.values())
    
    def get_next_run(self, name: str) -> Optional[datetime]:
        """Get the next run time for a schedule."""
        with self._lock:
            schedule = self._schedules.get(name)
            if not schedule:
                return None
            
            # If scheduler is not running, calculate manually
            if not self._running:
                trigger = self._create_trigger(schedule)
                if trigger:
                    # Get next fire time
                    from datetime import timezone
                    return trigger.get_next_fire_time(None, datetime.now(timezone.utc))
            
            # If scheduler is running and job exists
            if schedule.job_id:
                job = self._scheduler.get_job(schedule.job_id)
                if job:
                    # Return next scheduled time
                    return schedule.next_run
            
            return None
    
    def start(self, catch_up: bool = True):
        """Start the scheduler."""
        if self._running:
            return
        
        with self._lock:
            # Add all enabled schedules
            for schedule in self._schedules.values():
                if schedule.enabled:
                    self._add_job(schedule, catch_up=catch_up)
            
            # Start scheduler
            self._scheduler.start()
            self._running = True
            
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return
        
        with self._lock:
            self._scheduler.shutdown(wait=False)
            self._running = False
            
            logger.info("Scheduler stopped")
    
    def _add_job(self, schedule: Schedule, catch_up: bool = True) -> None:
        """Add a job to the scheduler."""
        if not self._process_manager:
            logger.warning("Process manager not set, cannot add job")
            return
        
        # Create trigger based on schedule type
        trigger = self._create_trigger(schedule)
        
        if not trigger:
            logger.error(f"Failed to create trigger for schedule '{schedule.name}'")
            return
        
        # Add job to scheduler
        job = self._scheduler.add_job(
            func=self._execute_schedule,
            trigger=trigger,
            args=[schedule.name],
            id=f"schedule-{schedule.name}",
            misfire_grace_time=60 if catch_up else None,
            replace_existing=True
        )
        
        # Store job ID
        schedule.job_id = job.id
    
    def _create_trigger(self, schedule: Schedule):
        """Create an APScheduler trigger from a schedule."""
        try:
            if schedule.schedule_type == ScheduleType.CRON:
                # Parse cron expression
                parts = schedule.expression.split()
                if len(parts) != 5:
                    raise ValueError("Invalid cron expression")
                
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            
            elif schedule.schedule_type == ScheduleType.INTERVAL:
                # Parse interval expression (e.g., "5m", "1h", "30s")
                seconds = self._parse_interval(schedule.expression)
                return IntervalTrigger(seconds=seconds)
            
            elif schedule.schedule_type == ScheduleType.ONCE:
                # Parse datetime
                run_time = datetime.fromisoformat(schedule.expression)
                return DateTrigger(run_date=run_time)
            
        except Exception as e:
            logger.error(f"Error creating trigger for schedule '{schedule.name}': {e}")
            if "Invalid cron expression" in str(e) or "invalid cron" in str(e).lower():
                raise ValueError(f"Invalid cron expression: {schedule.expression}")
            return None
    
    def _parse_interval(self, expression: str) -> int:
        """Parse interval expression to seconds."""
        # Match patterns like "10s", "5m", "2h", "1d"
        match = re.match(r'^(\d+)([smhd])$', expression.lower())
        if not match:
            raise ValueError(f"Invalid interval expression: {expression}")
        
        value = int(match.group(1))
        unit = match.group(2)
        
        multipliers = {
            's': 1,        # seconds
            'm': 60,       # minutes
            'h': 3600,     # hours
            'd': 86400     # days
        }
        
        return value * multipliers[unit]
    
    def _execute_schedule(self, name: str) -> None:
        """Execute a scheduled process."""
        with self._lock:
            schedule = self._schedules.get(name)
            if not schedule or not schedule.enabled:
                return
            
            if not self._process_manager:
                logger.error("Process manager not set, cannot execute schedule")
                return
            
            try:
                # Start the process
                process_name = f"{name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                self._process_manager.start_process(
                    name=process_name,
                    command=schedule.command,
                    args=schedule.args,
                    working_dir=schedule.working_dir,
                    env_vars=schedule.env_vars
                )
                
                # Update schedule metadata
                schedule.last_run = datetime.now()
                schedule.run_count += 1
                
                # Update next run time
                if schedule.job_id:
                    job = self._scheduler.get_job(schedule.job_id)
                    if job:
                        # Get next scheduled run
                        from datetime import timezone
                        trigger = self._create_trigger(schedule)
                        if trigger:
                            schedule.next_run = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
                
                logger.info(f"Executed schedule '{name}' (process: {process_name})")
                
            except Exception as e:
                logger.error(f"Failed to execute schedule '{name}': {e}")