"""Schedule management API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status
import structlog

from src.api.models.requests import ScheduleCreateRequest
from src.api.models.responses import ScheduleResponse, MessageResponse
from src.api.deps import get_scheduler, get_config_manager
from src.config.config_manager import ScheduleConfig

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules():
    """Get all schedules."""
    try:
        scheduler = get_scheduler()
        schedules = scheduler.get_all_schedules()
        return [
            ScheduleResponse(
                id=s.id,
                name=s.name,
                process_name=s.process_name,
                schedule_type=s.schedule_type,
                cron_expression=s.cron_expression,
                interval_seconds=s.interval_seconds,
                enabled=s.enabled,
                next_run=getattr(s, 'next_run', None),
                last_run=s.last_run
            )
            for s in schedules
        ]
    except Exception as e:
        logger.error("Failed to list schedules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=ScheduleResponse)
async def get_schedule(name: str):
    """Get a specific schedule by name."""
    scheduler = get_scheduler()
    schedule = scheduler.get_schedule(name)
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule '{name}' not found")
    
    return ScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        process_name=schedule.process_name,
        schedule_type=schedule.schedule_type,
        cron_expression=schedule.cron_expression,
        interval_seconds=schedule.interval_seconds,
        enabled=schedule.enabled,
        next_run=getattr(schedule, 'next_run', None),
        last_run=schedule.last_run
    )


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(request: ScheduleCreateRequest):
    """Create a new schedule."""
    try:
        # Create schedule config
        config = ScheduleConfig(
            name=request.name,
            process_name=request.process_name,
            schedule_type=request.schedule_type,
            cron_expression=request.cron_expression,
            interval_seconds=request.interval_seconds,
            enabled=request.enabled
        )
        
        # Add to scheduler
        scheduler = get_scheduler()
        if config.schedule_type == "cron":
            scheduler.add_cron_schedule(
                name=config.name,
                process_name=config.process_name,
                cron_expression=config.cron_expression
            )
        else:
            scheduler.add_interval_schedule(
                name=config.name,
                process_name=config.process_name,
                seconds=config.interval_seconds
            )
        
        # Save to config
        config_manager = get_config_manager()
        config_manager.add_schedule(config)
        config_manager.save_config()
        
        logger.info("Schedule created", name=request.name)
        return MessageResponse(message="Schedule created successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create schedule", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/enable", response_model=MessageResponse)
async def enable_schedule(name: str):
    """Enable a schedule."""
    try:
        scheduler = get_scheduler()
        success = scheduler.enable_schedule(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Schedule '{name}' not found")
        
        # Update config
        config_manager = get_config_manager()
        config = config_manager.get_config()
        for schedule in config.schedules:
            if schedule.name == name:
                schedule.enabled = True
                config_manager.save_config()
                break
        
        logger.info("Schedule enabled", name=name)
        return MessageResponse(message="Schedule enabled successfully")
        
    except Exception as e:
        logger.error("Failed to enable schedule", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/disable", response_model=MessageResponse)
async def disable_schedule(name: str):
    """Disable a schedule."""
    try:
        scheduler = get_scheduler()
        success = scheduler.disable_schedule(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Schedule '{name}' not found")
        
        # Update config
        config_manager = get_config_manager()
        config = config_manager.get_config()
        for schedule in config.schedules:
            if schedule.name == name:
                schedule.enabled = False
                config_manager.save_config()
                break
        
        logger.info("Schedule disabled", name=name)
        return MessageResponse(message="Schedule disabled successfully")
        
    except Exception as e:
        logger.error("Failed to disable schedule", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=MessageResponse)
async def delete_schedule(name: str):
    """Delete a schedule."""
    try:
        scheduler = get_scheduler()
        success = scheduler.remove_schedule(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Schedule '{name}' not found")
        
        # Remove from config
        config_manager = get_config_manager()
        config_manager.remove_schedule(name)
        config_manager.save_config()
        
        logger.info("Schedule deleted", name=name)
        return MessageResponse(message="Schedule deleted successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete schedule", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))