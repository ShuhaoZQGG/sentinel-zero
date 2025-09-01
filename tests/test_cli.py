"""Tests for CLI command parsing and functionality."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import shlex
from src.cli.main import cli, process_manager, policy_manager
from src.core.process_manager import ProcessInfo, ProcessStatus


class TestCLIArgumentParsing:
    """Test CLI argument parsing, especially for long strings (Issue #10)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_start_command_with_long_string_in_cmd(self):
        """Test that long strings in -c/--cmd are properly handled."""
        with patch.object(process_manager, 'start_process') as mock_start:
            # Mock the return value
            mock_start.return_value = ProcessInfo(
                name="test-process",
                command="./orchestrate.sh",
                args=["start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file"],
                status=ProcessStatus.RUNNING,
                pid=12345,
                working_dir="/test/dir"
            )
            
            # Test with long string in command
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'test-process',
                '-c', './orchestrate.sh "start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file"',
                '-d', '/test/dir'
            ])
            
            assert result.exit_code == 0
            assert "Started process 'test-process'" in result.output
            
            # Verify the command was parsed correctly
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['command'] == './orchestrate.sh'
            assert len(call_args['args']) == 1
            assert 'start a new project sentinel-zero' in call_args['args'][0]
    
    def test_start_command_with_args_option(self):
        """Test that --args option properly handles long strings as single argument."""
        with patch.object(process_manager, 'start_process') as mock_start:
            mock_start.return_value = ProcessInfo(
                name="test-process",
                command="./orchestrate.sh",
                args=["long argument with spaces and special characters"],
                status=ProcessStatus.RUNNING,
                pid=12345,
                working_dir="/test/dir"
            )
            
            # Test with --args option - each --args is a separate argument
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'test-process',
                '-c', './orchestrate.sh',
                '--args', 'long argument with spaces and special characters',
                '-d', '/test/dir'
            ])
            
            assert result.exit_code == 0
            assert "Started process 'test-process'" in result.output
            
            # Verify args were passed correctly (as a single argument)
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['command'] == './orchestrate.sh'
            assert call_args['args'] == ['long argument with spaces and special characters']
    
    def test_start_command_with_multiple_args(self):
        """Test that multiple --args options work correctly."""
        with patch.object(process_manager, 'start_process') as mock_start:
            mock_start.return_value = ProcessInfo(
                name="test-process",
                command="python",
                args=["script.py", "--option", "value with spaces"],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            # Pass multiple args using multiple --args options
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'test-process',
                '-c', 'python',
                '--args', 'script.py',
                '--args', '--option',
                '--args', 'value with spaces'
            ])
            
            assert result.exit_code == 0
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            # Each --args should be a separate argument
            assert call_args['args'] == ['script.py', '--option', 'value with spaces']
    
    def test_start_command_preserves_quotes_in_args(self):
        """Test that quotes in arguments are properly preserved."""
        with patch.object(process_manager, 'start_process') as mock_start:
            mock_start.return_value = ProcessInfo(
                name="test-process",
                command="echo",
                args=["Hello \"World\""],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'test-process',
                '-c', 'echo',
                '--args', 'Hello "World"'
            ])
            
            assert result.exit_code == 0
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['args'] == ['Hello "World"']


class TestRestartPolicyCustomDelay:
    """Test custom delay option for restart policies (Issue #11)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_create_policy_with_custom_delay_hours(self):
        """Test creating a restart policy with custom delay in hours."""
        with patch.object(policy_manager, 'create_policy') as mock_create:
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'custom-policy',
                '--retries', '3',
                '--delay', '5h'
            ])
            
            # Command should succeed
            assert result.exit_code == 0
            assert "Created restart policy 'custom-policy'" in result.output
            
            # Verify the policy was created with correct delay (5 hours = 18000 seconds)
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['name'] == 'custom-policy'
            assert call_args['max_retries'] == 3
            assert call_args['retry_delay'] == 18000  # 5 hours in seconds
    
    def test_create_policy_with_custom_delay_minutes(self):
        """Test creating a restart policy with custom delay in minutes."""
        with patch.object(policy_manager, 'create_policy') as mock_create:
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'minute-policy',
                '--retries', '5',
                '--delay', '30m'
            ])
            
            assert result.exit_code == 0
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['retry_delay'] == 1800  # 30 minutes in seconds
    
    def test_create_policy_with_custom_delay_seconds(self):
        """Test creating a restart policy with custom delay in seconds."""
        with patch.object(policy_manager, 'create_policy') as mock_create:
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'second-policy',
                '--retries', '10',
                '--delay', '120s'
            ])
            
            assert result.exit_code == 0
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['retry_delay'] == 120  # 120 seconds
    
    def test_create_policy_with_custom_delay_default_seconds(self):
        """Test creating a restart policy with numeric delay (defaults to seconds)."""
        with patch.object(policy_manager, 'create_policy') as mock_create:
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'numeric-policy',
                '--retries', '5',
                '--delay', '60'
            ])
            
            assert result.exit_code == 0
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['retry_delay'] == 60  # 60 seconds
    
    def test_start_command_with_custom_policy_delay(self):
        """Test starting a process with custom restart policy delay."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch.object(policy_manager, 'apply_policy') as mock_apply, \
             patch.object(policy_manager, 'get_policy') as mock_get, \
             patch.object(policy_manager, 'create_policy') as mock_create:
            
            # Mock the base policy
            mock_base_policy = Mock()
            mock_base_policy.max_retries = 3
            mock_base_policy.backoff_multiplier = 1.5
            mock_base_policy.max_delay = 300
            mock_get.return_value = mock_base_policy
            
            mock_start.return_value = ProcessInfo(
                name="delayed-process",
                command="test.sh",
                args=[],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'delayed-process',
                '-c', 'test.sh',
                '--restart-policy', 'standard',
                '--restart-delay', '2h'
            ])
            
            assert result.exit_code == 0
            
            # Verify custom policy was created with correct delay
            mock_create.assert_called_once()
            create_args = mock_create.call_args[1]
            assert create_args['name'] == 'standard_custom_delayed-process'
            assert create_args['retry_delay'] == 7200  # 2 hours in seconds
            
            # Verify the custom policy was applied
            mock_apply.assert_called_once()
            call_args = mock_apply.call_args
            assert call_args[0][0] == 'delayed-process'  # process name
            assert call_args[0][1] == 'standard_custom_delayed-process'  # custom policy name
    
    def test_invalid_delay_format(self):
        """Test that invalid delay format is properly rejected."""
        result = self.runner.invoke(cli, [
            'policy', 'create',
            '-n', 'bad-policy',
            '--retries', '3',
            '--delay', 'invalid'
        ])
        
        assert result.exit_code != 0
        assert "Invalid delay format" in result.output or "Error" in result.output
    
    def test_policy_list_shows_delay(self):
        """Test that policy list command shows custom delays correctly."""
        with patch.object(policy_manager, 'list_policies') as mock_list:
            mock_list.return_value = [
                {
                    'name': 'custom-delay',
                    'max_retries': 5,
                    'retry_delay': 18000,  # 5 hours
                    'backoff_multiplier': 1.5
                }
            ]
            
            result = self.runner.invoke(cli, ['policy', 'list'])
            
            assert result.exit_code == 0
            # Should display delay in human-readable format
            assert "5h" in result.output or "18000" in result.output


class TestCLIIntegration:
    """Integration tests for CLI fixes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_complex_command_with_policy_and_delay(self):
        """Test complex command with both long args and custom delay."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch.object(policy_manager, 'create_policy') as mock_create_policy, \
             patch.object(policy_manager, 'apply_policy') as mock_apply:
            
            mock_start.return_value = ProcessInfo(
                name="complex-process",
                command="./complex.sh",
                args=["very long argument string with multiple words and special characters!"],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            # First create a custom policy
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'long-delay',
                '--retries', '5',
                '--delay', '3h'
            ])
            assert result.exit_code == 0
            
            # Then start process with that policy
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'complex-process',
                '-c', './complex.sh "very long argument string with multiple words and special characters!"',
                '--restart-policy', 'long-delay'
            ])
            
            assert result.exit_code == 0
            assert "Started process 'complex-process'" in result.output