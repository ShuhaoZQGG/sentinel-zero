"""Integration tests for process management API endpoints."""

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app
import json
import time


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing."""
    # For testing, we'll mock authentication
    # In production, this would use real auth
    with patch("src.api.middleware.auth_db.verify_token"):
        return {"Authorization": "Bearer test-token"}


class TestProcessLifecycle:
    """Test complete process lifecycle through API."""
    
    def test_create_process(self, client, auth_headers):
        """Test creating a new process."""
        process_data = {
            "name": "test-process",
            "command": "echo 'Hello World'",
            "working_directory": "/tmp",
            "environment": {"TEST_VAR": "test_value"},
            "restart_policy": {
                "max_retries": 3,
                "delay": 5,
                "backoff_multiplier": 1.5
            }
        }
        
        response = client.post(
            "/api/processes",
            json=process_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-process"
        assert data["command"] == "echo 'Hello World'"
        assert "id" in data
        return data["id"]
    
    def test_start_process(self, client, auth_headers):
        """Test starting a process."""
        # Create process first
        process_id = self.test_create_process(client, auth_headers)
        
        # Start the process
        response = client.post(
            f"/api/processes/{process_id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "pid" in data
    
    def test_stop_process(self, client, auth_headers):
        """Test stopping a running process."""
        # Create and start process
        process_id = self.test_create_process(client, auth_headers)
        client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        
        # Stop the process
        response = client.post(
            f"/api/processes/{process_id}/stop",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
    
    def test_restart_process(self, client, auth_headers):
        """Test restarting a process."""
        # Create and start process
        process_id = self.test_create_process(client, auth_headers)
        client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        
        # Restart the process
        response = client.post(
            f"/api/processes/{process_id}/restart",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["restart_count"] >= 1
    
    def test_delete_process(self, client, auth_headers):
        """Test deleting a process."""
        # Create process
        process_id = self.test_create_process(client, auth_headers)
        
        # Delete the process
        response = client.delete(
            f"/api/processes/{process_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify it's deleted
        response = client.get(f"/api/processes/{process_id}", headers=auth_headers)
        assert response.status_code == 404


class TestProcessMonitoring:
    """Test process monitoring endpoints."""
    
    def test_get_process_status(self, client, auth_headers):
        """Test getting process status."""
        # Create and start process
        process_data = {
            "name": "status-test",
            "command": "sleep 10"
        }
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        process_id = response.json()["id"]
        client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        
        # Get status
        response = client.get(
            f"/api/processes/{process_id}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "cpu_percent" in data
        assert "memory_mb" in data
        assert "uptime" in data
    
    def test_get_process_logs(self, client, auth_headers):
        """Test getting process logs."""
        # Create and start process that generates output
        process_data = {
            "name": "log-test",
            "command": "echo 'Line 1'; echo 'Line 2'; echo 'Line 3'"
        }
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        process_id = response.json()["id"]
        client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        
        # Wait for process to complete
        time.sleep(1)
        
        # Get logs
        response = client.get(
            f"/api/processes/{process_id}/logs",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "stdout" in data
        assert "stderr" in data
        assert len(data["stdout"]) > 0
    
    def test_get_process_metrics(self, client, auth_headers):
        """Test getting process metrics."""
        # Create and start process
        process_data = {
            "name": "metrics-test",
            "command": "sleep 5"
        }
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        process_id = response.json()["id"]
        client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        
        # Get metrics
        response = client.get(
            f"/api/processes/{process_id}/metrics",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "cpu_history" in data
        assert "memory_history" in data
        assert "restart_history" in data


class TestProcessListingAndFiltering:
    """Test process listing and filtering endpoints."""
    
    def test_list_all_processes(self, client, auth_headers):
        """Test listing all processes."""
        # Create multiple processes
        for i in range(3):
            process_data = {
                "name": f"list-test-{i}",
                "command": f"echo {i}"
            }
            client.post("/api/processes", json=process_data, headers=auth_headers)
        
        # List all processes
        response = client.get("/api/processes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("name" in p for p in data)
    
    def test_filter_processes_by_status(self, client, auth_headers):
        """Test filtering processes by status."""
        # Create processes with different statuses
        running_process = {
            "name": "running-filter",
            "command": "sleep 10"
        }
        stopped_process = {
            "name": "stopped-filter",
            "command": "echo done"
        }
        
        # Create and start one process
        response = client.post("/api/processes", json=running_process, headers=auth_headers)
        running_id = response.json()["id"]
        client.post(f"/api/processes/{running_id}/start", headers=auth_headers)
        
        # Create but don't start another
        client.post("/api/processes", json=stopped_process, headers=auth_headers)
        
        # Filter by running status
        response = client.get(
            "/api/processes?status=running",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(p["status"] == "running" for p in data if "status" in p)
    
    def test_search_processes_by_name(self, client, auth_headers):
        """Test searching processes by name."""
        # Create processes with specific names
        process_data = {
            "name": "search-test-unique",
            "command": "echo test"
        }
        client.post("/api/processes", json=process_data, headers=auth_headers)
        
        # Search by name
        response = client.get(
            "/api/processes?search=unique",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("unique" in p["name"] for p in data)


class TestBulkOperations:
    """Test bulk process operations."""
    
    def test_bulk_start_processes(self, client, auth_headers):
        """Test starting multiple processes at once."""
        # Create multiple processes
        process_ids = []
        for i in range(3):
            process_data = {
                "name": f"bulk-start-{i}",
                "command": f"sleep {i+1}"
            }
            response = client.post("/api/processes", json=process_data, headers=auth_headers)
            process_ids.append(response.json()["id"])
        
        # Bulk start
        response = client.post(
            "/api/processes/bulk/start",
            json={"process_ids": process_ids},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["started"] == 3
        assert data["failed"] == 0
    
    def test_bulk_stop_processes(self, client, auth_headers):
        """Test stopping multiple processes at once."""
        # Create and start multiple processes
        process_ids = []
        for i in range(3):
            process_data = {
                "name": f"bulk-stop-{i}",
                "command": f"sleep {i+5}"
            }
            response = client.post("/api/processes", json=process_data, headers=auth_headers)
            pid = response.json()["id"]
            process_ids.append(pid)
            client.post(f"/api/processes/{pid}/start", headers=auth_headers)
        
        # Bulk stop
        response = client.post(
            "/api/processes/bulk/stop",
            json={"process_ids": process_ids},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stopped"] == 3
        assert data["failed"] == 0


class TestProcessGroups:
    """Test process group management."""
    
    def test_create_process_group(self, client, auth_headers):
        """Test creating a process group."""
        # Create processes in the same group
        group_name = "test-group"
        for i in range(2):
            process_data = {
                "name": f"group-member-{i}",
                "command": f"echo {i}",
                "group": group_name
            }
            client.post("/api/processes", json=process_data, headers=auth_headers)
        
        # Get processes by group
        response = client.get(
            f"/api/processes?group={group_name}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p.get("group") == group_name for p in data)
    
    def test_group_operations(self, client, auth_headers):
        """Test operations on process groups."""
        group_name = "operation-group"
        
        # Create group processes
        process_ids = []
        for i in range(2):
            process_data = {
                "name": f"group-op-{i}",
                "command": f"sleep {i+3}",
                "group": group_name
            }
            response = client.post("/api/processes", json=process_data, headers=auth_headers)
            process_ids.append(response.json()["id"])
        
        # Start entire group
        response = client.post(
            f"/api/groups/{group_name}/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Stop entire group
        response = client.post(
            f"/api/groups/{group_name}/stop",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling in process API."""
    
    def test_invalid_process_id(self, client, auth_headers):
        """Test operations with invalid process ID."""
        invalid_id = "nonexistent-id"
        
        response = client.get(f"/api/processes/{invalid_id}", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_invalid_command(self, client, auth_headers):
        """Test creating process with invalid command."""
        process_data = {
            "name": "invalid-cmd",
            "command": "/nonexistent/command"
        }
        
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        # Should create but fail when starting
        process_id = response.json()["id"]
        
        response = client.post(f"/api/processes/{process_id}/start", headers=auth_headers)
        assert response.status_code in [400, 500]
    
    def test_duplicate_process_name(self, client, auth_headers):
        """Test creating process with duplicate name."""
        process_data = {
            "name": "duplicate-name",
            "command": "echo test"
        }
        
        # First should succeed
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Second should fail
        response = client.post("/api/processes", json=process_data, headers=auth_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()