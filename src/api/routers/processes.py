"""Process management API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status
import structlog

from src.api.models.requests import ProcessCreateRequest
from src.api.models.responses import ProcessResponse, MessageResponse
from src.api.deps import get_process_manager, get_config_manager
from src.config.config_manager import ProcessConfig

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=List[ProcessResponse])
async def list_processes():
    """Get all processes."""
    try:
        process_manager = get_process_manager()
        processes = process_manager.get_all_processes()
        return [
            ProcessResponse(
                id=p.id,
                name=p.name,
                command=p.command,
                status=p.status,
                pid=p.pid,
                cpu_percent=getattr(p, 'cpu_percent', None),
                memory_mb=getattr(p, 'memory_mb', None),
                restart_count=getattr(p, 'restart_count', 0),
                last_started=p.started_at
            )
            for p in processes
        ]
    except Exception as e:
        logger.error("Failed to list processes", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=ProcessResponse)
async def get_process(name: str):
    """Get a specific process by name."""
    process_manager = get_process_manager()
    process = process_manager.get_process(name)
    if not process:
        raise HTTPException(status_code=404, detail=f"Process '{name}' not found")
    
    return ProcessResponse(
        id=process.id,
        name=process.name,
        command=process.command,
        status=process.status,
        pid=process.pid,
        cpu_percent=getattr(process, 'cpu_percent', None),
        memory_mb=getattr(process, 'memory_mb', None),
        restart_count=getattr(process, 'restart_count', 0),
        last_started=process.started_at
    )


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_process(request: ProcessCreateRequest):
    """Create a new process."""
    try:
        # Create process config
        config = ProcessConfig(
            name=request.name,
            command=request.command,
            working_directory=request.working_directory,
            environment=request.environment,
            auto_start=request.auto_start,
            enabled=request.enabled
        )
        
        # Add to process manager
        process_manager = get_process_manager()
        process_manager.add_process(
            name=config.name,
            command=config.command,
            working_directory=config.working_directory,
            env_vars=config.environment
        )
        
        # Save to config
        config_manager = get_config_manager()
        config_manager.add_process(config)
        config_manager.save_config()
        
        logger.info("Process created", name=request.name)
        return MessageResponse(message="Process created successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create process", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/start", response_model=MessageResponse)
async def start_process(name: str):
    """Start a process."""
    try:
        process_manager = get_process_manager()
        success = process_manager.start_process(name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to start process '{name}'")
        
        logger.info("Process started", name=name)
        return MessageResponse(message="Process started successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to start process", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/stop", response_model=MessageResponse)
async def stop_process(name: str):
    """Stop a process."""
    try:
        process_manager = get_process_manager()
        success = process_manager.stop_process(name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to stop process '{name}'")
        
        logger.info("Process stopped", name=name)
        return MessageResponse(message="Process stopped successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to stop process", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/restart", response_model=MessageResponse)
async def restart_process(name: str):
    """Restart a process."""
    try:
        process_manager = get_process_manager()
        success = process_manager.restart_process(name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to restart process '{name}'")
        
        logger.info("Process restarted", name=name)
        return MessageResponse(message="Process restarted successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to restart process", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=MessageResponse)
async def delete_process(name: str):
    """Delete a process."""
    try:
        process_manager = get_process_manager()
        # Stop process if running
        process_manager.stop_process(name)
        
        # Remove from process manager
        success = process_manager.remove_process(name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Process '{name}' not found")
        
        # Remove from config
        config_manager = get_config_manager()
        config_manager.remove_process(name)
        config_manager.save_config()
        
        logger.info("Process deleted", name=name)
        return MessageResponse(message="Process deleted successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete process", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))