"""Process management module for SentinelZero."""

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil
import structlog

logger = structlog.get_logger()


class ProcessStatus(Enum):
    """Process status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ProcessInfo:
    """Information about a managed process."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    working_dir: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    pid: Optional[int] = None
    status: ProcessStatus = ProcessStatus.STOPPED
    exit_code: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    group: Optional[str] = None
    restart_count: int = 0


class ProcessManager:
    """Manages system processes with monitoring and control capabilities."""
    
    def __init__(self):
        """Initialize the process manager."""
        self._processes: Dict[str, ProcessInfo] = {}
        self._subprocesses: Dict[str, subprocess.Popen] = {}
        self._output_buffers: Dict[str, Dict[str, str]] = {}
        self._lock = threading.RLock()
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self._monitor_thread.start()
        
        logger.info("ProcessManager initialized")
    
    def __del__(self):
        """Cleanup on deletion."""
        self._running = False
        # Stop all processes gracefully
        for name in list(self._processes.keys()):
            try:
                self.stop_process(name, timeout=5)
            except:
                pass
    
    def start_process(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        capture_output: bool = True,
        group: Optional[str] = None
    ) -> ProcessInfo:
        """Start a new process."""
        with self._lock:
            if name in self._processes:
                raise ValueError(f"Process with name '{name}' already exists")
            
            # Create process info
            process_info = ProcessInfo(
                name=name,
                command=command,
                args=args or [],
                working_dir=working_dir,
                env_vars=env_vars or {},
                status=ProcessStatus.STARTING,
                group=group
            )
            
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            # Prepare command
            cmd = [command] + (args or [])
            
            # Set up output capture
            stdout_param = subprocess.PIPE if capture_output else None
            stderr_param = subprocess.PIPE if capture_output else None
            
            try:
                # Start the subprocess
                proc = subprocess.Popen(
                    cmd,
                    stdout=stdout_param,
                    stderr=stderr_param,
                    cwd=working_dir,
                    env=env,
                    start_new_session=True  # Create new process group
                )
                
                # Update process info
                process_info.pid = proc.pid
                process_info.status = ProcessStatus.RUNNING
                process_info.started_at = datetime.now()
                
                # Store references
                self._processes[name] = process_info
                self._subprocesses[name] = proc
                
                # Initialize output buffers
                if capture_output:
                    self._output_buffers[name] = {"stdout": "", "stderr": ""}
                    # Start output capture threads
                    self._start_output_capture(name, proc)
                
                logger.info(f"Started process '{name}' with PID {proc.pid}")
                
                return process_info
                
            except Exception as e:
                process_info.status = ProcessStatus.FAILED
                logger.error(f"Failed to start process '{name}': {e}")
                raise
    
    def stop_process(
        self,
        name: str,
        timeout: int = 10,
        force: bool = False
    ) -> bool:
        """Stop a running process."""
        with self._lock:
            if name not in self._processes:
                raise ValueError(f"Process '{name}' not found")
            
            process_info = self._processes[name]
            
            if process_info.status == ProcessStatus.STOPPED:
                return True
            
            if name not in self._subprocesses:
                # Process already terminated
                process_info.status = ProcessStatus.STOPPED
                return True
            
            proc = self._subprocesses[name]
            process_info.status = ProcessStatus.STOPPING
            
            try:
                if force:
                    # Force kill with SIGKILL
                    proc.kill()
                    logger.info(f"Force killed process '{name}'")
                else:
                    # Graceful termination with SIGTERM
                    proc.terminate()
                    try:
                        proc.wait(timeout=timeout)
                        logger.info(f"Gracefully stopped process '{name}'")
                    except subprocess.TimeoutExpired:
                        # Force kill if timeout exceeded
                        proc.kill()
                        logger.warning(f"Process '{name}' didn't stop gracefully, force killed")
                
                # Update process info
                process_info.status = ProcessStatus.STOPPED
                process_info.stopped_at = datetime.now()
                process_info.exit_code = proc.returncode
                
                # Clean up subprocess reference
                del self._subprocesses[name]
                
                return True
                
            except Exception as e:
                logger.error(f"Error stopping process '{name}': {e}")
                return False
    
    def restart_process(self, name: str) -> ProcessInfo:
        """Restart a process."""
        if name not in self._processes:
            raise ValueError(f"Process '{name}' not found")
        
        # Get process configuration
        process_info = self._processes[name]
        command = process_info.command
        args = process_info.args
        working_dir = process_info.working_dir
        env_vars = process_info.env_vars
        capture_output = name in self._output_buffers
        group = process_info.group
        
        # Increment restart count
        restart_count = process_info.restart_count + 1
        
        # Stop if running
        if process_info.status == ProcessStatus.RUNNING:
            self.stop_process(name)
        
        # Remove old process info
        del self._processes[name]
        
        # Start with same configuration
        new_info = self.start_process(
            name=name,
            command=command,
            args=args,
            working_dir=working_dir,
            env_vars=env_vars,
            capture_output=capture_output,
            group=group
        )
        
        # Restore restart count
        new_info.restart_count = restart_count
        
        return new_info
    
    def get_status(self, name: str) -> ProcessStatus:
        """Get the status of a process."""
        with self._lock:
            if name not in self._processes:
                raise ValueError(f"Process '{name}' not found")
            return self._processes[name].status
    
    def get_process_info(self, name: str) -> Optional[ProcessInfo]:
        """Get detailed information about a process."""
        with self._lock:
            return self._processes.get(name)
    
    def list_processes(self, group: Optional[str] = None) -> List[ProcessInfo]:
        """List all processes, optionally filtered by group."""
        with self._lock:
            processes = list(self._processes.values())
            if group:
                processes = [p for p in processes if p.group == group]
            return processes
    
    def get_process_output(self, name: str) -> Optional[Dict[str, str]]:
        """Get captured output from a process."""
        with self._lock:
            return self._output_buffers.get(name)
    
    def get_process_metrics(self, name: str) -> Optional[Dict[str, Any]]:
        """Get resource metrics for a running process."""
        with self._lock:
            if name not in self._processes:
                raise ValueError(f"Process '{name}' not found")
            
            process_info = self._processes[name]
            
            if process_info.status != ProcessStatus.RUNNING or not process_info.pid:
                return None
            
            try:
                proc = psutil.Process(process_info.pid)
                
                # Get CPU and memory usage
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_info = proc.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                
                return {
                    "cpu_percent": cpu_percent,
                    "memory_mb": round(memory_mb, 2),
                    "num_threads": proc.num_threads(),
                    "status": proc.status(),
                    "create_time": proc.create_time()
                }
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
    
    def get_process_status(self, name: str) -> Optional[ProcessStatus]:
        """Get the current status of a process."""
        with self._lock:
            if name not in self._processes:
                return None
            return self._processes[name].status
    
    def get_process_logs(self, name: str) -> Optional[Dict[str, str]]:
        """Get process logs (alias for get_process_output)."""
        return self.get_process_output(name)
    
    def stop_group(self, group: str) -> None:
        """Stop all processes in a group."""
        with self._lock:
            group_processes = [
                name for name, info in self._processes.items()
                if info.group == group
            ]
            
            for name in group_processes:
                try:
                    self.stop_process(name)
                except Exception as e:
                    logger.error(f"Error stopping process '{name}' in group '{group}': {e}")
    
    def _start_output_capture(self, name: str, proc: subprocess.Popen) -> None:
        """Start threads to capture process output."""
        def capture_stdout():
            if proc.stdout:
                for line in iter(proc.stdout.readline, b''):
                    if not self._running:
                        break
                    decoded = line.decode('utf-8', errors='replace')
                    with self._lock:
                        if name in self._output_buffers:
                            self._output_buffers[name]["stdout"] += decoded
        
        def capture_stderr():
            if proc.stderr:
                for line in iter(proc.stderr.readline, b''):
                    if not self._running:
                        break
                    decoded = line.decode('utf-8', errors='replace')
                    with self._lock:
                        if name in self._output_buffers:
                            self._output_buffers[name]["stderr"] += decoded
        
        # Start capture threads
        threading.Thread(target=capture_stdout, daemon=True).start()
        threading.Thread(target=capture_stderr, daemon=True).start()
    
    def _monitor_processes(self) -> None:
        """Monitor running processes for crashes and status changes."""
        while self._running:
            with self._lock:
                for name, proc in list(self._subprocesses.items()):
                    poll_result = proc.poll()
                    
                    if poll_result is not None:
                        # Process has terminated
                        process_info = self._processes[name]
                        process_info.exit_code = poll_result
                        process_info.stopped_at = datetime.now()
                        
                        if poll_result == 0:
                            process_info.status = ProcessStatus.STOPPED
                            logger.info(f"Process '{name}' exited normally")
                        else:
                            process_info.status = ProcessStatus.FAILED
                            logger.warning(f"Process '{name}' failed with exit code {poll_result}")
                        
                        # Remove from subprocesses
                        del self._subprocesses[name]
            
            time.sleep(0.5)  # Check every 500ms