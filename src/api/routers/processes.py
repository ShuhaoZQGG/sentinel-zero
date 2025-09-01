"""Process management router for API"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from src.api.models.schemas import (
    ProcessCreate,
    ProcessUpdate,
    ProcessResponse,
    ProcessStatus
)
from src.models.database import get_db
from src.models.process import Process
from src.core.process_manager import ProcessManager

router = APIRouter()


@router.post("/", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED)
async def create_process(
    process: ProcessCreate,
    db: Session = Depends(get_db)
):
    """Start a new process"""
    try:
        # Check if process with same name exists
        existing = db.query(Process).filter(Process.name == process.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Process with name '{process.name}' already exists"
            )
        
        # Create process in database
        db_process = Process(
            name=process.name,
            command=process.command,
            args=process.args,
            working_dir=process.working_dir,
            env_vars=process.env_vars,
            restart_policy_id=process.restart_policy_id
        )
        db.add(db_process)
        db.commit()
        db.refresh(db_process)
        
        # Start the process
        manager = ProcessManager(db)
        manager.start_process(db_process.id)
        
        # Refresh to get updated status
        db.refresh(db_process)
        
        return ProcessResponse.model_validate(db_process)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create process: {str(e)}"
        )


@router.get("/", response_model=List[ProcessResponse])
async def list_processes(
    status: Optional[ProcessStatus] = None,
    db: Session = Depends(get_db)
):
    """List all processes with optional status filter"""
    query = db.query(Process)
    if status:
        query = query.filter(Process.status == status.value)
    
    processes = query.all()
    return [ProcessResponse.model_validate(p) for p in processes]


@router.get("/{process_id}", response_model=ProcessResponse)
async def get_process(
    process_id: int,
    db: Session = Depends(get_db)
):
    """Get details of a specific process"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    return ProcessResponse.model_validate(process)


@router.put("/{process_id}", response_model=ProcessResponse)
async def update_process(
    process_id: int,
    update: ProcessUpdate,
    db: Session = Depends(get_db)
):
    """Update process configuration"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    # Update fields if provided
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(process, field, value)
    
    db.commit()
    db.refresh(process)
    
    return ProcessResponse.model_validate(process)


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_process(
    process_id: int,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """Stop and remove a process"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    try:
        # Stop the process
        manager = ProcessManager(db)
        manager.stop_process(process_id, force=force)
        
        # Remove from database
        db.delete(process)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop process: {str(e)}"
        )


@router.post("/{process_id}/restart", response_model=ProcessResponse)
async def restart_process(
    process_id: int,
    db: Session = Depends(get_db)
):
    """Restart a process"""
    process = db.query(Process).filter(Process.id == process_id).first()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process with id {process_id} not found"
        )
    
    try:
        manager = ProcessManager(db)
        manager.restart_process(process_id)
        
        db.refresh(process)
        return ProcessResponse.model_validate(process)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart process: {str(e)}"
        )