"""Configuration file loader and validator for SentinelZero."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class PolicyConfig(BaseModel):
    """Configuration for a restart policy."""
    
    max_retries: int = Field(default=3, ge=0, le=100)
    delay: str = Field(default="5s")
    backoff: float = Field(default=1.5, ge=1.0, le=10.0)
    restart_on_codes: Optional[List[int]] = None
    
    @field_validator('delay')
    @classmethod
    def validate_delay(cls, v):
        """Validate and parse delay string."""
        if not isinstance(v, str):
            raise ValueError("Delay must be a string")
        
        # Parse delay string (e.g., "5s", "1m", "1h")
        unit_multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        if v[-1] not in unit_multipliers:
            raise ValueError(f"Invalid delay unit. Use one of: {list(unit_multipliers.keys())}")
        
        try:
            value = float(v[:-1])
            if value < 0:
                raise ValueError("Delay must be positive")
            return value * unit_multipliers[v[-1]]
        except (ValueError, IndexError):
            raise ValueError(f"Invalid delay format: {v}")


class ScheduleConfig(BaseModel):
    """Configuration for a process schedule."""
    
    type: str = Field(default="cron")
    expression: str
    enabled: bool = Field(default=True)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate schedule type."""
        valid_types = ['cron', 'interval', 'once']
        if v not in valid_types:
            raise ValueError(f"Schedule type must be one of: {valid_types}")
        return v


class ProcessConfig(BaseModel):
    """Configuration for a single process."""
    
    name: str
    command: str
    directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
    group: Optional[str] = None
    restart: Optional[PolicyConfig] = None
    schedule: Optional[ScheduleConfig] = None
    args: Optional[List[str]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate process name."""
        if not v or not v.strip():
            raise ValueError("Process name cannot be empty")
        if len(v) > 100:
            raise ValueError("Process name too long (max 100 characters)")
        return v.strip()


class DefaultsConfig(BaseModel):
    """Default configuration values."""
    
    log_level: str = Field(default="info")
    restart_policy: str = Field(default="standard")
    working_dir: Optional[str] = None
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['debug', 'info', 'warning', 'error']
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.lower()


class Config(BaseModel):
    """Root configuration structure."""
    
    defaults: Optional[DefaultsConfig] = None
    processes: Optional[List[ProcessConfig]] = None
    policies: Optional[Dict[str, PolicyConfig]] = None


@dataclass
class ConfigLoader:
    """Loads and validates configuration from YAML or JSON files."""
    
    config_path: Optional[Path] = None
    config: Optional[Config] = None
    _default_config_paths: List[Path] = field(default_factory=lambda: [
        Path.home() / '.sentinel' / 'config.yaml',
        Path.home() / '.sentinel' / 'config.yml',
        Path.home() / '.sentinel' / 'config.json',
        Path('/etc/sentinel/config.yaml'),
        Path('/etc/sentinel/config.yml'),
        Path('/etc/sentinel/config.json'),
        Path('./config.yaml'),
        Path('./config.yml'),
        Path('./config.json'),
    ])
    
    def find_config_file(self) -> Optional[Path]:
        """Find configuration file in default locations."""
        if self.config_path and self.config_path.exists():
            return self.config_path
        
        for path in self._default_config_paths:
            if path.exists() and path.is_file():
                return path
        
        return None
    
    def load(self, config_path: Optional[Path] = None) -> Config:
        """Load configuration from file."""
        if config_path:
            self.config_path = config_path
        
        config_file = self.find_config_file()
        
        if not config_file:
            # Return default configuration if no file found
            return Config()
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_file.suffix}")
            
            # Validate and parse configuration
            self.config = Config(**data) if data else Config()
            return self.config
            
        except FileNotFoundError:
            raise ValueError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if not self.config:
            raise ValueError("No configuration to save")
        
        save_path = config_path or self.config_path
        if not save_path:
            # Use default location
            save_path = Path.home() / '.sentinel' / 'config.yaml'
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.config.model_dump(exclude_none=True)
        
        with open(save_path, 'w') as f:
            if save_path.suffix in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif save_path.suffix == '.json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {save_path.suffix}")
    
    def validate(self) -> bool:
        """Validate current configuration."""
        if not self.config:
            return False
        
        try:
            # Re-validate using Pydantic
            Config(**self.config.model_dump())
            return True
        except ValidationError:
            return False
    
    def get_process_config(self, name: str) -> Optional[ProcessConfig]:
        """Get configuration for a specific process."""
        if not self.config or not self.config.processes:
            return None
        
        for process in self.config.processes:
            if process.name == name:
                return process
        
        return None
    
    def get_policy_config(self, name: str) -> Optional[PolicyConfig]:
        """Get configuration for a specific policy."""
        if not self.config or not self.config.policies:
            return None
        
        return self.config.policies.get(name)
    
    def apply_defaults(self, process_config: ProcessConfig) -> ProcessConfig:
        """Apply default values to a process configuration."""
        if not self.config or not self.config.defaults:
            return process_config
        
        defaults = self.config.defaults
        
        # Apply default working directory if not specified
        if not process_config.directory and defaults.working_dir:
            process_config.directory = defaults.working_dir
        
        # Apply default restart policy if not specified
        if not process_config.restart and defaults.restart_policy:
            policy = self.get_policy_config(defaults.restart_policy)
            if policy:
                process_config.restart = policy
        
        return process_config
    
    def reload(self) -> Config:
        """Reload configuration from file."""
        return self.load(self.config_path)
    
    def merge(self, other_config: Config) -> Config:
        """Merge another configuration into current one."""
        if not self.config:
            self.config = other_config
            return self.config
        
        # Merge defaults
        if other_config.defaults:
            if self.config.defaults:
                self.config.defaults = DefaultsConfig(
                    **{**self.config.defaults.model_dump(), **other_config.defaults.model_dump()}
                )
            else:
                self.config.defaults = other_config.defaults
        
        # Merge processes
        if other_config.processes:
            if self.config.processes:
                # Merge by name, new processes override existing ones
                existing_names = {p.name for p in self.config.processes}
                for process in other_config.processes:
                    if process.name in existing_names:
                        # Replace existing process
                        self.config.processes = [
                            p if p.name != process.name else process
                            for p in self.config.processes
                        ]
                    else:
                        # Add new process
                        self.config.processes.append(process)
            else:
                self.config.processes = other_config.processes
        
        # Merge policies
        if other_config.policies:
            if self.config.policies:
                self.config.policies.update(other_config.policies)
            else:
                self.config.policies = other_config.policies
        
        return self.config


def create_example_config() -> str:
    """Generate an example configuration file content."""
    example = {
        "defaults": {
            "log_level": "info",
            "restart_policy": "standard",
            "working_dir": "~/projects"
        },
        "processes": [
            {
                "name": "web-server",
                "command": "python app.py",
                "directory": "/app",
                "environment": {
                    "PORT": "8080",
                    "ENV": "production"
                },
                "restart": {
                    "max_retries": 5,
                    "delay": "10s",
                    "backoff": 1.5
                },
                "schedule": {
                    "type": "cron",
                    "expression": "0 */6 * * *",
                    "enabled": True
                }
            },
            {
                "name": "worker",
                "command": "python worker.py",
                "group": "background-jobs",
                "restart": {
                    "max_retries": 10,
                    "delay": "1s",
                    "backoff": 2.0
                }
            }
        ],
        "policies": {
            "standard": {
                "max_retries": 3,
                "delay": "5s",
                "backoff": 1.5
            },
            "aggressive": {
                "max_retries": 10,
                "delay": "1s",
                "backoff": 2.0
            },
            "conservative": {
                "max_retries": 2,
                "delay": "30s",
                "backoff": 1.2
            }
        }
    }
    
    return yaml.dump(example, default_flow_style=False, sort_keys=False)