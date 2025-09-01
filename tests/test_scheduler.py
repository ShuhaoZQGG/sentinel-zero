"""Tests for the scheduler module."""

import time
from datetime import datetime, timedelta
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.scheduler import ProcessScheduler, ScheduleType, Schedule


class TestProcessScheduler:
    """Test suite for ProcessScheduler class."""
    
    @pytest.fixture
    def scheduler(self):
        """Create a ProcessScheduler instance for testing."""
        return ProcessScheduler()
    
    @pytest.fixture
    def mock_process_manager(self):
        """Create a mock process manager."""
        mock = Mock()
        mock.start_process = Mock(return_value=Mock(pid=1234))
        mock.get_status = Mock(return_value="stopped")
        return mock
    
    def test_add_cron_schedule(self, scheduler, mock_process_manager):
        """Test adding a cron schedule."""
        scheduler.set_process_manager(mock_process_manager)
        
        schedule = scheduler.add_schedule(
            name="test-cron",
            schedule_type=ScheduleType.CRON,
            expression="0 2 * * *",  # Daily at 2 AM
            command="echo",
            args=["Hello from cron"]
        )
        
        assert schedule is not None
        assert schedule.name == "test-cron"
        assert schedule.schedule_type == ScheduleType.CRON
        assert schedule.expression == "0 2 * * *"
        assert schedule.enabled is True
    
    def test_add_interval_schedule(self, scheduler, mock_process_manager):
        """Test adding an interval schedule."""
        scheduler.set_process_manager(mock_process_manager)
        
        schedule = scheduler.add_schedule(
            name="test-interval",
            schedule_type=ScheduleType.INTERVAL,
            expression="5m",  # Every 5 minutes
            command="python",
            args=["script.py"]
        )
        
        assert schedule is not None
        assert schedule.name == "test-interval"
        assert schedule.schedule_type == ScheduleType.INTERVAL
        assert schedule.expression == "5m"
    
    def test_add_once_schedule(self, scheduler, mock_process_manager):
        """Test adding a one-time schedule."""
        scheduler.set_process_manager(mock_process_manager)
        
        run_at = datetime.now() + timedelta(minutes=10)
        
        schedule = scheduler.add_schedule(
            name="test-once",
            schedule_type=ScheduleType.ONCE,
            expression=run_at.isoformat(),
            command="backup.sh"
        )
        
        assert schedule is not None
        assert schedule.name == "test-once"
        assert schedule.schedule_type == ScheduleType.ONCE
    
    def test_duplicate_schedule_name(self, scheduler, mock_process_manager):
        """Test that duplicate schedule names raise error."""
        scheduler.set_process_manager(mock_process_manager)
        
        scheduler.add_schedule(
            name="test-dup",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="echo"
        )
        
        with pytest.raises(ValueError, match="Schedule with name 'test-dup' already exists"):
            scheduler.add_schedule(
                name="test-dup",
                schedule_type=ScheduleType.CRON,
                expression="0 * * * *",
                command="echo"
            )
    
    def test_remove_schedule(self, scheduler, mock_process_manager):
        """Test removing a schedule."""
        scheduler.set_process_manager(mock_process_manager)
        
        scheduler.add_schedule(
            name="test-remove",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="echo"
        )
        
        result = scheduler.remove_schedule("test-remove")
        assert result is True
        
        # Verify schedule is gone
        schedules = scheduler.list_schedules()
        assert not any(s.name == "test-remove" for s in schedules)
    
    def test_enable_disable_schedule(self, scheduler, mock_process_manager):
        """Test enabling and disabling schedules."""
        scheduler.set_process_manager(mock_process_manager)
        
        schedule = scheduler.add_schedule(
            name="test-toggle",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="echo"
        )
        
        # Initially enabled
        assert schedule.enabled is True
        
        # Disable
        scheduler.disable_schedule("test-toggle")
        schedule = scheduler.get_schedule("test-toggle")
        assert schedule.enabled is False
        
        # Enable
        scheduler.enable_schedule("test-toggle")
        schedule = scheduler.get_schedule("test-toggle")
        assert schedule.enabled is True
    
    def test_list_schedules(self, scheduler, mock_process_manager):
        """Test listing all schedules."""
        scheduler.set_process_manager(mock_process_manager)
        
        # Add multiple schedules
        scheduler.add_schedule("sched-1", ScheduleType.CRON, "* * * * *", "echo")
        scheduler.add_schedule("sched-2", ScheduleType.INTERVAL, "10s", "echo")
        scheduler.add_schedule("sched-3", ScheduleType.ONCE, datetime.now().isoformat(), "echo")
        
        schedules = scheduler.list_schedules()
        assert len(schedules) == 3
        assert all(s.name in ["sched-1", "sched-2", "sched-3"] for s in schedules)
    
    def test_get_next_run(self, scheduler, mock_process_manager):
        """Test getting next run time for schedules."""
        scheduler.set_process_manager(mock_process_manager)
        
        # Add a schedule that runs every minute
        schedule = scheduler.add_schedule(
            name="test-next",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="echo"
        )
        
        next_run = scheduler.get_next_run("test-next")
        assert next_run is not None
        
        # Convert to naive datetime for comparison
        from datetime import timezone
        now = datetime.now(timezone.utc)
        assert next_run > now
        assert (next_run - now).total_seconds() <= 60
    
    def test_interval_parsing(self, scheduler, mock_process_manager):
        """Test parsing of interval expressions."""
        scheduler.set_process_manager(mock_process_manager)
        
        # Test various interval formats
        test_cases = [
            ("10s", 10),      # 10 seconds
            ("5m", 300),      # 5 minutes
            ("2h", 7200),     # 2 hours
            ("1d", 86400),    # 1 day
        ]
        
        for expression, expected_seconds in test_cases:
            schedule = scheduler.add_schedule(
                name=f"test-{expression}",
                schedule_type=ScheduleType.INTERVAL,
                expression=expression,
                command="echo"
            )
            assert schedule is not None
            # Clean up
            scheduler.remove_schedule(f"test-{expression}")
    
    def test_invalid_cron_expression(self, scheduler, mock_process_manager):
        """Test that invalid cron expressions raise error."""
        scheduler.set_process_manager(mock_process_manager)
        
        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler.add_schedule(
                name="bad-cron",
                schedule_type=ScheduleType.CRON,
                expression="invalid cron",
                command="echo"
            )
    
    def test_schedule_execution(self, scheduler, mock_process_manager):
        """Test that schedules execute at the right time."""
        scheduler.set_process_manager(mock_process_manager)
        
        # Add a schedule that runs immediately (every second)
        schedule = scheduler.add_schedule(
            name="test-exec",
            schedule_type=ScheduleType.INTERVAL,
            expression="1s",
            command="echo",
            args=["test"]
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for execution
        time.sleep(2)
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify process was started
        mock_process_manager.start_process.assert_called()
        
    def test_schedule_with_environment_vars(self, scheduler, mock_process_manager):
        """Test schedule with environment variables."""
        scheduler.set_process_manager(mock_process_manager)
        
        schedule = scheduler.add_schedule(
            name="test-env",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="script.sh",
            env_vars={"PATH": "/custom/path", "ENV": "production"}
        )
        
        assert schedule.env_vars == {"PATH": "/custom/path", "ENV": "production"}
    
    def test_schedule_with_working_dir(self, scheduler, mock_process_manager):
        """Test schedule with custom working directory."""
        scheduler.set_process_manager(mock_process_manager)
        
        schedule = scheduler.add_schedule(
            name="test-dir",
            schedule_type=ScheduleType.CRON,
            expression="0 * * * *",
            command="backup.py",
            working_dir="/opt/backups"
        )
        
        assert schedule.working_dir == "/opt/backups"
    
    def test_missed_schedule_handling(self, scheduler, mock_process_manager):
        """Test handling of missed schedule executions."""
        scheduler.set_process_manager(mock_process_manager)
        
        # Add a schedule
        schedule = scheduler.add_schedule(
            name="test-missed",
            schedule_type=ScheduleType.CRON,
            expression="* * * * *",
            command="echo"
        )
        
        # Simulate last run being 5 minutes ago
        schedule.last_run = datetime.now() - timedelta(minutes=5)
        
        # Start scheduler with catch-up disabled
        scheduler.start(catch_up=False)
        time.sleep(0.1)
        scheduler.stop()
        
        # Should only run once, not 5 times
        assert mock_process_manager.start_process.call_count <= 1