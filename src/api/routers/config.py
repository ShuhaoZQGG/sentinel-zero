"""Configuration management API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
import structlog

from src.api.models.responses import MessageResponse, ConfigValidationResponse
from src.api.deps import get_config_manager

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=Dict[str, Any])
async def get_config():
    """Get current configuration."""
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        return config_manager.export_config()
    except Exception as e:
        logger.error("Failed to get configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=MessageResponse)
async def update_config(config_data: Dict[str, Any]):
    """Update configuration."""
    try:
        config_manager = get_config_manager()
        # Import new config
        config_manager.import_config(config_data)
        
        # Validate
        errors = config_manager.validate_config()
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Configuration validation failed", "errors": errors}
            )
        
        # Save
        config_manager.save_config()
        
        logger.info("Configuration updated")
        return MessageResponse(message="Configuration updated successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config():
    """Validate current configuration."""
    try:
        config_manager = get_config_manager()
        errors = config_manager.validate_config()
        return ConfigValidationResponse(
            valid=len(errors) == 0,
            errors=errors
        )
    except Exception as e:
        logger.error("Failed to validate configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=MessageResponse)
async def reload_config():
    """Reload configuration from file."""
    try:
        config_manager = get_config_manager()
        # Reload config
        config = config_manager.load_config()
        
        # Validate
        errors = config_manager.validate_config()
        if errors:
            logger.warning("Configuration has validation errors", errors=errors)
        
        logger.info("Configuration reloaded", 
                   processes=len(config.processes),
                   schedules=len(config.schedules))
        
        return MessageResponse(
            message="Configuration reloaded successfully",
            details={"validation_errors": errors} if errors else None
        )
        
    except Exception as e:
        logger.error("Failed to reload configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=Dict[str, Any])
async def export_config():
    """Export configuration as JSON."""
    try:
        config_manager = get_config_manager()
        return config_manager.export_config()
    except Exception as e:
        logger.error("Failed to export configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=MessageResponse)
async def import_config(config_data: Dict[str, Any]):
    """Import configuration from JSON."""
    try:
        config_manager = get_config_manager()
        # Import config
        config_manager.import_config(config_data)
        
        # Validate
        errors = config_manager.validate_config()
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Configuration validation failed", "errors": errors}
            )
        
        # Save
        config_manager.save_config()
        
        logger.info("Configuration imported")
        return MessageResponse(message="Configuration imported successfully")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to import configuration", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))