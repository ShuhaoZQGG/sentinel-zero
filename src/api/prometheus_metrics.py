"""Prometheus metrics exporter for SentinelZero"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from prometheus_client.core import CollectorRegistry
from fastapi import Response
from sqlalchemy.orm import Session
from datetime import datetime
import psutil
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process, Schedule, get_session

# Create a custom registry
registry = CollectorRegistry()

# Process metrics
processes_total = Gauge(
    'sentinelzero_processes_total',
    'Total number of managed processes',
    registry=registry
)

processes_running = Gauge(
    'sentinelzero_processes_running',
    'Number of currently running processes',
    registry=registry
)

processes_failed = Gauge(
    'sentinelzero_processes_failed',
    'Number of failed processes',
    registry=registry
)

process_cpu_usage = Gauge(
    'sentinelzero_process_cpu_percent',
    'CPU usage percentage per process',
    ['process_name', 'process_id'],
    registry=registry
)

process_memory_usage = Gauge(
    'sentinelzero_process_memory_mb',
    'Memory usage in MB per process',
    ['process_name', 'process_id'],
    registry=registry
)

process_restart_count = Counter(
    'sentinelzero_process_restarts_total',
    'Total number of process restarts',
    ['process_name', 'process_id'],
    registry=registry
)

process_uptime = Gauge(
    'sentinelzero_process_uptime_seconds',
    'Process uptime in seconds',
    ['process_name', 'process_id'],
    registry=registry
)

# Schedule metrics
schedules_total = Gauge(
    'sentinelzero_schedules_total',
    'Total number of schedules',
    registry=registry
)

schedules_enabled = Gauge(
    'sentinelzero_schedules_enabled',
    'Number of enabled schedules',
    registry=registry
)

schedule_executions = Counter(
    'sentinelzero_schedule_executions_total',
    'Total number of schedule executions',
    ['schedule_name', 'schedule_id'],
    registry=registry
)

schedule_next_run = Gauge(
    'sentinelzero_schedule_next_run_timestamp',
    'Timestamp of next schedule run',
    ['schedule_name', 'schedule_id'],
    registry=registry
)

# System metrics
system_cpu_usage = Gauge(
    'sentinelzero_system_cpu_percent',
    'System CPU usage percentage',
    registry=registry
)

system_memory_usage = Gauge(
    'sentinelzero_system_memory_percent',
    'System memory usage percentage',
    registry=registry
)

system_memory_available = Gauge(
    'sentinelzero_system_memory_available_mb',
    'Available system memory in MB',
    registry=registry
)

system_disk_usage = Gauge(
    'sentinelzero_system_disk_percent',
    'System disk usage percentage',
    registry=registry
)

system_uptime = Gauge(
    'sentinelzero_system_uptime_seconds',
    'System uptime in seconds',
    registry=registry
)

# Service info
service_info = Info(
    'sentinelzero_service',
    'SentinelZero service information',
    registry=registry
)

# API metrics
api_requests = Counter(
    'sentinelzero_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

api_request_duration = Histogram(
    'sentinelzero_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)


def update_metrics(db: Session = None):
    """Update Prometheus metrics from database"""
    if not db:
        db = next(get_session())
    
    try:
        # Update process metrics
        processes = db.query(Process).all()
        total_processes = len(processes)
        running_processes = 0
        failed_processes = 0
        
        for process in processes:
            if process.status == 'running':
                running_processes += 1
                
                # Get process metrics if available
                try:
                    if process.pid:
                        p = psutil.Process(process.pid)
                        cpu_percent = p.cpu_percent(interval=0.1)
                        memory_info = p.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)
                        
                        process_cpu_usage.labels(
                            process_name=process.name,
                            process_id=str(process.id)
                        ).set(cpu_percent)
                        
                        process_memory_usage.labels(
                            process_name=process.name,
                            process_id=str(process.id)
                        ).set(memory_mb)
                        
                        # Calculate uptime
                        if process.started_at:
                            uptime = (datetime.utcnow() - process.started_at).total_seconds()
                            process_uptime.labels(
                                process_name=process.name,
                                process_id=str(process.id)
                            ).set(uptime)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            elif process.status == 'failed':
                failed_processes += 1
            
            # Update restart count
            if process.restart_count > 0:
                process_restart_count.labels(
                    process_name=process.name,
                    process_id=str(process.id)
                )._value.set(process.restart_count)
        
        processes_total.set(total_processes)
        processes_running.set(running_processes)
        processes_failed.set(failed_processes)
        
        # Update schedule metrics
        schedules = db.query(Schedule).all()
        total_schedules = len(schedules)
        enabled_schedules = sum(1 for s in schedules if s.enabled)
        
        schedules_total.set(total_schedules)
        schedules_enabled.set(enabled_schedules)
        
        for schedule in schedules:
            if schedule.run_count > 0:
                schedule_executions.labels(
                    schedule_name=schedule.name,
                    schedule_id=str(schedule.id)
                )._value.set(schedule.run_count)
            
            if schedule.next_run:
                next_run_timestamp = schedule.next_run.timestamp()
                schedule_next_run.labels(
                    schedule_name=schedule.name,
                    schedule_id=str(schedule.id)
                ).set(next_run_timestamp)
        
        # Update system metrics
        system_cpu_usage.set(psutil.cpu_percent(interval=0.1))
        
        memory = psutil.virtual_memory()
        system_memory_usage.set(memory.percent)
        system_memory_available.set(memory.available / (1024 * 1024))
        
        disk = psutil.disk_usage('/')
        system_disk_usage.set(disk.percent)
        
        boot_time = psutil.boot_time()
        system_uptime.set(datetime.now().timestamp() - boot_time)
        
        # Update service info
        service_info.info({
            'version': '1.0.0',
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        })
        
    except Exception as e:
        print(f"Error updating Prometheus metrics: {e}")
    finally:
        if db:
            db.close()


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format"""
    update_metrics()
    return generate_latest(registry)


async def metrics_endpoint() -> Response:
    """FastAPI endpoint for Prometheus metrics"""
    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4"
    )