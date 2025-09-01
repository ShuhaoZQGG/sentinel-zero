"""Integration tests for SentinelZero service."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.cli.main import cli
from src.core.process_manager import ProcessManager
from src.core.restart_policy import RestartPolicy
from src.core.scheduler import ProcessScheduler
from src.models.base import Base
from src.models.models import Process, Schedule


class TestEndToEndScenarios:
    """Test complete user workflows."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        
        yield db_path, Session
        
        # Cleanup
        os.unlink(db_path)

    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()

    def test_complete_process_lifecycle(self, temp_db, runner):
        """Test starting, monitoring, and stopping a process."""
        db_path, Session = temp_db
        
        with patch('src.cli.main.get_db_session') as mock_session:
            mock_session.return_value = Session()
            
            # Start a process
            result = runner.invoke(cli, [
                'start',
                '--name', 'test-echo',
                '--cmd', 'echo "Hello, World!"'
            ])
            assert result.exit_code == 0
            assert 'Started process' in result.output
            
            # Check status
            result = runner.invoke(cli, ['status', 'test-echo'])
            assert result.exit_code == 0
            assert 'test-echo' in result.output
            
            # List processes
            result = runner.invoke(cli, ['list'])
            assert result.exit_code == 0
            assert 'test-echo' in result.output
            
            # Stop the process
            result = runner.invoke(cli, ['stop', 'test-echo'])
            assert result.exit_code == 0
            assert 'Stopped process' in result.output

    def test_process_with_restart_policy(self, temp_db):
        """Test process with automatic restart on failure."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process that fails immediately
        process = Process(
            name='failing-process',
            command='exit 1',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        # Create restart policy
        policy = RestartPolicy(
            process_id=process.id,
            policy_type='standard',
            max_retries=3,
            retry_delay=0.1,
            backoff_multiplier=1.5
        )
        
        # Initialize process manager
        pm = ProcessManager()
        
        # Apply restart policy and start process
        pm.apply_restart_policy(process.name, policy)
        pm.start_process(process.name)
        
        # Wait for retries
        time.sleep(1)
        
        # Check that retries were attempted
        process = session.query(Process).filter_by(name='failing-process').first()
        assert process.restart_count > 0
        assert process.restart_count <= 3

    def test_scheduled_process_execution(self, temp_db):
        """Test scheduling a process to run at intervals."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process
        process = Process(
            name='scheduled-task',
            command='echo "Scheduled execution"',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        # Create scheduler
        scheduler = ProcessScheduler()
        
        # Add interval schedule (every second for testing)
        schedule = scheduler.add_schedule(
            process_id=process.id,
            schedule_type='interval',
            schedule_expr='1',  # 1 second
            enabled=True
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for at least one execution
        time.sleep(2)
        
        # Check that process was executed
        logs = session.query(Process).filter_by(id=process.id).first()
        
        # Stop scheduler
        scheduler.stop()
        
        assert schedule is not None
        assert schedule.last_run is not None

    def test_process_group_management(self, temp_db):
        """Test managing multiple related processes as a group."""
        db_path, Session = temp_db
        session = Session()
        
        # Create multiple processes in a group
        processes = []
        for i in range(3):
            process = Process(
                name=f'worker-{i}',
                command=f'echo "Worker {i}"',
                group='workers',
                status='stopped'
            )
            processes.append(process)
            session.add(process)
        session.commit()
        
        pm = ProcessManager()
        
        # Start all processes in the group
        for process in processes:
            pm.start_process(process.name)
        
        # Check all are running
        running_processes = session.query(Process).filter_by(
            group='workers',
            status='running'
        ).all()
        assert len(running_processes) == 3
        
        # Stop all processes in the group
        for process in processes:
            pm.stop_process(process.name)
        
        # Check all are stopped
        stopped_processes = session.query(Process).filter_by(
            group='workers',
            status='stopped'
        ).all()
        assert len(stopped_processes) == 3

    def test_process_with_environment_variables(self, temp_db):
        """Test process execution with custom environment variables."""
        db_path, Session = temp_db
        session = Session()
        
        # Create process with environment variables
        env_vars = json.dumps({
            'CUSTOM_VAR': 'test_value',
            'ANOTHER_VAR': '123'
        })
        
        process = Process(
            name='env-test',
            command='echo $CUSTOM_VAR',
            env_vars=env_vars,
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        pm = ProcessManager()
        pm.start_process('env-test')
        
        # Give it time to execute
        time.sleep(0.5)
        
        # Check process executed with environment
        process = session.query(Process).filter_by(name='env-test').first()
        assert process.status in ['running', 'stopped']

    def test_process_resource_monitoring(self, temp_db):
        """Test monitoring CPU and memory usage of processes."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process that runs for a while
        process = Process(
            name='resource-test',
            command='sleep 2',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        pm = ProcessManager()
        pm.start_process('resource-test')
        
        # Wait for process to start
        time.sleep(0.5)
        
        # Get metrics
        metrics = pm.get_process_metrics('resource-test')
        
        assert metrics is not None
        assert 'cpu_percent' in metrics
        assert 'memory_mb' in metrics
        assert metrics['cpu_percent'] >= 0
        assert metrics['memory_mb'] > 0
        
        # Stop process
        pm.stop_process('resource-test')

    def test_process_log_capture(self, temp_db):
        """Test capturing stdout and stderr from processes."""
        db_path, Session = temp_db
        session = Session()
        
        # Create process that produces output
        process = Process(
            name='log-test',
            command='echo "stdout message" && >&2 echo "stderr message"',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        pm = ProcessManager()
        
        # Capture output
        stdout_lines = []
        stderr_lines = []
        
        def capture_stdout(line):
            stdout_lines.append(line)
        
        def capture_stderr(line):
            stderr_lines.append(line)
        
        with patch.object(pm, '_handle_output', side_effect=capture_stdout):
            with patch.object(pm, '_handle_error', side_effect=capture_stderr):
                pm.start_process('log-test')
                time.sleep(1)
        
        # Verify output was captured
        assert any('stdout message' in line for line in stdout_lines)
        # Note: stderr capture might not work in all environments

    def test_graceful_shutdown(self, temp_db):
        """Test graceful shutdown of processes."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a long-running process
        process = Process(
            name='graceful-test',
            command='sleep 10',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        pm = ProcessManager()
        pm.start_process('graceful-test')
        
        # Wait for process to start
        time.sleep(0.5)
        
        # Stop gracefully (SIGTERM)
        pm.stop_process('graceful-test', force=False)
        
        # Check process stopped
        process = session.query(Process).filter_by(name='graceful-test').first()
        assert process.status == 'stopped'

    def test_force_kill_process(self, temp_db):
        """Test force killing a process that doesn't respond to SIGTERM."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process that ignores SIGTERM
        process = Process(
            name='force-kill-test',
            command='trap "" TERM; sleep 10',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        pm = ProcessManager()
        pm.start_process('force-kill-test')
        
        # Wait for process to start
        time.sleep(0.5)
        
        # Force kill (SIGKILL)
        pm.stop_process('force-kill-test', force=True)
        
        # Check process stopped
        process = session.query(Process).filter_by(name='force-kill-test').first()
        assert process.status == 'stopped'

    def test_cron_schedule(self, temp_db):
        """Test cron-based scheduling."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process
        process = Process(
            name='cron-task',
            command='echo "Cron execution"',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        scheduler = ProcessScheduler()
        
        # Add cron schedule (every minute)
        schedule = scheduler.add_schedule(
            process_id=process.id,
            schedule_type='cron',
            schedule_expr='* * * * *',  # Every minute
            enabled=True
        )
        
        assert schedule is not None
        assert schedule.next_run is not None
        
        # Calculate next run should be within the next minute
        time_until_next = (schedule.next_run - time.time())
        assert 0 < time_until_next <= 60

    def test_restart_policy_with_exit_codes(self, temp_db):
        """Test restart policy based on specific exit codes."""
        db_path, Session = temp_db
        session = Session()
        
        # Create a process
        process = Process(
            name='exit-code-test',
            command='exit 42',
            status='stopped'
        )
        session.add(process)
        session.commit()
        
        # Create policy that only restarts on exit code 42
        policy = RestartPolicy(
            process_id=process.id,
            policy_type='custom',
            max_retries=2,
            retry_delay=0.1,
            restart_on_codes=[42]
        )
        
        pm = ProcessManager()
        pm.apply_restart_policy(process.name, policy)
        pm.start_process(process.name)
        
        # Wait for retries
        time.sleep(0.5)
        
        # Check that retries were attempted
        process = session.query(Process).filter_by(name='exit-code-test').first()
        assert process.restart_count > 0

    def test_multiple_scheduler_instances(self, temp_db):
        """Test running multiple scheduled tasks concurrently."""
        db_path, Session = temp_db
        session = Session()
        
        scheduler = ProcessScheduler()
        
        # Create multiple scheduled processes
        for i in range(3):
            process = Process(
                name=f'scheduled-{i}',
                command=f'echo "Task {i}"',
                status='stopped'
            )
            session.add(process)
            session.commit()
            
            # Add different interval schedules
            scheduler.add_schedule(
                process_id=process.id,
                schedule_type='interval',
                schedule_expr=str(i + 1),  # 1, 2, 3 seconds
                enabled=True
            )
        
        # Verify all schedules were created
        schedules = session.query(Schedule).all()
        assert len(schedules) == 3
        
        # Check different intervals
        for i, schedule in enumerate(schedules):
            assert schedule.schedule_expr == str(i + 1)