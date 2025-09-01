"""Tests for the process manager module."""

import os
import signal
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.process_manager import ProcessManager, ProcessStatus, ProcessInfo


class TestProcessManager:
    """Test suite for ProcessManager class."""

    @pytest.fixture
    def manager(self):
        """Create a ProcessManager instance for testing."""
        return ProcessManager()

    def test_start_process_success(self, manager):
        """Test starting a process successfully."""
        process_info = manager.start_process(
            name="test-echo",
            command="echo",
            args=["Hello, World!"],
            working_dir="/tmp",
            env_vars={"TEST_VAR": "test_value"}
        )
        
        assert process_info is not None
        assert process_info.name == "test-echo"
        assert process_info.status == ProcessStatus.RUNNING
        assert process_info.pid > 0
        
        # Wait for process to complete
        time.sleep(1)
        
        # Check process completed
        status = manager.get_status("test-echo")
        assert status == ProcessStatus.STOPPED

    def test_start_process_duplicate_name(self, manager):
        """Test that starting a process with duplicate name raises error."""
        manager.start_process("test-process", "sleep", ["1"])
        
        with pytest.raises(ValueError, match="Process with name 'test-process' already exists"):
            manager.start_process("test-process", "echo", ["test"])
        
        # Cleanup
        manager.stop_process("test-process")

    def test_stop_process_success(self, manager):
        """Test stopping a running process."""
        manager.start_process("test-sleep", "sleep", ["10"])
        
        result = manager.stop_process("test-sleep", timeout=5)
        assert result is True
        
        status = manager.get_status("test-sleep")
        assert status == ProcessStatus.STOPPED

    def test_stop_process_force(self, manager):
        """Test force stopping a process."""
        manager.start_process("test-force", "sleep", ["100"])
        
        result = manager.stop_process("test-force", force=True)
        assert result is True
        
        status = manager.get_status("test-force")
        assert status == ProcessStatus.STOPPED

    def test_stop_nonexistent_process(self, manager):
        """Test stopping a process that doesn't exist."""
        with pytest.raises(ValueError, match="Process 'nonexistent' not found"):
            manager.stop_process("nonexistent")

    def test_get_process_info(self, manager):
        """Test retrieving process information."""
        manager.start_process(
            name="test-info",
            command="sleep",
            args=["1"],
            working_dir="/tmp",
            env_vars={"TEST": "value"}
        )
        
        info = manager.get_process_info("test-info")
        assert info is not None
        assert info.name == "test-info"
        assert info.command == "sleep"
        assert info.args == ["1"]
        assert info.working_dir == "/tmp"
        assert info.env_vars == {"TEST": "value"}
        assert info.pid > 0
        assert info.status == ProcessStatus.RUNNING
        
        # Cleanup
        manager.stop_process("test-info")

    def test_list_processes(self, manager):
        """Test listing all processes."""
        # Start multiple processes
        manager.start_process("test-1", "sleep", ["1"])
        manager.start_process("test-2", "sleep", ["1"])
        manager.start_process("test-3", "sleep", ["1"])
        
        processes = manager.list_processes()
        assert len(processes) == 3
        assert all(p.name in ["test-1", "test-2", "test-3"] for p in processes)
        
        # Cleanup
        for name in ["test-1", "test-2", "test-3"]:
            try:
                manager.stop_process(name)
            except:
                pass

    def test_capture_output(self, manager):
        """Test capturing process stdout and stderr."""
        info = manager.start_process(
            name="test-output",
            command="echo",
            args=["Test output"],
            capture_output=True
        )
        
        # Wait for process to complete
        time.sleep(0.1)
        
        output = manager.get_process_output("test-output")
        assert output is not None
        assert "Test output" in output.get("stdout", "")

    def test_process_with_environment_variables(self, manager):
        """Test process execution with custom environment variables."""
        info = manager.start_process(
            name="test-env",
            command="sh",
            args=["-c", "echo $CUSTOM_VAR"],
            env_vars={"CUSTOM_VAR": "custom_value"},
            capture_output=True
        )
        
        # Wait for completion
        time.sleep(0.1)
        
        output = manager.get_process_output("test-env")
        assert "custom_value" in output.get("stdout", "")

    def test_process_monitoring(self, manager):
        """Test monitoring process resource usage."""
        manager.start_process("test-monitor", "sleep", ["2"])
        
        metrics = manager.get_process_metrics("test-monitor")
        assert metrics is not None
        assert "cpu_percent" in metrics
        assert "memory_mb" in metrics
        assert metrics["cpu_percent"] >= 0
        assert metrics["memory_mb"] > 0
        
        # Cleanup
        manager.stop_process("test-monitor")

    def test_process_crash_detection(self, manager):
        """Test detection of process crashes."""
        # Start a process that will exit with error
        manager.start_process(
            name="test-crash",
            command="sh",
            args=["-c", "exit 1"]
        )
        
        # Wait for process to exit
        time.sleep(0.5)
        
        status = manager.get_status("test-crash")
        assert status == ProcessStatus.FAILED
        
        info = manager.get_process_info("test-crash")
        assert info.exit_code == 1

    def test_restart_process(self, manager):
        """Test restarting a process."""
        # Start initial process
        info1 = manager.start_process("test-restart", "sleep", ["1"])
        pid1 = info1.pid
        
        # Wait for it to complete
        time.sleep(1.1)
        
        # Restart the process
        info2 = manager.restart_process("test-restart")
        pid2 = info2.pid
        
        assert pid1 != pid2
        assert info2.status == ProcessStatus.RUNNING
        
        # Cleanup
        manager.stop_process("test-restart")

    def test_process_group_management(self, manager):
        """Test managing processes as groups."""
        # Start processes in same group
        manager.start_process("group-1", "sleep", ["1"], group="test-group")
        manager.start_process("group-2", "sleep", ["1"], group="test-group")
        manager.start_process("group-3", "sleep", ["1"], group="test-group")
        
        # List processes in group
        group_processes = manager.list_processes(group="test-group")
        assert len(group_processes) == 3
        
        # Stop all processes in group
        manager.stop_group("test-group")
        
        # Verify all stopped
        for name in ["group-1", "group-2", "group-3"]:
            assert manager.get_status(name) == ProcessStatus.STOPPED

    def test_working_directory(self, manager):
        """Test process execution in specific working directory."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file in temp directory
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test content")
            
            # Start process that lists files in working directory
            manager.start_process(
                name="test-cwd",
                command="ls",
                args=["-la"],
                working_dir=tmpdir,
                capture_output=True
            )
            
            # Wait for completion
            time.sleep(0.1)
            
            output = manager.get_process_output("test-cwd")
            assert "test.txt" in output.get("stdout", "")