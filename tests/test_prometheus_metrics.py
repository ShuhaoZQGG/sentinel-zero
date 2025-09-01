"""Tests for Prometheus metrics"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.prometheus_metrics import (
    processes_total,
    processes_running,
    processes_failed,
    schedules_total,
    schedules_enabled,
    system_cpu_usage,
    system_memory_usage,
    get_metrics,
    update_metrics
)


def test_prometheus_metrics_format():
    """Test that metrics are in Prometheus format"""
    metrics_data = get_metrics()
    assert isinstance(metrics_data, bytes)
    
    # Check for some expected metric names
    metrics_str = metrics_data.decode('utf-8')
    assert 'sentinelzero_processes_total' in metrics_str
    assert 'sentinelzero_processes_running' in metrics_str
    assert 'sentinelzero_system_cpu_percent' in metrics_str


@patch('src.api.prometheus_metrics.get_session')
@patch('src.api.prometheus_metrics.psutil')
def test_update_metrics(mock_psutil, mock_get_session):
    """Test updating metrics from database"""
    # Mock database session
    mock_db = MagicMock()
    mock_get_session.return_value = iter([mock_db])
    
    # Mock process data
    mock_process = MagicMock()
    mock_process.id = 1
    mock_process.name = "test_process"
    mock_process.status = "running"
    mock_process.pid = 1234
    mock_process.restart_count = 2
    mock_process.started_at = None
    
    mock_db.query().all.return_value = [mock_process]
    
    # Mock psutil data
    mock_psutil.cpu_percent.return_value = 25.5
    mock_psutil.virtual_memory.return_value = MagicMock(
        percent=60.0,
        available=4096 * 1024 * 1024
    )
    mock_psutil.disk_usage.return_value = MagicMock(percent=75.0)
    mock_psutil.boot_time.return_value = 1234567890
    
    # Update metrics
    update_metrics(mock_db)
    
    # Verify session was queried
    assert mock_db.query.called


def test_process_metrics_labels():
    """Test that process metrics have correct labels"""
    # Get metrics and check format
    metrics_data = get_metrics()
    metrics_str = metrics_data.decode('utf-8')
    
    # Check for label format in metrics
    if 'sentinelzero_process_cpu_percent{' in metrics_str:
        assert 'process_name=' in metrics_str
        assert 'process_id=' in metrics_str


def test_schedule_metrics_labels():
    """Test that schedule metrics have correct labels"""
    # Get metrics and check format
    metrics_data = get_metrics()
    metrics_str = metrics_data.decode('utf-8')
    
    # Check for label format in metrics
    if 'sentinelzero_schedule_executions_total{' in metrics_str:
        assert 'schedule_name=' in metrics_str
        assert 'schedule_id=' in metrics_str


def test_api_metrics_labels():
    """Test that API metrics have correct labels"""
    from src.api.prometheus_metrics import api_requests, api_request_duration
    
    # Increment a test metric
    api_requests.labels(
        method="GET",
        endpoint="/api/test",
        status_code="200"
    ).inc()
    
    # Record a duration
    api_request_duration.labels(
        method="GET",
        endpoint="/api/test"
    ).observe(0.5)
    
    # Get metrics and verify
    metrics_data = get_metrics()
    metrics_str = metrics_data.decode('utf-8')
    
    assert 'sentinelzero_api_requests_total' in metrics_str
    assert 'sentinelzero_api_request_duration_seconds' in metrics_str


def test_system_metrics():
    """Test system metrics collection"""
    metrics_data = get_metrics()
    metrics_str = metrics_data.decode('utf-8')
    
    # Check for system metrics
    assert 'sentinelzero_system_cpu_percent' in metrics_str
    assert 'sentinelzero_system_memory_percent' in metrics_str
    assert 'sentinelzero_system_memory_available_mb' in metrics_str
    assert 'sentinelzero_system_disk_percent' in metrics_str
    assert 'sentinelzero_system_uptime_seconds' in metrics_str


def test_service_info():
    """Test service info metric"""
    metrics_data = get_metrics()
    metrics_str = metrics_data.decode('utf-8')
    
    # Check for service info
    assert 'sentinelzero_service_info' in metrics_str
    assert 'version=' in metrics_str
    assert 'python_version=' in metrics_str