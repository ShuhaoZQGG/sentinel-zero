"""Schedule management router for API"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from src.api.models.schemas import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse
)
from src.models.database import get_db
from src.models.schedule import Schedule
from src.models.process import Process
from src.core.scheduler import Scheduler

router = APIRouter()


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db)
):
    """Create a new schedule for a process"""
    # Verify process exists
    process = db.query(Process).filter(Process.id == schedule.process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {schedule.process_id} not found"
        )
    
    try:
        # Create schedule in database
        db_schedule = Schedule(
            process_id=schedule.process_id,
            schedule_type=schedule.schedule_type.value,
            schedule_expr=schedule.schedule_expr,
            enabled=schedule.enabled
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        # Add to scheduler if enabled
        if schedule.enabled:
            scheduler = Scheduler(db)
            scheduler.add_schedule(db_schedule.id)
        
        return ScheduleResponse.model_validate(db_schedule)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    process_id: Optional[int] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all schedules with optional filters"""
    query = db.query(Schedule)
    
    if process_id is not None:
        query = query.filter(Schedule.process_id == process_id)
    if enabled is not None:
        query = query.filter(Schedule.enabled == enabled)
    
    schedules = query.all()
    return [ScheduleResponse.model_validate(s) for s in schedules]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Get details of a specific schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    
    return ScheduleResponse.model_validate(schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    update: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Update schedule configuration"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    
    try:
        scheduler = Scheduler(db)
        
        # Remove old schedule from scheduler
        if schedule.enabled:
            scheduler.remove_schedule(schedule_id)
        
        # Update fields
        update_data = update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "schedule_type" and value:
                setattr(schedule, field, value.value)
            else:
                setattr(schedule, field, value)
        
        db.commit()
        db.refresh(schedule)
        
        # Add updated schedule back if enabled
        if schedule.enabled:
            scheduler.add_schedule(schedule_id)
        
        return ScheduleResponse.model_validate(schedule)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Delete a schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    
    try:
        # Remove from scheduler
        if schedule.enabled:
            scheduler = Scheduler(db)
            scheduler.remove_schedule(schedule_id)
        
        # Remove from database
        db.delete(schedule)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@router.post("/{schedule_id}/enable", response_model=ScheduleResponse)
async def enable_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Enable a schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    
    if not schedule.enabled:
        schedule.enabled = True
        db.commit()
        
        # Add to scheduler
        scheduler = Scheduler(db)
        scheduler.add_schedule(schedule_id)
    
    db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)


@router.post("/{schedule_id}/disable", response_model=ScheduleResponse)
async def disable_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """Disable a schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    
    if schedule.enabled:
        schedule.enabled = False
        db.commit()
        
        # Remove from scheduler
        scheduler = Scheduler(db)
        scheduler.remove_schedule(schedule_id)
    
    db.refresh(schedule)
    return ScheduleResponse.model_validate(schedule)