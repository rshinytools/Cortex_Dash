# ABOUTME: WebSocket manager for real-time dashboard updates
# ABOUTME: Handles WebSocket connections and broadcasts updates to connected clients

from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime

from app.core.logging import logger

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by study_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store user connections
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        
    async def connect(
        self,
        websocket: WebSocket,
        study_id: str,
        user_id: str,
        client_id: str
    ):
        """Accept new WebSocket connection"""
        
        await websocket.accept()
        
        # Add to study connections
        if study_id not in self.active_connections:
            self.active_connections[study_id] = set()
        self.active_connections[study_id].add(websocket)
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "study_id": study_id,
            "user_id": user_id,
            "client_id": client_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"WebSocket connected: user={user_id}, study={study_id}, client={client_id}")
        
        # Send connection confirmation
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
        """Remove WebSocket connection"""
        
        metadata = self.connection_metadata.get(websocket)
        
        if metadata:
            study_id = metadata["study_id"]
            user_id = metadata["user_id"]
            
            # Remove from study connections
            if study_id in self.active_connections:
                self.active_connections[study_id].discard(websocket)
                if not self.active_connections[study_id]:
                    del self.active_connections[study_id]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected: user={user_id}, study={study_id}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific connection"""
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_study(self, study_id: str, message: dict):
        """Broadcast message to all connections for a study"""
        
        if study_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[study_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to study {study_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to all connections for a user"""
        
        if user_id in self.user_connections:
            disconnected = []
            
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def broadcast_dashboard_update(
        self,
        study_id: str,
        dashboard_id: str,
        update_type: str,
        data: dict
    ):
        """Broadcast dashboard update to relevant connections"""
        
        message = {
            "type": "dashboard_update",
            "dashboard_id": dashboard_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_study(study_id, message)
    
    async def broadcast_widget_update(
        self,
        study_id: str,
        widget_id: str,
        data: dict
    ):
        """Broadcast widget data update"""
        
        message = {
            "type": "widget_update",
            "widget_id": widget_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_study(study_id, message)
    
    async def broadcast_data_refresh(
        self,
        study_id: str,
        status: str,
        details: dict
    ):
        """Broadcast data refresh status"""
        
        message = {
            "type": "data_refresh",
            "status": status,  # started, progress, completed, failed
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_study(study_id, message)
    
    async def broadcast_notification(
        self,
        user_id: str,
        notification: dict
    ):
        """Broadcast notification to user"""
        
        message = {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_user(user_id, message)
    
    def get_connection_count(self, study_id: str = None) -> int:
        """Get count of active connections"""
        
        if study_id:
            return len(self.active_connections.get(study_id, set()))
        
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_users(self, study_id: str) -> List[str]:
        """Get list of connected users for a study"""
        
        users = []
        
        if study_id in self.active_connections:
            for connection in self.active_connections[study_id]:
                metadata = self.connection_metadata.get(connection)
                if metadata:
                    users.append(metadata["user_id"])
        
        return list(set(users))  # Remove duplicates

# Global connection manager instance
manager = ConnectionManager()