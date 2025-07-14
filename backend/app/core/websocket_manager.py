# ABOUTME: WebSocket connection manager for real-time updates
# ABOUTME: Handles study initialization progress broadcasting and connection management

from typing import Dict, List, Set, Optional
import logging
from fastapi import WebSocket, WebSocketDisconnect
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections: {study_id: {user_id: [websocket1, websocket2, ...]}}
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        # Track connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, study_id: str, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        # Initialize study connections if not exists
        if study_id not in self.active_connections:
            self.active_connections[study_id] = {}
        
        # Initialize user connections if not exists
        if user_id not in self.active_connections[study_id]:
            self.active_connections[study_id][user_id] = []
        
        # Add connection
        self.active_connections[study_id][user_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "study_id": study_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"WebSocket connected: study={study_id}, user={user_id}")
        
        # Send initial connection confirmation
        await self.send_personal_message(
            websocket,
            {
                "type": "connection",
                "status": "connected",
                "study_id": study_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        study_id = metadata["study_id"]
        user_id = metadata["user_id"]
        
        # Remove from active connections
        if (study_id in self.active_connections and 
            user_id in self.active_connections[study_id]):
            self.active_connections[study_id][user_id].remove(websocket)
            
            # Clean up empty structures
            if not self.active_connections[study_id][user_id]:
                del self.active_connections[study_id][user_id]
            
            if not self.active_connections[study_id]:
                del self.active_connections[study_id]
        
        # Remove metadata
        del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected: study={study_id}, user={user_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_study(self, study_id: str, message: dict):
        """Broadcast a message to all connections for a specific study"""
        if study_id not in self.active_connections:
            return
        
        disconnected_sockets = []
        
        for user_id, connections in self.active_connections[study_id].items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to study {study_id}, user {user_id}: {e}")
                    disconnected_sockets.append(connection)
        
        # Clean up disconnected sockets
        for socket in disconnected_sockets:
            self.disconnect(socket)
    
    async def broadcast_to_user(self, study_id: str, user_id: str, message: dict):
        """Broadcast a message to all connections for a specific user in a study"""
        if (study_id not in self.active_connections or 
            user_id not in self.active_connections[study_id]):
            return
        
        disconnected_sockets = []
        
        for connection in self.active_connections[study_id][user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id} in study {study_id}: {e}")
                disconnected_sockets.append(connection)
        
        # Clean up disconnected sockets
        for socket in disconnected_sockets:
            self.disconnect(socket)
    
    async def broadcast_progress(self, study_id: str, progress_data: dict):
        """Broadcast initialization progress update to all study connections"""
        message = {
            "type": "progress",
            "timestamp": datetime.utcnow().isoformat(),
            **progress_data
        }
        await self.broadcast_to_study(study_id, message)
    
    async def broadcast_error(self, study_id: str, error_data: dict):
        """Broadcast error message to all study connections"""
        message = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            **error_data
        }
        await self.broadcast_to_study(study_id, message)
    
    async def broadcast_status_change(self, study_id: str, status: str, details: Optional[dict] = None):
        """Broadcast status change to all study connections"""
        message = {
            "type": "status_change",
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **(details or {})
        }
        await self.broadcast_to_study(study_id, message)
    
    def get_connection_count(self, study_id: str) -> int:
        """Get the number of active connections for a study"""
        if study_id not in self.active_connections:
            return 0
        
        count = 0
        for user_connections in self.active_connections[study_id].values():
            count += len(user_connections)
        
        return count
    
    def get_connected_users(self, study_id: str) -> Set[str]:
        """Get the set of user IDs connected to a study"""
        if study_id not in self.active_connections:
            return set()
        
        return set(self.active_connections[study_id].keys())


# Global WebSocket manager instance
websocket_manager = ConnectionManager()