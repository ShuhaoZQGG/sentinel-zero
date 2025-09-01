"""Configuration management system for SentinelZero."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class ProcessConfig(BaseModel):
    """Configuration for a managed process."""
    
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(..., min_length=1, description="Unique process name")
    command: str = Field(..., min_length=1, description="Command to execute")
    working_directory: Optional[str] = Field(None, description="Working directory for the process")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    auto_start: bool = Field(False, description="Start automatically on service startup")
    enabled: bool = Field(True, description="Whether the process is enabled")
    
    @field_validator('name', 'command')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class ScheduleConfig(BaseModel):
    """Configuration for scheduled task execution."""
    
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(..., min_length=1, description="Unique schedule name")
    process_name: str = Field(..., description="Name of the process to schedule")
    schedule_type: str = Field(..., description="Type of schedule: 'cron' or 'interval'")
    cron_expression: Optional[str] = Field(None, description="Cron expression for cron schedules")
    interval_seconds: Optional[int] = Field(None, gt=0, description="Interval in seconds")
    enabled: bool = Field(True, description="Whether the schedule is enabled")
    
    @field_validator('schedule_type')
    @classmethod
    def validate_schedule_type(cls, v: str) -> str:
        """Validate schedule type."""
        if v not in ['cron', 'interval']:
            raise ValueError("schedule_type must be 'cron' or 'interval'")
        return v
    
    @model_validator(mode='after')
    def validate_schedule(self):
        """Validate schedule configuration based on type."""
        if self.schedule_type == 'cron' and not self.cron_expression:
            raise ValueError("cron_expression is required for cron schedule type")
        if self.schedule_type == 'interval' and self.interval_seconds is None:
            raise ValueError("interval_seconds is required for interval schedule type")
        return self


class RestartPolicyConfig(BaseModel):
    """Configuration for process restart policies."""
    
    model_config = ConfigDict(extra='forbid')
    
    process_name: str = Field(..., description="Name of the process this policy applies to")
    max_retries: int = Field(3, ge=0, description="Maximum number of restart attempts")
    retry_delay_seconds: int = Field(1, ge=0, description="Delay between restart attempts")
    exponential_backoff: bool = Field(False, description="Use exponential backoff for delays")
    restart_on_failure: bool = Field(True, description="Restart on non-zero exit codes")
    restart_on_success: bool = Field(False, description="Restart on zero exit code")
    success_codes: List[int] = Field([0], description="Exit codes considered successful")
    failure_codes: List[int] = Field([], description="Specific exit codes to trigger restart")


class GlobalConfig(BaseModel):
    """Global configuration settings for SentinelZero."""
    
    model_config = ConfigDict(extra='forbid')
    
    log_directory: str = Field("/var/log/sentinelzero", description="Directory for log files")
    log_level: str = Field("INFO", description="Logging level")
    database_path: str = Field("sentinel.db", description="Path to SQLite database")
    api_enabled: bool = Field(False, description="Enable REST API")
    api_port: int = Field(8000, ge=1, le=65535, description="API port")
    api_host: str = Field("127.0.0.1", description="API host")
    max_log_size_mb: int = Field(100, gt=0, description="Maximum log file size in MB")
    log_retention_days: int = Field(30, gt=0, description="Days to retain log files")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()


class SentinelConfig(BaseModel):
    """Complete SentinelZero configuration."""
    
    model_config = ConfigDict(extra='forbid')
    
    global_config: GlobalConfig = Field(default_factory=GlobalConfig)
    processes: List[ProcessConfig] = Field(default_factory=list)
    schedules: List[ScheduleConfig] = Field(default_factory=list)
    restart_policies: List[RestartPolicyConfig] = Field(default_factory=list)


class ConfigManager:
    """Manages SentinelZero configuration files."""
    
    def __init__(self, config_path: str):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self._config = SentinelConfig()
        
    def load_config(self) -> SentinelConfig:
        """Load configuration from YAML file.
        
        Returns:
            Loaded configuration object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValidationError: If configuration validation fails
        """
        if not self.config_path.exists():
            # Return default config if file doesn't exist
            return self._config
            
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Parse global config
        if 'global' in data:
            self._config.global_config = GlobalConfig(**data['global'])
        
        # Parse processes
        if 'processes' in data:
            self._config.processes = [ProcessConfig(**p) for p in data['processes']]
        
        # Parse schedules
        if 'schedules' in data:
            self._config.schedules = [ScheduleConfig(**s) for s in data['schedules']]
        
        # Parse restart policies
        if 'restart_policies' in data:
            self._config.restart_policies = [RestartPolicyConfig(**r) for r in data['restart_policies']]
        
        return self._config
    
    def save_config(self) -> None:
        """Save current configuration to YAML file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict
        data = self.export_config()
        
        # Write to file
        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def get_config(self) -> SentinelConfig:
        """Get current configuration.
        
        Returns:
            Current configuration object
        """
        return self._config
    
    def add_process(self, process: ProcessConfig) -> None:
        """Add a new process configuration.
        
        Args:
            process: Process configuration to add
            
        Raises:
            ValueError: If process with same name already exists
        """
        if any(p.name == process.name for p in self._config.processes):
            raise ValueError(f"Process '{process.name}' already exists")
        self._config.processes.append(process)
    
    def update_process(self, name: str, process: ProcessConfig) -> None:
        """Update an existing process configuration.
        
        Args:
            name: Name of process to update
            process: New process configuration
            
        Raises:
            ValueError: If process doesn't exist
        """
        for i, p in enumerate(self._config.processes):
            if p.name == name:
                self._config.processes[i] = process
                return
        raise ValueError(f"Process '{name}' not found")
    
    def remove_process(self, name: str) -> None:
        """Remove a process configuration.
        
        Args:
            name: Name of process to remove
            
        Raises:
            ValueError: If process doesn't exist
        """
        for i, p in enumerate(self._config.processes):
            if p.name == name:
                del self._config.processes[i]
                return
        raise ValueError(f"Process '{name}' not found")
    
    def add_schedule(self, schedule: ScheduleConfig) -> None:
        """Add a new schedule configuration.
        
        Args:
            schedule: Schedule configuration to add
            
        Raises:
            ValueError: If schedule with same name already exists
        """
        if any(s.name == schedule.name for s in self._config.schedules):
            raise ValueError(f"Schedule '{schedule.name}' already exists")
        self._config.schedules.append(schedule)
    
    def update_schedule(self, name: str, schedule: ScheduleConfig) -> None:
        """Update an existing schedule configuration.
        
        Args:
            name: Name of schedule to update
            schedule: New schedule configuration
            
        Raises:
            ValueError: If schedule doesn't exist
        """
        for i, s in enumerate(self._config.schedules):
            if s.name == name:
                self._config.schedules[i] = schedule
                return
        raise ValueError(f"Schedule '{name}' not found")
    
    def remove_schedule(self, name: str) -> None:
        """Remove a schedule configuration.
        
        Args:
            name: Name of schedule to remove
            
        Raises:
            ValueError: If schedule doesn't exist
        """
        for i, s in enumerate(self._config.schedules):
            if s.name == name:
                del self._config.schedules[i]
                return
        raise ValueError(f"Schedule '{name}' not found")
    
    def validate_config(self) -> List[str]:
        """Validate configuration for consistency.
        
        Returns:
            List of validation error messages
        """
        # Load config first if not already loaded
        if not self._config.processes and self.config_path.exists():
            self.load_config()
            
        errors = []
        
        # Check that scheduled processes exist
        process_names = {p.name for p in self._config.processes}
        for schedule in self._config.schedules:
            if schedule.process_name not in process_names:
                errors.append(f"Schedule '{schedule.name}' references non-existent process '{schedule.process_name}'")
        
        # Check that restart policies reference existing processes
        for policy in self._config.restart_policies:
            if policy.process_name not in process_names:
                errors.append(f"Restart policy references non-existent process '{policy.process_name}'")
        
        return errors
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary.
        
        Returns:
            Configuration as dictionary
        """
        data = {}
        
        # Export global config
        data['global'] = self._config.global_config.model_dump()
        
        # Export processes
        if self._config.processes:
            data['processes'] = [p.model_dump() for p in self._config.processes]
        
        # Export schedules
        if self._config.schedules:
            data['schedules'] = [s.model_dump() for s in self._config.schedules]
        
        # Export restart policies
        if self._config.restart_policies:
            data['restart_policies'] = [r.model_dump() for r in self._config.restart_policies]
        
        return data
    
    def import_config(self, data: Dict[str, Any]) -> None:
        """Import configuration from dictionary.
        
        Args:
            data: Configuration dictionary
        """
        self._config = SentinelConfig()
        
        # Import global config
        if 'global' in data:
            self._config.global_config = GlobalConfig(**data['global'])
        
        # Import processes
        if 'processes' in data:
            self._config.processes = [ProcessConfig(**p) for p in data['processes']]
        
        # Import schedules
        if 'schedules' in data:
            self._config.schedules = [ScheduleConfig(**s) for s in data['schedules']]
        
        # Import restart policies
        if 'restart_policies' in data:
            self._config.restart_policies = [RestartPolicyConfig(**r) for r in data['restart_policies']]