"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json

from src.api.main import app
from src.api.models.responses import ProcessResponse, ScheduleResponse, SystemStatusResponse
from src.models.models import Process, Schedule, RestartPolicyModel as RestartPolicy


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_process_manager():
    """Mock process manager."""
    with patch('src.api.routers.processes.process_manager') as mock:
        yield mock


@pytest.fixture
def mock_scheduler():
    """Mock scheduler."""
    with patch('src.api.routers.schedules.scheduler') as mock:
        yield mock


class TestProcessEndpoints:
    """Test process management endpoints."""
    
    def test_list_processes(self, client, mock_process_manager):
        """Test GET /api/processes endpoint."""
        # Mock process data
        mock_process = Mock()
        mock_process.id = 1
        mock_process.name = "test_process"
        mock_process.command = "echo test"
        mock_process.status = "running"
        mock_process.pid = 12345
        mock_process.cpu_percent = 5.2
        mock_process.memory_mb = 128.5
        
        mock_process_manager.get_all_processes.return_value = [mock_process]
        
        response = client.get("/api/processes")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_process"
        assert data[0]["status"] == "running"
        assert data[0]["pid"] == 12345
    
    def test_get_process(self, client, mock_process_manager):
        """Test GET /api/processes/{name} endpoint."""
        mock_process = Mock()
        mock_process.id = 1
        mock_process.name = "test_process"
        mock_process.command = "echo test"
        mock_process.status = "running"
        mock_process.pid = 12345
        mock_process.cpu_percent = 5.2
        mock_process.memory_mb = 128.5
        
        mock_process_manager.get_process.return_value = mock_process
        
        response = client.get("/api/processes/test_process")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "test_process"
        assert data["status"] == "running"
    
    def test_get_process_not_found(self, client, mock_process_manager):
        """Test GET /api/processes/{name} with non-existent process."""
        mock_process_manager.get_process.return_value = None
        
        response = client.get("/api/processes/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_start_process(self, client, mock_process_manager):
        """Test POST /api/processes/{name}/start endpoint."""
        mock_process_manager.start_process.return_value = True
        
        response = client.post("/api/processes/test_process/start")
        assert response.status_code == 200
        assert response.json()["message"] == "Process started successfully"
        
        mock_process_manager.start_process.assert_called_once_with("test_process")
    
    def test_stop_process(self, client, mock_process_manager):
        """Test POST /api/processes/{name}/stop endpoint."""
        mock_process_manager.stop_process.return_value = True
        
        response = client.post("/api/processes/test_process/stop")
        assert response.status_code == 200
        assert response.json()["message"] == "Process stopped successfully"
        
        mock_process_manager.stop_process.assert_called_once_with("test_process")
    
    def test_restart_process(self, client, mock_process_manager):
        """Test POST /api/processes/{name}/restart endpoint."""
        mock_process_manager.restart_process.return_value = True
        
        response = client.post("/api/processes/test_process/restart")
        assert response.status_code == 200
        assert response.json()["message"] == "Process restarted successfully"
    
    def test_create_process(self, client, mock_process_manager):
        """Test POST /api/processes endpoint."""
        process_data = {
            "name": "new_process",
            "command": "python script.py",
            "working_directory": "/app",
            "environment": {"KEY": "value"},
            "auto_start": True
        }
        
        mock_process_manager.add_process.return_value = True
        
        response = client.post("/api/processes", json=process_data)
        assert response.status_code == 201
        assert response.json()["message"] == "Process created successfully"
    
    def test_delete_process(self, client, mock_process_manager):
        """Test DELETE /api/processes/{name} endpoint."""
        mock_process_manager.remove_process.return_value = True
        
        response = client.delete("/api/processes/test_process")
        assert response.status_code == 200
        assert response.json()["message"] == "Process deleted successfully"


class TestScheduleEndpoints:
    """Test schedule management endpoints."""
    
    def test_list_schedules(self, client, mock_scheduler):
        """Test GET /api/schedules endpoint."""
        mock_schedule = Mock()
        mock_schedule.id = 1
        mock_schedule.name = "daily_backup"
        mock_schedule.process_name = "backup_script"
        mock_schedule.schedule_type = "cron"
        mock_schedule.cron_expression = "0 2 * * *"
        mock_schedule.enabled = True
        mock_schedule.next_run = "2025-01-02T02:00:00"
        
        mock_scheduler.get_all_schedules.return_value = [mock_schedule]
        
        response = client.get("/api/schedules")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "daily_backup"
        assert data[0]["schedule_type"] == "cron"
    
    def test_get_schedule(self, client, mock_scheduler):
        """Test GET /api/schedules/{name} endpoint."""
        mock_schedule = Mock()
        mock_schedule.id = 1
        mock_schedule.name = "daily_backup"
        mock_schedule.process_name = "backup_script"
        mock_schedule.schedule_type = "cron"
        mock_schedule.cron_expression = "0 2 * * *"
        mock_schedule.enabled = True
        mock_schedule.next_run = "2025-01-02T02:00:00"
        
        mock_scheduler.get_schedule.return_value = mock_schedule
        
        response = client.get("/api/schedules/daily_backup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "daily_backup"
    
    def test_create_schedule(self, client, mock_scheduler):
        """Test POST /api/schedules endpoint."""
        schedule_data = {
            "name": "hourly_task",
            "process_name": "task_script",
            "schedule_type": "interval",
            "interval_seconds": 3600,
            "enabled": True
        }
        
        mock_scheduler.add_schedule.return_value = True
        
        response = client.post("/api/schedules", json=schedule_data)
        assert response.status_code == 201
        assert response.json()["message"] == "Schedule created successfully"
    
    def test_enable_schedule(self, client, mock_scheduler):
        """Test POST /api/schedules/{name}/enable endpoint."""
        mock_scheduler.enable_schedule.return_value = True
        
        response = client.post("/api/schedules/daily_backup/enable")
        assert response.status_code == 200
        assert response.json()["message"] == "Schedule enabled successfully"
    
    def test_disable_schedule(self, client, mock_scheduler):
        """Test POST /api/schedules/{name}/disable endpoint."""
        mock_scheduler.disable_schedule.return_value = True
        
        response = client.post("/api/schedules/daily_backup/disable")
        assert response.status_code == 200
        assert response.json()["message"] == "Schedule disabled successfully"
    
    def test_delete_schedule(self, client, mock_scheduler):
        """Test DELETE /api/schedules/{name} endpoint."""
        mock_scheduler.remove_schedule.return_value = True
        
        response = client.delete("/api/schedules/daily_backup")
        assert response.status_code == 200
        assert response.json()["message"] == "Schedule deleted successfully"


class TestSystemEndpoints:
    """Test system status and health endpoints."""
    
    def test_health_check(self, client):
        """Test GET /api/health endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_system_status(self, client, mock_process_manager, mock_scheduler):
        """Test GET /api/status endpoint."""
        # Mock data
        mock_process_manager.get_all_processes.return_value = [Mock(), Mock()]
        mock_scheduler.get_all_schedules.return_value = [Mock()]
        
        with patch('psutil.cpu_percent', return_value=25.5):
            with patch('psutil.virtual_memory') as mock_mem:
                mock_mem.return_value = Mock(percent=60.0)
                
                response = client.get("/api/status")
                assert response.status_code == 200
                
                data = response.json()
                assert data["total_processes"] == 2
                assert data["total_schedules"] == 1
                assert data["cpu_percent"] == 25.5
                assert data["memory_percent"] == 60.0
    
    def test_logs_endpoint(self, client):
        """Test GET /api/logs endpoint."""
        with patch('src.api.routers.system.get_recent_logs') as mock_logs:
            mock_logs.return_value = [
                {"timestamp": "2025-01-01T10:00:00", "level": "INFO", "message": "Test log"}
            ]
            
            response = client.get("/api/logs?limit=10")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 1
            assert data[0]["message"] == "Test log"


class TestConfigEndpoints:
    """Test configuration management endpoints."""
    
    def test_get_config(self, client):
        """Test GET /api/config endpoint."""
        with patch('src.api.routers.config.config_manager') as mock_cm:
            mock_config = Mock()
            mock_config.export_config.return_value = {
                "global": {"log_level": "INFO"},
                "processes": [],
                "schedules": []
            }
            mock_cm.get_config.return_value = mock_config
            
            response = client.get("/api/config")
            assert response.status_code == 200
            
            data = response.json()
            assert "global" in data
            assert data["global"]["log_level"] == "INFO"
    
    def test_update_config(self, client):
        """Test PUT /api/config endpoint."""
        config_data = {
            "global": {
                "log_level": "DEBUG",
                "api_port": 8080
            }
        }
        
        with patch('src.api.routers.config.config_manager') as mock_cm:
            mock_cm.import_config.return_value = None
            mock_cm.save_config.return_value = None
            
            response = client.put("/api/config", json=config_data)
            assert response.status_code == 200
            assert response.json()["message"] == "Configuration updated successfully"
    
    def test_validate_config(self, client):
        """Test POST /api/config/validate endpoint."""
        with patch('src.api.routers.config.config_manager') as mock_cm:
            mock_cm.validate_config.return_value = []
            
            response = client.post("/api/config/validate")
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert data["errors"] == []
    
    def test_validate_config_with_errors(self, client):
        """Test POST /api/config/validate with validation errors."""
        with patch('src.api.routers.config.config_manager') as mock_cm:
            mock_cm.validate_config.return_value = [
                "Schedule 'test' references non-existent process 'missing'"
            ]
            
            response = client.post("/api/config/validate")
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is False
            assert len(data["errors"]) == 1


class TestRestartPolicyEndpoints:
    """Test restart policy endpoints."""
    
    def test_get_restart_policies(self, client):
        """Test GET /api/restart-policies endpoint."""
        with patch('src.api.routers.restart_policies.get_all_policies') as mock_get:
            mock_policy = Mock()
            mock_policy.process_name = "web_server"
            mock_policy.max_retries = 3
            mock_policy.retry_delay_seconds = 5
            mock_policy.exponential_backoff = True
            
            mock_get.return_value = [mock_policy]
            
            response = client.get("/api/restart-policies")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 1
            assert data[0]["process_name"] == "web_server"
    
    def test_create_restart_policy(self, client):
        """Test POST /api/restart-policies endpoint."""
        policy_data = {
            "process_name": "worker",
            "max_retries": 5,
            "retry_delay_seconds": 10,
            "exponential_backoff": True
        }
        
        with patch('src.api.routers.restart_policies.create_policy') as mock_create:
            mock_create.return_value = True
            
            response = client.post("/api/restart-policies", json=policy_data)
            assert response.status_code == 201
            assert response.json()["message"] == "Restart policy created successfully"