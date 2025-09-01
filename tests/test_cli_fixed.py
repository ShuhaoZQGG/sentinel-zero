"""Tests for CLI command parsing and functionality - Fixed version."""

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
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch('src.cli.main.get_session') as mock_session, \
             patch.object(policy_manager, 'apply_policy'):
            
            # Mock the database session
            mock_session.return_value.__enter__ = Mock(return_value=Mock(add=Mock()))
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
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
    
    def test_start_command_simple(self):
        """Test simple command without arguments."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch('src.cli.main.get_session') as mock_session, \
             patch.object(policy_manager, 'apply_policy'):
            # Mock the database session
            mock_session.return_value.__enter__ = Mock(return_value=Mock(add=Mock()))
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
            mock_start.return_value = ProcessInfo(
                name="simple",
                command="echo",
                args=[],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'simple',
                '-c', 'echo'
            ])
            
            assert result.exit_code == 0
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['command'] == 'echo'
            assert call_args['args'] == []
    
    def test_start_command_with_multiple_args_in_cmd(self):
        """Test command with multiple arguments in -c option."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch('src.cli.main.get_session') as mock_session, \
             patch.object(policy_manager, 'apply_policy'):
            # Mock the database session
            mock_session.return_value.__enter__ = Mock(return_value=Mock(add=Mock()))
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
            mock_start.return_value = ProcessInfo(
                name="multi-args",
                command="python",
                args=["script.py", "--option", "value"],
                status=ProcessStatus.RUNNING,
                pid=12345
            )
            
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'multi-args',
                '-c', 'python script.py --option value'
            ])
            
            assert result.exit_code == 0
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['command'] == 'python'
            assert call_args['args'] == ['script.py', '--option', 'value']


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
    
    def test_start_command_with_custom_policy_delay(self):
        """Test starting a process with custom restart policy delay."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch.object(policy_manager, 'apply_policy') as mock_apply, \
             patch.object(policy_manager, 'get_policy') as mock_get, \
             patch.object(policy_manager, 'create_policy') as mock_create, \
             patch('src.cli.main.get_session') as mock_session:
            
            # Mock the database session
            mock_session.return_value.__enter__ = Mock(return_value=Mock(add=Mock()))
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
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
    
    def test_policy_list_shows_delay(self):
        """Test that policy list command shows custom delays correctly."""
        with patch.object(policy_manager, 'list_policies') as mock_list:
            mock_list.return_value = [
                {
                    'name': 'custom-delay',
                    'max_retries': 5,
                    'retry_delay': 18000,  # 5 hours
                    'backoff_multiplier': 1.5,
                    'max_delay': 36000
                }
            ]
            
            result = self.runner.invoke(cli, ['policy', 'list'])
            
            assert result.exit_code == 0
            # Should display delay in human-readable format
            assert "5h" in result.output or "18000" in result.output


class TestIssue10Fix:
    """Test the fix for Issue #10 - long command arguments."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_issue_10_exact_command(self):
        """Test the exact command from Issue #10."""
        with patch.object(process_manager, 'start_process') as mock_start, \
             patch('src.cli.main.get_session') as mock_session, \
             patch.object(policy_manager, 'apply_policy'):
            # Mock the database session
            mock_session.return_value.__enter__ = Mock(return_value=Mock(add=Mock()))
            mock_session.return_value.__exit__ = Mock(return_value=None)
            
            mock_start.return_value = ProcessInfo(
                name="orchestrate-project",
                command="./orchestrate.sh",
                args=["start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file"],
                status=ProcessStatus.RUNNING,
                pid=12345,
                working_dir="/Users/shuhaozhang/Project/sentinel-zero"
            )
            
            # The exact command from the issue
            result = self.runner.invoke(cli, [
                'start',
                '-n', 'orchestrate-project',
                '-c', "./orchestrate.sh 'start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies. Check the detailed vision in README.md file'",
                '-d', '/Users/shuhaozhang/Project/sentinel-zero',
                '--restart-policy', 'standard'
            ])
            
            assert result.exit_code == 0
            assert "Started process 'orchestrate-project'" in result.output
            
            # Verify correct parsing
            mock_start.assert_called_once()
            call_args = mock_start.call_args[1]
            assert call_args['command'] == './orchestrate.sh'
            assert len(call_args['args']) == 1
            assert 'start a new project sentinel-zero' in call_args['args'][0]


class TestIssue11Fix:
    """Test the fix for Issue #11 - custom restart delay."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_issue_11_custom_delay(self):
        """Test creating a restart policy with 5 hour delay as requested in Issue #11."""
        with patch.object(policy_manager, 'create_policy') as mock_create:
            result = self.runner.invoke(cli, [
                'policy', 'create',
                '-n', 'long-restart',
                '--retries', '3',
                '--delay', '5h'
            ])
            
            assert result.exit_code == 0
            assert "Created restart policy 'long-restart'" in result.output
            
            # Verify 5 hour delay
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['retry_delay'] == 18000  # 5 hours = 18000 seconds