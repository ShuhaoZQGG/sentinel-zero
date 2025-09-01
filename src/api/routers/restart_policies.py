"""Restart policy management API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status
import structlog

from src.api.models.requests import RestartPolicyCreateRequest
from src.api.models.responses import RestartPolicyResponse, MessageResponse
from src.config.config_manager import RestartPolicyConfig
from src.models.models import RestartPolicyModel as RestartPolicy
from src.models.base import SessionLocal

router = APIRouter()
logger = structlog.get_logger()


def get_all_policies() -> List[RestartPolicy]:
    """Get all restart policies from database."""
    db = SessionLocal()
    try:
        return db.query(RestartPolicy).all()
    finally:
        db.close()


def get_policy(process_name: str) -> RestartPolicy:
    """Get restart policy for a specific process."""
    db = SessionLocal()
    try:
        return db.query(RestartPolicy).filter(
            RestartPolicy.process_name == process_name
        ).first()
    finally:
        db.close()


def create_policy(policy_data: RestartPolicyCreateRequest) -> bool:
    """Create a new restart policy."""
    db = SessionLocal()
    try:
        # Check if policy already exists
        existing = db.query(RestartPolicy).filter(
            RestartPolicy.process_name == policy_data.process_name
        ).first()
        
        if existing:
            return False
        
        # Create new policy
        policy = RestartPolicy(
            process_name=policy_data.process_name,
            max_retries=policy_data.max_retries,
            retry_delay_seconds=policy_data.retry_delay_seconds,
            exponential_backoff=policy_data.exponential_backoff,
            restart_on_failure=policy_data.restart_on_failure,
            restart_on_success=policy_data.restart_on_success
        )
        
        db.add(policy)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def update_policy(process_name: str, policy_data: RestartPolicyCreateRequest) -> bool:
    """Update an existing restart policy."""
    db = SessionLocal()
    try:
        policy = db.query(RestartPolicy).filter(
            RestartPolicy.process_name == process_name
        ).first()
        
        if not policy:
            return False
        
        policy.max_retries = policy_data.max_retries
        policy.retry_delay_seconds = policy_data.retry_delay_seconds
        policy.exponential_backoff = policy_data.exponential_backoff
        policy.restart_on_failure = policy_data.restart_on_failure
        policy.restart_on_success = policy_data.restart_on_success
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_policy(process_name: str) -> bool:
    """Delete a restart policy."""
    db = SessionLocal()
    try:
        policy = db.query(RestartPolicy).filter(
            RestartPolicy.process_name == process_name
        ).first()
        
        if not policy:
            return False
        
        db.delete(policy)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@router.get("/", response_model=List[RestartPolicyResponse])
async def list_restart_policies():
    """Get all restart policies."""
    try:
        policies = get_all_policies()
        return [
            RestartPolicyResponse(
                process_name=p.process_name,
                max_retries=p.max_retries,
                retry_delay_seconds=p.retry_delay_seconds,
                exponential_backoff=p.exponential_backoff,
                restart_on_failure=p.restart_on_failure,
                restart_on_success=p.restart_on_success,
                success_codes=p.success_codes or [0],
                failure_codes=p.failure_codes or []
            )
            for p in policies
        ]
    except Exception as e:
        logger.error("Failed to list restart policies", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{process_name}", response_model=RestartPolicyResponse)
async def get_restart_policy(process_name: str):
    """Get restart policy for a specific process."""
    policy = get_policy(process_name)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Restart policy for '{process_name}' not found")
    
    return RestartPolicyResponse(
        process_name=policy.process_name,
        max_retries=policy.max_retries,
        retry_delay_seconds=policy.retry_delay_seconds,
        exponential_backoff=policy.exponential_backoff,
        restart_on_failure=policy.restart_on_failure,
        restart_on_success=policy.restart_on_success,
        success_codes=policy.success_codes or [0],
        failure_codes=policy.failure_codes or []
    )


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_restart_policy(request: RestartPolicyCreateRequest):
    """Create a new restart policy."""
    try:
        # Create policy in database
        success = create_policy(request)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Restart policy for '{request.process_name}' already exists"
            )
        
        # Add to config
        from src.api.deps import get_config_manager
        config_manager = get_config_manager()
        policy_config = RestartPolicyConfig(
            process_name=request.process_name,
            max_retries=request.max_retries,
            retry_delay_seconds=request.retry_delay_seconds,
            exponential_backoff=request.exponential_backoff,
            restart_on_failure=request.restart_on_failure,
            restart_on_success=request.restart_on_success,
            success_codes=request.success_codes,
            failure_codes=request.failure_codes
        )
        
        config = config_manager.get_config()
        config.restart_policies.append(policy_config)
        config_manager.save_config()
        
        logger.info("Restart policy created", process_name=request.process_name)
        return MessageResponse(message="Restart policy created successfully")
        
    except Exception as e:
        logger.error("Failed to create restart policy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{process_name}", response_model=MessageResponse)
async def update_restart_policy(process_name: str, request: RestartPolicyCreateRequest):
    """Update an existing restart policy."""
    try:
        success = update_policy(process_name, request)
        if not success:
            raise HTTPException(status_code=404, detail=f"Restart policy for '{process_name}' not found")
        
        # Update config
        from src.api.deps import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        for i, policy in enumerate(config.restart_policies):
            if policy.process_name == process_name:
                config.restart_policies[i] = RestartPolicyConfig(
                    process_name=request.process_name,
                    max_retries=request.max_retries,
                    retry_delay_seconds=request.retry_delay_seconds,
                    exponential_backoff=request.exponential_backoff,
                    restart_on_failure=request.restart_on_failure,
                    restart_on_success=request.restart_on_success,
                    success_codes=request.success_codes,
                    failure_codes=request.failure_codes
                )
                config_manager.save_config()
                break
        
        logger.info("Restart policy updated", process_name=process_name)
        return MessageResponse(message="Restart policy updated successfully")
        
    except Exception as e:
        logger.error("Failed to update restart policy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{process_name}", response_model=MessageResponse)
async def delete_restart_policy(process_name: str):
    """Delete a restart policy."""
    try:
        success = delete_policy(process_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Restart policy for '{process_name}' not found")
        
        # Remove from config
        from src.api.deps import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()
        config.restart_policies = [
            p for p in config.restart_policies if p.process_name != process_name
        ]
        config_manager.save_config()
        
        logger.info("Restart policy deleted", process_name=process_name)
        return MessageResponse(message="Restart policy deleted successfully")
        
    except Exception as e:
        logger.error("Failed to delete restart policy", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))