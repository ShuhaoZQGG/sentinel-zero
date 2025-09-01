"""Integration tests for WebSocket real-time updates."""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch


@pytest.fixture
def client():
    """Create a test client with WebSocket support."""
    return TestClient(app)


class TestWebSocketConnection:
    """Test WebSocket connection and authentication."""
    
    def test_websocket_connect_with_auth(self, client):
        """Test WebSocket connection with authentication."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Send a test message
            websocket.send_json({"type": "ping"})
            
            # Should receive a pong response
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_connect_without_auth(self, client):
        """Test WebSocket connection without authentication."""
        try:
            with client.websocket_connect("/ws") as websocket:
                # Should be rejected
                pass
        except Exception as e:
            # Connection should be refused
            assert "403" in str(e) or "401" in str(e)
    
    def test_websocket_reconnection(self, client):
        """Test WebSocket reconnection handling."""
        # First connection
        with client.websocket_connect("/ws?token=test-token") as ws1:
            ws1.send_json({"type": "ping"})
            data = ws1.receive_json()
            assert data["type"] == "pong"
        
        # Second connection (reconnect)
        with client.websocket_connect("/ws?token=test-token") as ws2:
            ws2.send_json({"type": "ping"})
            data = ws2.receive_json()
            assert data["type"] == "pong"


class TestProcessUpdates:
    """Test real-time process status updates via WebSocket."""
    
    def test_process_start_notification(self, client):
        """Test receiving notification when process starts."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to process updates
            websocket.send_json({
                "type": "subscribe",
                "channel": "processes"
            })
            
            # Simulate process start
            with patch("src.api.websocket.broadcast_event") as mock_broadcast:
                mock_broadcast({
                    "type": "process.started",
                    "data": {
                        "id": "test-123",
                        "name": "test-process",
                        "status": "running",
                        "pid": 12345
                    }
                })
            
            # Should receive the update
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "process.started"
            assert data["data"]["name"] == "test-process"
    
    def test_process_stop_notification(self, client):
        """Test receiving notification when process stops."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to process updates
            websocket.send_json({
                "type": "subscribe",
                "channel": "processes"
            })
            
            # Simulate process stop
            with patch("src.api.websocket.broadcast_event") as mock_broadcast:
                mock_broadcast({
                    "type": "process.stopped",
                    "data": {
                        "id": "test-123",
                        "name": "test-process",
                        "status": "stopped",
                        "exit_code": 0
                    }
                })
            
            # Should receive the update
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "process.stopped"
            assert data["data"]["exit_code"] == 0
    
    def test_process_error_notification(self, client):
        """Test receiving notification when process encounters error."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to process updates
            websocket.send_json({
                "type": "subscribe",
                "channel": "processes"
            })
            
            # Simulate process error
            with patch("src.api.websocket.broadcast_event") as mock_broadcast:
                mock_broadcast({
                    "type": "process.error",
                    "data": {
                        "id": "test-123",
                        "name": "test-process",
                        "error": "Process crashed",
                        "exit_code": 1
                    }
                })
            
            # Should receive the error notification
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "process.error"
            assert "crashed" in data["data"]["error"].lower()


class TestMetricsUpdates:
    """Test real-time metrics updates via WebSocket."""
    
    def test_metrics_subscription(self, client):
        """Test subscribing to metrics updates."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to metrics for a specific process
            websocket.send_json({
                "type": "subscribe",
                "channel": "metrics",
                "process_id": "test-123"
            })
            
            # Should receive acknowledgment
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["channel"] == "metrics"
    
    def test_metrics_updates(self, client):
        """Test receiving periodic metrics updates."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to metrics
            websocket.send_json({
                "type": "subscribe",
                "channel": "metrics",
                "process_id": "test-123"
            })
            
            # Simulate metrics update
            with patch("src.api.websocket.broadcast_metrics") as mock_metrics:
                mock_metrics({
                    "process_id": "test-123",
                    "cpu_percent": 25.5,
                    "memory_mb": 128.3,
                    "timestamp": "2024-01-20T10:30:00Z"
                })
            
            # Should receive metrics
            websocket.receive_json()  # Skip subscription confirmation
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "metrics.update"
            assert data["data"]["cpu_percent"] == 25.5


class TestLogStreaming:
    """Test real-time log streaming via WebSocket."""
    
    def test_log_streaming_subscription(self, client):
        """Test subscribing to log streams."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to logs for a process
            websocket.send_json({
                "type": "subscribe",
                "channel": "logs",
                "process_id": "test-123",
                "follow": True
            })
            
            # Should receive acknowledgment
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["channel"] == "logs"
    
    def test_log_streaming_data(self, client):
        """Test receiving log data in real-time."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to logs
            websocket.send_json({
                "type": "subscribe",
                "channel": "logs",
                "process_id": "test-123",
                "follow": True
            })
            
            # Simulate log output
            with patch("src.api.websocket.stream_logs") as mock_logs:
                mock_logs({
                    "process_id": "test-123",
                    "type": "stdout",
                    "line": "Application started successfully",
                    "timestamp": "2024-01-20T10:30:00Z"
                })
            
            # Should receive log line
            websocket.receive_json()  # Skip subscription confirmation
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "log.line"
            assert "started successfully" in data["data"]["line"]


class TestScheduleUpdates:
    """Test real-time schedule updates via WebSocket."""
    
    def test_schedule_execution_notification(self, client):
        """Test receiving notification when scheduled task executes."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Subscribe to schedule updates
            websocket.send_json({
                "type": "subscribe",
                "channel": "schedules"
            })
            
            # Simulate schedule execution
            with patch("src.api.websocket.broadcast_event") as mock_broadcast:
                mock_broadcast({
                    "type": "schedule.executed",
                    "data": {
                        "schedule_id": "sched-123",
                        "process_name": "backup",
                        "execution_time": "2024-01-20T02:00:00Z",
                        "next_run": "2024-01-21T02:00:00Z"
                    }
                })
            
            # Should receive the update
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "schedule.executed"
            assert data["data"]["process_name"] == "backup"


class TestBroadcasting:
    """Test broadcasting to multiple WebSocket clients."""
    
    def test_broadcast_to_multiple_clients(self, client):
        """Test that updates are broadcast to all connected clients."""
        # Connect multiple clients
        with client.websocket_connect("/ws?token=test-token1") as ws1:
            with client.websocket_connect("/ws?token=test-token2") as ws2:
                # Both subscribe to processes
                ws1.send_json({"type": "subscribe", "channel": "processes"})
                ws2.send_json({"type": "subscribe", "channel": "processes"})
                
                # Simulate broadcast event
                with patch("src.api.websocket.broadcast_to_all") as mock_broadcast:
                    mock_broadcast({
                        "type": "system.announcement",
                        "data": {"message": "System maintenance in 5 minutes"}
                    })
                
                # Both should receive the message
                ws1.receive_json()  # Skip subscription confirmation
                ws2.receive_json()  # Skip subscription confirmation
                
                data1 = ws1.receive_json(timeout=1)
                data2 = ws2.receive_json(timeout=1)
                
                assert data1["type"] == "system.announcement"
                assert data2["type"] == "system.announcement"
                assert data1["data"]["message"] == data2["data"]["message"]


class TestErrorHandling:
    """Test WebSocket error handling."""
    
    def test_invalid_message_format(self, client):
        """Test handling of invalid message format."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Send invalid message
            websocket.send_text("not json")
            
            # Should receive error response
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "invalid" in data["message"].lower()
    
    def test_unknown_message_type(self, client):
        """Test handling of unknown message type."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Send unknown message type
            websocket.send_json({"type": "unknown_type"})
            
            # Should receive error response
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "unknown" in data["message"].lower()
    
    def test_subscription_to_invalid_channel(self, client):
        """Test subscription to invalid channel."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Try to subscribe to invalid channel
            websocket.send_json({
                "type": "subscribe",
                "channel": "invalid_channel"
            })
            
            # Should receive error response
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "invalid channel" in data["message"].lower()


class TestHeartbeat:
    """Test WebSocket heartbeat mechanism."""
    
    def test_heartbeat_ping_pong(self, client):
        """Test heartbeat ping-pong mechanism."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data
    
    def test_automatic_heartbeat(self, client):
        """Test automatic heartbeat from server."""
        with client.websocket_connect("/ws?token=test-token") as websocket:
            # Wait for automatic heartbeat
            # Server should send periodic heartbeats
            data = websocket.receive_json(timeout=30)
            assert data["type"] in ["heartbeat", "ping"]