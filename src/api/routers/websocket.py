"""WebSocket router for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import asyncio
import logging
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models.schemas import WebSocketMessage
from models.base import get_session as get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "processes": set(),
            "logs": set(),
            "metrics": set()
        }
    
    async def connect(self, websocket: WebSocket, channel: str = "processes"):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "processes"):
        """Remove a WebSocket connection"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, channel: str = "processes"):
        """Broadcast a message to all connections in a channel"""
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[channel].discard(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/processes")
async def websocket_processes(websocket: WebSocket):
    """WebSocket endpoint for real-time process updates"""
    await manager.connect(websocket, "processes")
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "data": {"status": "connected"},
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_text()
            
            # Parse message
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific process
                    process_id = message.get("process_id")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "data": {"process_id": process_id},
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "data": {"message": "Invalid JSON"},
                        "timestamp": datetime.now().isoformat()
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "processes")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "processes")


@router.websocket("/logs/{process_id}")
async def websocket_logs(websocket: WebSocket, process_id: int):
    """WebSocket endpoint for real-time log streaming"""
    await manager.connect(websocket, f"logs_{process_id}")
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "data": {
                    "status": "connected",
                    "process_id": process_id
                },
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Stream logs (simplified for MVP)
        while True:
            # In production, this would tail the actual log file
            await asyncio.sleep(1)
            
            # Check for client messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                message = json.loads(data)
                
                if message.get("type") == "stop":
                    break
                    
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"logs_{process_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, f"logs_{process_id}")


@router.websocket("/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates"""
    await manager.connect(websocket, "metrics")
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "data": {"status": "connected"},
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Send metrics updates periodically
        while True:
            # In production, this would send actual metrics
            import psutil
            
            metrics = {
                "type": "metrics",
                "data": {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(json.dumps(metrics), websocket)
            await asyncio.sleep(5)  # Send metrics every 5 seconds
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, "metrics")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "metrics")


# Helper functions to broadcast updates from other parts of the application
async def broadcast_process_update(process_id: int, status: str, details: dict = None):
    """Broadcast a process status update to all connected clients"""
    message = json.dumps({
        "type": "process_update",
        "data": {
            "process_id": process_id,
            "status": status,
            "details": details or {}
        },
        "timestamp": datetime.now().isoformat()
    })
    await manager.broadcast(message, "processes")


async def broadcast_log_entry(process_id: int, log_type: str, message: str):
    """Broadcast a new log entry to clients subscribed to a process"""
    log_message = json.dumps({
        "type": "log",
        "data": {
            "process_id": process_id,
            "log_type": log_type,
            "message": message
        },
        "timestamp": datetime.now().isoformat()
    })
    await manager.broadcast(log_message, f"logs_{process_id}")