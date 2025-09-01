"""Tests for CLI bug fixes (Issues #10 and #11)."""

import pytest
import shlex
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from src.cli.main import cli, process_manager, policy_manager
from src.core.process_manager import ProcessInfo, ProcessStatus
from datetime import datetime


class TestIssue10CLIArgumentParsing:
    """Tests for Issue #10: CLI should accept long strings in -c and --args."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch.object(process_manager, 'start_process')
    @patch.object(policy_manager, 'apply_policy')
    def test_command_with_long_string_shlex(self, mock_apply_policy, mock_start_process):
        """Test that commands with long strings are properly parsed using shlex."""
        # Mock the start_process to return a process info
        mock_start_process.return_value = ProcessInfo(
            name="test-process",
            command="./script.sh",
            args=["start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies."],
            status=ProcessStatus.RUNNING,
            pid=12345,
            started_at=datetime.now(),
            restart_count=0
        )
        
        # Test with a long string in command
        long_string = "start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes with configurable retry policies."
        result = self.runner.invoke(cli, [
            'start',
            '-n', 'test-process',
            '-c', f'./script.sh "{long_string}"',
            '-d', '/Users/test'
        ])
        
        if result.exit_code != 0:
            print(f"Error output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "Started process 'test-process'" in result.output
        
        # Verify the command was parsed correctly
        mock_start_process.assert_called_once()
        call_args = mock_start_process.call_args[1]
        assert call_args['command'] == './script.sh'
        assert long_string in ' '.join(call_args['args'])
    
    @patch.object(process_manager, 'start_process')
    @patch.object(policy_manager, 'apply_policy')
    def test_args_with_long_string(self, mock_apply_policy, mock_start_process):
        """Test that --args option accepts long strings."""
        # Mock the start_process to return a process info
        mock_start_process.return_value = ProcessInfo(
            name="test-process",
            command="./orchestrate.sh",
            args=["start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes"],
            status=ProcessStatus.RUNNING,
            pid=12345,
            started_at=datetime.now(),
            restart_count=0
        )
        
        # Test with long string in --args
        long_arg = "start a new project sentinel-zero, A macOS service that starts, monitors, schedules, and automatically restarts command-line processes"
        result = self.runner.invoke(cli, [
            'start',
            '-n', 'orchestrate-project',
            '-c', './orchestrate.sh',
            '--args', long_arg,
            '-d', '/Users/shuhaozhang/Project/sentinel-zero'
        ])
        
        assert result.exit_code == 0
        assert "Started process 'orchestrate-project'" in result.output
        
        # Verify args were parsed correctly
        mock_start_process.assert_called_once()
        call_args = mock_start_process.call_args[1]
        assert call_args['command'] == './orchestrate.sh'
        # The args should contain the words from the long string
        args_str = ' '.join(call_args['args'])
        assert 'start a new project sentinel-zero' in args_str
        assert 'macOS service' in args_str
    
    @patch.object(process_manager, 'start_process')
    @patch.object(policy_manager, 'apply_policy')
    def test_command_with_quotes_and_spaces(self, mock_apply_policy, mock_start_process):
        """Test commands with quotes and spaces are properly handled."""
        mock_start_process.return_value = ProcessInfo(
            name="complex-cmd",
            command="python",
            args=["script.py", "--message", "Hello World with spaces"],
            status=ProcessStatus.RUNNING,
            pid=12345,
            started_at=datetime.now(),
            restart_count=0
        )
        
        result = self.runner.invoke(cli, [
            'start',
            '-n', 'complex-cmd',
            '-c', 'python script.py --message "Hello World with spaces"',
            '--restart-policy', 'standard'
        ])
        
        assert result.exit_code == 0
        mock_start_process.assert_called_once()
        call_args = mock_start_process.call_args[1]
        assert call_args['command'] == 'python'
        assert 'script.py' in call_args['args']
        assert 'Hello World with spaces' in ' '.join(call_args['args'])


class TestIssue11CustomRestartDelay:
    """Tests for Issue #11: Custom restart delay with time formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_parse_time_format_hours(self):
        """Test parsing time format with hours (5h)."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("5h") == 5 * 3600
        assert parse_time_to_seconds("2.5h") == 2.5 * 3600
        assert parse_time_to_seconds("24h") == 24 * 3600
    
    def test_parse_time_format_minutes(self):
        """Test parsing time format with minutes (30m)."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("30m") == 30 * 60
        assert parse_time_to_seconds("90m") == 90 * 60
        assert parse_time_to_seconds("5.5m") == 5.5 * 60
    
    def test_parse_time_format_seconds(self):
        """Test parsing time format with seconds (45s)."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("45s") == 45
        assert parse_time_to_seconds("120s") == 120
        assert parse_time_to_seconds("0.5s") == 0.5
    
    def test_parse_time_format_days(self):
        """Test parsing time format with days (2d)."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("2d") == 2 * 86400
        assert parse_time_to_seconds("0.5d") == 0.5 * 86400
        assert parse_time_to_seconds("7d") == 7 * 86400
    
    def test_parse_time_format_combined(self):
        """Test parsing combined time formats."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("1h30m") == 3600 + 1800
        assert parse_time_to_seconds("2d4h") == 2 * 86400 + 4 * 3600
        assert parse_time_to_seconds("1h30m45s") == 3600 + 1800 + 45
    
    def test_parse_time_format_plain_number(self):
        """Test parsing plain numbers (backwards compatibility)."""
        from src.utils.time_parser import parse_time_to_seconds
        
        assert parse_time_to_seconds("60") == 60
        assert parse_time_to_seconds("3600") == 3600
        assert parse_time_to_seconds("0") == 0
    
    @patch.object(policy_manager, 'create_policy')
    def test_restart_policy_with_custom_delay(self, mock_create_policy):
        """Test creating restart policy with custom delay format."""
        result = self.runner.invoke(cli, [
            'restart-policy',
            'create',
            '--name', 'custom-delay',
            '--delay', '5h',
            '--max-retries', '3'
        ])
        
        assert result.exit_code == 0
        mock_create_policy.assert_called_once()
        call_args = mock_create_policy.call_args[1]
        assert call_args['name'] == 'custom-delay'
        assert call_args['retry_delay'] == 18000  # 5 hours in seconds
        assert call_args['max_retries'] == 3
    
    @patch.object(process_manager, 'start_process')
    @patch.object(policy_manager, 'create_policy')
    @patch.object(policy_manager, 'apply_policy')
    def test_start_process_with_custom_restart_delay(self, mock_apply, mock_create, mock_start):
        """Test starting a process with custom restart delay."""
        mock_start.return_value = ProcessInfo(
            name="delayed-process",
            command="./script.sh",
            args=[],
            status=ProcessStatus.RUNNING,
            pid=12345,
            started_at=datetime.now(),
            restart_count=0
        )
        
        result = self.runner.invoke(cli, [
            'start',
            '-n', 'delayed-process',
            '-c', './script.sh',
            '--restart-delay', '2h30m',
            '--restart-policy', 'custom'
        ])
        
        assert result.exit_code == 0
        
        # Check that a custom policy was created with the right delay
        mock_create.assert_called()
        create_args = mock_create.call_args[1]
        assert create_args['retry_delay'] == 9000  # 2.5 hours in seconds
    
    @patch.object(process_manager, 'stop_process')
    @patch.object(process_manager, 'start_process')
    @patch('src.cli.main.get_session')
    @patch('time.sleep')
    def test_restart_command_with_delay(self, mock_sleep, mock_get_session, mock_start, mock_stop):
        """Test restart command with custom delay."""
        # Mock database session
        mock_session = MagicMock()
        mock_process = MagicMock()
        mock_process.name = 'test-process'
        mock_process.command = './script.sh'
        mock_process.args = []
        mock_process.working_dir = None
        mock_process.env_vars = {}
        mock_process.group_name = None
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_process
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_start.return_value = ProcessInfo(
            name="test-process",
            command="./script.sh",
            args=[],
            status=ProcessStatus.RUNNING,
            pid=67890,
            started_at=datetime.now(),
            restart_count=1
        )
        
        result = self.runner.invoke(cli, [
            'restart',
            'test-process',
            '--delay', '30s'
        ])
        
        assert result.exit_code == 0
        mock_stop.assert_called_once_with('test-process', force=False)
        mock_sleep.assert_called_once_with(30.0)
        mock_start.assert_called_once()