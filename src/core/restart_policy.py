"""Restart policy module for automatic process recovery."""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
import structlog

logger = structlog.get_logger()


class RestartDecision(Enum):
    """Decision on whether to restart a process."""
    RESTART = "restart"
    STOP = "stop"
    BACKOFF = "backoff"


@dataclass
class RestartPolicy:
    """Defines a restart policy for processes."""
    name: str
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    backoff_multiplier: float = 1.5
    max_delay: int = 300  # Maximum delay in seconds (5 minutes)
    restart_on_codes: Optional[Set[int]] = None  # Specific exit codes to restart on
    ignore_codes: Optional[Set[int]] = None  # Exit codes to not restart on
    health_check_command: Optional[str] = None
    health_check_interval: int = 30  # seconds
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RestartState:
    """Tracks restart state for a process."""
    process_name: str
    policy_name: str
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    current_delay: int = 0
    consecutive_failures: int = 0


class RestartPolicyManager:
    """Manages restart policies and decisions."""
    
    def __init__(self):
        """Initialize the restart policy manager."""
        self._policies: Dict[str, RestartPolicy] = {}
        self._process_policies: Dict[str, str] = {}  # process_name -> policy_name
        self._restart_states: Dict[str, RestartState] = {}
        
        # Create default policies
        self._create_default_policies()
        
        logger.info("RestartPolicyManager initialized")
    
    def _create_default_policies(self):
        """Create default restart policies."""
        # Standard policy
        self.create_policy(
            name="standard",
            max_retries=3,
            retry_delay=5,
            backoff_multiplier=1.5
        )
        
        # Aggressive policy
        self.create_policy(
            name="aggressive",
            max_retries=10,
            retry_delay=1,
            backoff_multiplier=2.0,
            max_delay=60
        )
        
        # Conservative policy
        self.create_policy(
            name="conservative",
            max_retries=5,
            retry_delay=30,
            backoff_multiplier=1.2,
            max_delay=600
        )
        
        # No restart policy
        self.create_policy(
            name="none",
            max_retries=0
        )
    
    def create_policy(
        self,
        name: str,
        max_retries: int = 3,
        retry_delay: int = 5,
        backoff_multiplier: float = 1.5,
        max_delay: int = 300,
        restart_on_codes: Optional[List[int]] = None,
        ignore_codes: Optional[List[int]] = None,
        health_check_command: Optional[str] = None,
        health_check_interval: int = 30
    ) -> RestartPolicy:
        """Create a new restart policy."""
        if name in self._policies:
            raise ValueError(f"Policy '{name}' already exists")
        
        policy = RestartPolicy(
            name=name,
            max_retries=max_retries,
            retry_delay=retry_delay,
            backoff_multiplier=backoff_multiplier,
            max_delay=max_delay,
            restart_on_codes=set(restart_on_codes) if restart_on_codes else None,
            ignore_codes=set(ignore_codes) if ignore_codes else None,
            health_check_command=health_check_command,
            health_check_interval=health_check_interval
        )
        
        self._policies[name] = policy
        logger.info(f"Created restart policy '{name}'")
        
        return policy
    
    def update_policy(self, name: str, **kwargs) -> RestartPolicy:
        """Update an existing policy."""
        if name not in self._policies:
            raise ValueError(f"Policy '{name}' not found")
        
        policy = self._policies[name]
        
        for key, value in kwargs.items():
            if hasattr(policy, key):
                if key in ['restart_on_codes', 'ignore_codes'] and value is not None:
                    value = set(value)
                setattr(policy, key, value)
        
        logger.info(f"Updated policy '{name}'")
        return policy
    
    def delete_policy(self, name: str) -> bool:
        """Delete a policy."""
        if name in ["standard", "aggressive", "conservative", "none"]:
            raise ValueError(f"Cannot delete built-in policy '{name}'")
        
        if name not in self._policies:
            return False
        
        # Check if any process is using this policy
        if any(p == name for p in self._process_policies.values()):
            raise ValueError(f"Policy '{name}' is in use by processes")
        
        del self._policies[name]
        logger.info(f"Deleted policy '{name}'")
        return True
    
    def get_policy(self, name: str) -> Optional[RestartPolicy]:
        """Get a policy by name."""
        return self._policies.get(name)
    
    def list_policies(self) -> List[RestartPolicy]:
        """List all policies."""
        return list(self._policies.values())
    
    def apply_policy(self, process_name: str, policy_name: str) -> None:
        """Apply a policy to a process."""
        if policy_name not in self._policies:
            raise ValueError(f"Policy '{policy_name}' not found")
        
        self._process_policies[process_name] = policy_name
        
        # Initialize restart state
        self._restart_states[process_name] = RestartState(
            process_name=process_name,
            policy_name=policy_name
        )
        
        logger.info(f"Applied policy '{policy_name}' to process '{process_name}'")
    
    def should_restart(
        self,
        process_name: str,
        exit_code: int,
        crashed: bool = False
    ) -> tuple[RestartDecision, int]:
        """Determine if a process should be restarted.
        
        Returns:
            Tuple of (decision, delay_seconds)
        """
        # Check if process has a policy
        if process_name not in self._process_policies:
            return (RestartDecision.STOP, 0)
        
        policy_name = self._process_policies[process_name]
        policy = self._policies[policy_name]
        
        # Get or create restart state
        if process_name not in self._restart_states:
            self._restart_states[process_name] = RestartState(
                process_name=process_name,
                policy_name=policy_name
            )
        
        state = self._restart_states[process_name]
        
        # Check if we should ignore this exit code
        if policy.ignore_codes and exit_code in policy.ignore_codes:
            logger.info(f"Process '{process_name}' exit code {exit_code} is in ignore list")
            return (RestartDecision.STOP, 0)
        
        # Check if we should only restart on specific codes
        if policy.restart_on_codes and exit_code not in policy.restart_on_codes:
            logger.info(f"Process '{process_name}' exit code {exit_code} not in restart list")
            return (RestartDecision.STOP, 0)
        
        # Check max retries
        if state.restart_count >= policy.max_retries:
            logger.warning(f"Process '{process_name}' exceeded max retries ({policy.max_retries})")
            return (RestartDecision.STOP, 0)
        
        # Calculate delay with backoff
        if state.restart_count == 0:
            delay = policy.retry_delay
        else:
            delay = min(
                state.current_delay * policy.backoff_multiplier,
                policy.max_delay
            )
        
        # Update state
        state.restart_count += 1
        state.current_delay = int(delay)
        state.last_restart = datetime.now()
        
        if crashed:
            state.consecutive_failures += 1
        else:
            state.consecutive_failures = 0
        
        logger.info(
            f"Process '{process_name}' will restart in {delay}s "
            f"(attempt {state.restart_count}/{policy.max_retries})"
        )
        
        return (RestartDecision.RESTART, int(delay))
    
    def reset_restart_count(self, process_name: str) -> None:
        """Reset the restart count for a process."""
        if process_name in self._restart_states:
            self._restart_states[process_name].restart_count = 0
            self._restart_states[process_name].consecutive_failures = 0
            self._restart_states[process_name].current_delay = 0
            logger.info(f"Reset restart count for process '{process_name}'")
    
    def get_restart_state(self, process_name: str) -> Optional[RestartState]:
        """Get the restart state for a process."""
        return self._restart_states.get(process_name)
    
    def get_process_policy(self, process_name: str) -> Optional[str]:
        """Get the policy name applied to a process."""
        return self._process_policies.get(process_name)