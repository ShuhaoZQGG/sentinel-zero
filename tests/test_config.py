"""Tests for configuration management system."""

import os
import tempfile
from pathlib import Path
import pytest
import yaml
from pydantic import ValidationError

from src.config.config_manager import ConfigManager, ProcessConfig, ScheduleConfig, RestartPolicyConfig, GlobalConfig


class TestProcessConfig:
    """Test ProcessConfig model validation."""
    
    def test_valid_process_config(self):
        """Test creating a valid process configuration."""
        config = ProcessConfig(
            name="test_process",
            command="python script.py",
            working_directory="/tmp",
            environment={"KEY": "value"},
            auto_start=True,
            enabled=True
        )
        assert config.name == "test_process"
        assert config.command == "python script.py"
        assert config.working_directory == "/tmp"
        assert config.environment == {"KEY": "value"}
        assert config.auto_start is True
        assert config.enabled is True
    
    def test_minimal_process_config(self):
        """Test creating process config with minimal required fields."""
        config = ProcessConfig(
            name="minimal",
            command="echo hello"
        )
        assert config.name == "minimal"
        assert config.command == "echo hello"
        assert config.working_directory is None
        assert config.environment == {}
        assert config.auto_start is False
        assert config.enabled is True
    
    def test_invalid_process_config(self):
        """Test validation errors for invalid process config."""
        with pytest.raises(ValidationError):
            ProcessConfig(name="", command="echo test")  # Empty name
        
        with pytest.raises(ValidationError):
            ProcessConfig(name="test", command="")  # Empty command


class TestScheduleConfig:
    """Test ScheduleConfig model validation."""
    
    def test_cron_schedule(self):
        """Test creating a cron-based schedule."""
        config = ScheduleConfig(
            name="backup",
            process_name="backup_process",
            schedule_type="cron",
            cron_expression="0 2 * * *",
            enabled=True
        )
        assert config.name == "backup"
        assert config.schedule_type == "cron"
        assert config.cron_expression == "0 2 * * *"
        assert config.interval_seconds is None
    
    def test_interval_schedule(self):
        """Test creating an interval-based schedule."""
        config = ScheduleConfig(
            name="heartbeat",
            process_name="heartbeat_process",
            schedule_type="interval",
            interval_seconds=60,
            enabled=True
        )
        assert config.name == "heartbeat"
        assert config.schedule_type == "interval"
        assert config.interval_seconds == 60
        assert config.cron_expression is None
    
    def test_invalid_schedule_config(self):
        """Test validation errors for schedule config."""
        with pytest.raises(ValidationError):
            # Missing cron expression for cron type
            ScheduleConfig(
                name="test",
                process_name="test_process",
                schedule_type="cron"
            )
        
        with pytest.raises(ValidationError):
            # Missing interval for interval type
            ScheduleConfig(
                name="test",
                process_name="test_process",
                schedule_type="interval"
            )


class TestRestartPolicyConfig:
    """Test RestartPolicyConfig model validation."""
    
    def test_valid_restart_policy(self):
        """Test creating a valid restart policy."""
        config = RestartPolicyConfig(
            process_name="web_server",
            max_retries=3,
            retry_delay_seconds=5,
            exponential_backoff=True,
            restart_on_failure=True,
            restart_on_success=False,
            success_codes=[0],
            failure_codes=[1, 2]
        )
        assert config.process_name == "web_server"
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 5
        assert config.exponential_backoff is True
    
    def test_default_restart_policy(self):
        """Test restart policy with default values."""
        config = RestartPolicyConfig(process_name="test")
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 1
        assert config.exponential_backoff is False
        assert config.restart_on_failure is True
        assert config.restart_on_success is False
        assert config.success_codes == [0]
        assert config.failure_codes == []


class TestGlobalConfig:
    """Test GlobalConfig model validation."""
    
    def test_valid_global_config(self):
        """Test creating a valid global configuration."""
        config = GlobalConfig(
            log_directory="/var/log/sentinelzero",
            log_level="INFO",
            database_path="/var/lib/sentinelzero/sentinel.db",
            api_enabled=True,
            api_port=8080,
            api_host="0.0.0.0",
            max_log_size_mb=100,
            log_retention_days=30
        )
        assert config.log_directory == "/var/log/sentinelzero"
        assert config.api_port == 8080
        assert config.api_enabled is True
    
    def test_default_global_config(self):
        """Test global config with default values."""
        config = GlobalConfig()
        assert config.log_level == "INFO"
        assert config.api_enabled is False
        assert config.api_port == 8000
        assert config.api_host == "127.0.0.1"


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_load_valid_yaml_config(self, tmp_path):
        """Test loading a valid YAML configuration file."""
        config_content = """
global:
  log_directory: /tmp/logs
  log_level: DEBUG
  api_enabled: true
  api_port: 8080

processes:
  - name: web_server
    command: python app.py
    working_directory: /app
    environment:
      PORT: "8000"
    auto_start: true
    
  - name: worker
    command: python worker.py
    enabled: false

schedules:
  - name: daily_backup
    process_name: backup_script
    schedule_type: cron
    cron_expression: "0 2 * * *"
    enabled: true

restart_policies:
  - process_name: web_server
    max_retries: 5
    retry_delay_seconds: 10
    exponential_backoff: true
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        assert config.global_config.log_level == "DEBUG"
        assert config.global_config.api_enabled is True
        assert len(config.processes) == 2
        assert config.processes[0].name == "web_server"
        assert config.processes[1].enabled is False
        assert len(config.schedules) == 1
        assert len(config.restart_policies) == 1
    
    def test_load_minimal_config(self, tmp_path):
        """Test loading config with minimal settings."""
        config_content = """
processes:
  - name: simple_process
    command: echo hello
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        assert len(config.processes) == 1
        assert config.processes[0].name == "simple_process"
        assert config.global_config.log_level == "INFO"  # Default
    
    def test_save_config(self, tmp_path):
        """Test saving configuration to YAML file."""
        config_file = tmp_path / "output.yaml"
        manager = ConfigManager(str(config_file))
        
        # Create configuration
        process = ProcessConfig(name="test", command="test.sh")
        schedule = ScheduleConfig(
            name="hourly",
            process_name="test",
            schedule_type="interval",
            interval_seconds=3600
        )
        
        manager.add_process(process)
        manager.add_schedule(schedule)
        manager.save_config()
        
        # Verify saved file
        assert config_file.exists()
        with open(config_file) as f:
            data = yaml.safe_load(f)
        
        assert len(data["processes"]) == 1
        assert data["processes"][0]["name"] == "test"
        assert len(data["schedules"]) == 1
        assert data["schedules"][0]["interval_seconds"] == 3600
    
    def test_update_process(self, tmp_path):
        """Test updating an existing process configuration."""
        config_file = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_file))
        
        # Add initial process
        process = ProcessConfig(name="test", command="old_command.sh")
        manager.add_process(process)
        
        # Update process
        updated = ProcessConfig(name="test", command="new_command.sh", enabled=False)
        manager.update_process("test", updated)
        
        config = manager.get_config()
        assert len(config.processes) == 1
        assert config.processes[0].command == "new_command.sh"
        assert config.processes[0].enabled is False
    
    def test_remove_process(self, tmp_path):
        """Test removing a process configuration."""
        config_file = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_file))
        
        # Add processes
        manager.add_process(ProcessConfig(name="test1", command="cmd1"))
        manager.add_process(ProcessConfig(name="test2", command="cmd2"))
        
        # Remove one
        manager.remove_process("test1")
        
        config = manager.get_config()
        assert len(config.processes) == 1
        assert config.processes[0].name == "test2"
    
    def test_validate_references(self, tmp_path):
        """Test validation of references between configs."""
        config_content = """
processes:
  - name: valid_process
    command: test.sh

schedules:
  - name: schedule1
    process_name: valid_process
    schedule_type: interval
    interval_seconds: 60
    
  - name: schedule2
    process_name: invalid_process  # This process doesn't exist
    schedule_type: interval
    interval_seconds: 60

restart_policies:
  - process_name: invalid_process  # This process doesn't exist
    max_retries: 3
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        manager = ConfigManager(str(config_file))
        errors = manager.validate_config()
        
        assert len(errors) == 2
        assert "invalid_process" in errors[0]
        assert "invalid_process" in errors[1]
    
    def test_export_import_config(self, tmp_path):
        """Test exporting and importing configuration."""
        # Create original config
        original_file = tmp_path / "original.yaml"
        manager1 = ConfigManager(str(original_file))
        
        manager1.add_process(ProcessConfig(name="proc1", command="cmd1"))
        manager1.add_schedule(ScheduleConfig(
            name="sched1",
            process_name="proc1",
            schedule_type="interval",
            interval_seconds=300
        ))
        
        # Export to dict
        export_data = manager1.export_config()
        
        # Import to new manager
        new_file = tmp_path / "imported.yaml"
        manager2 = ConfigManager(str(new_file))
        manager2.import_config(export_data)
        
        # Verify
        config = manager2.get_config()
        assert len(config.processes) == 1
        assert config.processes[0].name == "proc1"
        assert len(config.schedules) == 1
        assert config.schedules[0].name == "sched1"