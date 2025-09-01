"""Tests for configuration loading and validation."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.config.config_loader import (
    Config,
    ConfigLoader,
    DefaultsConfig,
    PolicyConfig,
    ProcessConfig,
    ScheduleConfig,
    create_example_config,
)


class TestPolicyConfig:
    """Test PolicyConfig validation."""

    def test_valid_policy_config(self):
        """Test creating a valid policy configuration."""
        config = PolicyConfig(
            max_retries=5,
            delay="10s",
            backoff=2.0,
            restart_on_codes=[1, 2, 3]
        )
        assert config.max_retries == 5
        assert config.delay == 10.0  # Converted to seconds
        assert config.backoff == 2.0
        assert config.restart_on_codes == [1, 2, 3]

    def test_delay_parsing(self):
        """Test parsing different delay formats."""
        assert PolicyConfig(delay="5s").delay == 5.0
        assert PolicyConfig(delay="2m").delay == 120.0
        assert PolicyConfig(delay="1h").delay == 3600.0
        assert PolicyConfig(delay="1d").delay == 86400.0
        assert PolicyConfig(delay="1.5m").delay == 90.0

    def test_invalid_delay_format(self):
        """Test invalid delay format raises error."""
        with pytest.raises(ValidationError):
            PolicyConfig(delay="5x")  # Invalid unit
        
        with pytest.raises(ValidationError):
            PolicyConfig(delay="abc")  # No number
        
        with pytest.raises(ValidationError):
            PolicyConfig(delay="-5s")  # Negative delay

    def test_boundary_values(self):
        """Test boundary values for policy configuration."""
        # Min values
        config = PolicyConfig(max_retries=0, backoff=1.0)
        assert config.max_retries == 0
        assert config.backoff == 1.0
        
        # Max values
        config = PolicyConfig(max_retries=100, backoff=10.0)
        assert config.max_retries == 100
        assert config.backoff == 10.0
        
        # Out of bounds
        with pytest.raises(ValidationError):
            PolicyConfig(max_retries=-1)
        
        with pytest.raises(ValidationError):
            PolicyConfig(max_retries=101)
        
        with pytest.raises(ValidationError):
            PolicyConfig(backoff=0.9)
        
        with pytest.raises(ValidationError):
            PolicyConfig(backoff=10.1)


class TestScheduleConfig:
    """Test ScheduleConfig validation."""

    def test_valid_schedule_config(self):
        """Test creating valid schedule configurations."""
        # Cron schedule
        config = ScheduleConfig(
            type="cron",
            expression="0 * * * *",
            enabled=True
        )
        assert config.type == "cron"
        assert config.expression == "0 * * * *"
        assert config.enabled is True
        
        # Interval schedule
        config = ScheduleConfig(
            type="interval",
            expression="300",
            enabled=False
        )
        assert config.type == "interval"
        assert config.expression == "300"
        assert config.enabled is False

    def test_invalid_schedule_type(self):
        """Test invalid schedule type raises error."""
        with pytest.raises(ValidationError):
            ScheduleConfig(type="invalid", expression="* * * * *")


class TestProcessConfig:
    """Test ProcessConfig validation."""

    def test_valid_process_config(self):
        """Test creating a valid process configuration."""
        config = ProcessConfig(
            name="test-process",
            command="echo hello",
            directory="/tmp",
            environment={"KEY": "value"},
            group="test-group",
            args=["arg1", "arg2"]
        )
        assert config.name == "test-process"
        assert config.command == "echo hello"
        assert config.directory == "/tmp"
        assert config.environment == {"KEY": "value"}
        assert config.group == "test-group"
        assert config.args == ["arg1", "arg2"]

    def test_process_with_nested_configs(self):
        """Test process with restart and schedule configurations."""
        config = ProcessConfig(
            name="complex-process",
            command="python app.py",
            restart=PolicyConfig(max_retries=3, delay="5s"),
            schedule=ScheduleConfig(type="cron", expression="0 * * * *")
        )
        assert config.restart.max_retries == 3
        assert config.restart.delay == 5.0
        assert config.schedule.type == "cron"

    def test_invalid_process_name(self):
        """Test invalid process names raise errors."""
        with pytest.raises(ValidationError):
            ProcessConfig(name="", command="echo")  # Empty name
        
        with pytest.raises(ValidationError):
            ProcessConfig(name="  ", command="echo")  # Whitespace only
        
        with pytest.raises(ValidationError):
            ProcessConfig(name="a" * 101, command="echo")  # Too long


class TestDefaultsConfig:
    """Test DefaultsConfig validation."""

    def test_valid_defaults_config(self):
        """Test creating valid defaults configuration."""
        config = DefaultsConfig(
            log_level="debug",
            restart_policy="aggressive",
            working_dir="/home/user"
        )
        assert config.log_level == "debug"
        assert config.restart_policy == "aggressive"
        assert config.working_dir == "/home/user"

    def test_log_level_validation(self):
        """Test log level validation."""
        for level in ['debug', 'info', 'warning', 'error']:
            config = DefaultsConfig(log_level=level)
            assert config.log_level == level
        
        # Case insensitive
        config = DefaultsConfig(log_level="DEBUG")
        assert config.log_level == "debug"
        
        # Invalid level
        with pytest.raises(ValidationError):
            DefaultsConfig(log_level="invalid")


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_load_yaml_config(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
defaults:
  log_level: info
  restart_policy: standard
  
processes:
  - name: test-process
    command: echo hello
    
policies:
  standard:
    max_retries: 3
    delay: 5s
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            loader = ConfigLoader()
            config = loader.load(Path(f.name))
            
            assert config.defaults.log_level == "info"
            assert len(config.processes) == 1
            assert config.processes[0].name == "test-process"
            assert "standard" in config.policies
            
            # Cleanup
            Path(f.name).unlink()

    def test_load_json_config(self):
        """Test loading configuration from JSON file."""
        json_content = {
            "defaults": {
                "log_level": "debug"
            },
            "processes": [
                {
                    "name": "json-process",
                    "command": "ls -la"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            
            loader = ConfigLoader()
            config = loader.load(Path(f.name))
            
            assert config.defaults.log_level == "debug"
            assert len(config.processes) == 1
            assert config.processes[0].name == "json-process"
            
            # Cleanup
            Path(f.name).unlink()

    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config(
            defaults=DefaultsConfig(log_level="info"),
            processes=[
                ProcessConfig(name="test", command="echo")
            ]
        )
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            loader = ConfigLoader()
            loader.config = config
            loader.save(Path(f.name))
            
            # Load it back
            loaded_config = loader.load(Path(f.name))
            assert loaded_config.defaults.log_level == "info"
            assert len(loaded_config.processes) == 1
            
            # Cleanup
            Path(f.name).unlink()

    def test_get_process_config(self):
        """Test retrieving specific process configuration."""
        config = Config(
            processes=[
                ProcessConfig(name="process1", command="cmd1"),
                ProcessConfig(name="process2", command="cmd2")
            ]
        )
        
        loader = ConfigLoader()
        loader.config = config
        
        process = loader.get_process_config("process1")
        assert process.name == "process1"
        assert process.command == "cmd1"
        
        # Non-existent process
        assert loader.get_process_config("nonexistent") is None

    def test_get_policy_config(self):
        """Test retrieving specific policy configuration."""
        config = Config(
            policies={
                "policy1": PolicyConfig(max_retries=3),
                "policy2": PolicyConfig(max_retries=5)
            }
        )
        
        loader = ConfigLoader()
        loader.config = config
        
        policy = loader.get_policy_config("policy1")
        assert policy.max_retries == 3
        
        # Non-existent policy
        assert loader.get_policy_config("nonexistent") is None

    def test_apply_defaults(self):
        """Test applying default values to process configuration."""
        config = Config(
            defaults=DefaultsConfig(
                working_dir="/default/path",
                restart_policy="standard"
            ),
            policies={
                "standard": PolicyConfig(max_retries=3, delay="5s")
            }
        )
        
        loader = ConfigLoader()
        loader.config = config
        
        # Process without directory should get default
        process = ProcessConfig(name="test", command="echo")
        process = loader.apply_defaults(process)
        assert process.directory == "/default/path"
        assert process.restart.max_retries == 3
        
        # Process with directory should keep it
        process = ProcessConfig(name="test", command="echo", directory="/custom")
        process = loader.apply_defaults(process)
        assert process.directory == "/custom"

    def test_merge_configs(self):
        """Test merging two configurations."""
        config1 = Config(
            defaults=DefaultsConfig(log_level="info"),
            processes=[
                ProcessConfig(name="process1", command="cmd1")
            ],
            policies={
                "policy1": PolicyConfig(max_retries=3)
            }
        )
        
        config2 = Config(
            defaults=DefaultsConfig(log_level="debug"),
            processes=[
                ProcessConfig(name="process1", command="cmd1-updated"),
                ProcessConfig(name="process2", command="cmd2")
            ],
            policies={
                "policy2": PolicyConfig(max_retries=5)
            }
        )
        
        loader = ConfigLoader()
        loader.config = config1
        merged = loader.merge(config2)
        
        # Defaults should be overridden
        assert merged.defaults.log_level == "debug"
        
        # Process1 should be updated, process2 added
        assert len(merged.processes) == 2
        process1 = next(p for p in merged.processes if p.name == "process1")
        assert process1.command == "cmd1-updated"
        
        # Both policies should exist
        assert len(merged.policies) == 2
        assert "policy1" in merged.policies
        assert "policy2" in merged.policies

    def test_validate_config(self):
        """Test configuration validation."""
        loader = ConfigLoader()
        
        # Valid config
        loader.config = Config(
            processes=[ProcessConfig(name="test", command="echo")]
        )
        assert loader.validate() is True
        
        # No config
        loader.config = None
        assert loader.validate() is False

    def test_reload_config(self):
        """Test reloading configuration from file."""
        initial_content = """
processes:
  - name: initial
    command: echo initial
"""
        
        updated_content = """
processes:
  - name: updated
    command: echo updated
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(initial_content)
            f.flush()
            
            loader = ConfigLoader()
            config = loader.load(Path(f.name))
            assert config.processes[0].name == "initial"
            
            # Update file
            with open(f.name, 'w') as update_f:
                update_f.write(updated_content)
            
            # Reload
            config = loader.reload()
            assert config.processes[0].name == "updated"
            
            # Cleanup
            Path(f.name).unlink()

    def test_create_example_config(self):
        """Test generating example configuration."""
        example = create_example_config()
        assert "web-server" in example
        assert "worker" in example
        assert "standard" in example
        assert "aggressive" in example
        
        # Should be valid YAML
        parsed = yaml.safe_load(example)
        assert "defaults" in parsed
        assert "processes" in parsed
        assert "policies" in parsed