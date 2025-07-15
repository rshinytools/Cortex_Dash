# ABOUTME: Unit tests for WebSocketManager
# ABOUTME: Tests WebSocket connection management and message broadcasting

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import json
from fastapi import WebSocket
from app.core.websocket_manager import WebSocketManager


@pytest.fixture
def manager():
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestConnectionManagement:
    @pytest.mark.asyncio
    async def test_connect_study(self, manager, mock_websocket):
        study_id = "study123"
        user_id = "user456"
        
        # Connect
        await manager.connect_study(study_id, user_id, mock_websocket)
        
        # Verify
        assert study_id in manager.study_connections
        assert user_id in manager.study_connections[study_id]
        assert manager.study_connections[study_id][user_id] == mock_websocket
        
    @pytest.mark.asyncio
    async def test_connect_multiple_users(self, manager, mock_websocket):
        study_id = "study123"
        websocket1 = Mock(spec=WebSocket)
        websocket2 = Mock(spec=WebSocket)
        
        # Connect multiple users
        await manager.connect_study(study_id, "user1", websocket1)
        await manager.connect_study(study_id, "user2", websocket2)
        
        # Verify
        assert len(manager.study_connections[study_id]) == 2
        assert manager.study_connections[study_id]["user1"] == websocket1
        assert manager.study_connections[study_id]["user2"] == websocket2
        
    @pytest.mark.asyncio
    async def test_disconnect_study(self, manager, mock_websocket):
        study_id = "study123"
        user_id = "user456"
        
        # Connect then disconnect
        await manager.connect_study(study_id, user_id, mock_websocket)
        manager.disconnect_study(study_id, user_id)
        
        # Verify disconnection
        assert study_id not in manager.study_connections
        
    @pytest.mark.asyncio
    async def test_disconnect_preserves_other_users(self, manager):
        study_id = "study123"
        websocket1 = Mock(spec=WebSocket)
        websocket2 = Mock(spec=WebSocket)
        
        # Connect two users
        await manager.connect_study(study_id, "user1", websocket1)
        await manager.connect_study(study_id, "user2", websocket2)
        
        # Disconnect one
        manager.disconnect_study(study_id, "user1")
        
        # Verify other user remains
        assert study_id in manager.study_connections
        assert "user2" in manager.study_connections[study_id]
        assert "user1" not in manager.study_connections[study_id]


class TestBroadcasting:
    @pytest.mark.asyncio
    async def test_broadcast_to_study(self, manager, mock_websocket):
        study_id = "study123"
        user_id = "user456"
        message = {"type": "progress", "value": 50}
        
        # Connect and broadcast
        await manager.connect_study(study_id, user_id, mock_websocket)
        await manager.broadcast_to_study(study_id, message)
        
        # Verify message sent
        mock_websocket.send_json.assert_called_once_with(message)
        
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_users(self, manager):
        study_id = "study123"
        websocket1 = Mock(spec=WebSocket)
        websocket1.send_json = AsyncMock()
        websocket2 = Mock(spec=WebSocket)
        websocket2.send_json = AsyncMock()
        
        message = {"type": "status", "value": "completed"}
        
        # Connect multiple users
        await manager.connect_study(study_id, "user1", websocket1)
        await manager.connect_study(study_id, "user2", websocket2)
        
        # Broadcast
        await manager.broadcast_to_study(study_id, message)
        
        # Verify both received
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
        
    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_study(self, manager):
        # Should not raise error
        await manager.broadcast_to_study("nonexistent", {"test": "message"})
        
    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connection(self, manager):
        study_id = "study123"
        
        # Create websocket that fails to send
        failing_websocket = Mock(spec=WebSocket)
        failing_websocket.send_json = AsyncMock(side_effect=Exception("Connection closed"))
        
        # Connect
        await manager.connect_study(study_id, "user1", failing_websocket)
        
        # Broadcast should handle error gracefully
        await manager.broadcast_to_study(study_id, {"test": "message"})
        
        # User should be disconnected
        assert study_id not in manager.study_connections


class TestUserSpecificMessages:
    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        study_id = "study123"
        user_id = "user456"
        message = {"type": "personal", "data": "test"}
        
        # Connect
        await manager.connect_study(study_id, user_id, mock_websocket)
        
        # Send to specific user
        await manager.send_to_user(study_id, user_id, message)
        
        # Verify
        mock_websocket.send_json.assert_called_once_with(message)
        
    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, manager):
        # Should not raise error
        await manager.send_to_user("study123", "nonexistent", {"test": "message"})


class TestConnectionState:
    def test_get_study_connections(self, manager):
        manager.study_connections = {
            "study1": {"user1": Mock(), "user2": Mock()},
            "study2": {"user3": Mock()}
        }
        
        # Test getting connections
        assert manager.get_study_connections("study1") == ["user1", "user2"]
        assert manager.get_study_connections("study2") == ["user3"]
        assert manager.get_study_connections("nonexistent") == []
        
    def test_is_user_connected(self, manager):
        manager.study_connections = {
            "study1": {"user1": Mock()}
        }
        
        assert manager.is_user_connected("study1", "user1") == True
        assert manager.is_user_connected("study1", "user2") == False
        assert manager.is_user_connected("study2", "user1") == False


class TestProgressUpdates:
    @pytest.mark.asyncio
    async def test_send_progress_update(self, manager, mock_websocket):
        study_id = "study123"
        user_id = "user456"
        
        # Connect
        await manager.connect_study(study_id, user_id, mock_websocket)
        
        # Send progress update
        await manager.send_progress_update(
            study_id,
            step="data_conversion",
            progress=75,
            message="Converting files..."
        )
        
        # Verify message format
        mock_websocket.send_json.assert_called_once()
        sent_message = mock_websocket.send_json.call_args[0][0]
        assert sent_message["type"] == "progress"
        assert sent_message["step"] == "data_conversion"
        assert sent_message["progress"] == 75
        assert sent_message["message"] == "Converting files..."


class TestCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_empty_studies(self, manager):
        study_id = "study123"
        websocket = Mock(spec=WebSocket)
        
        # Connect and disconnect
        await manager.connect_study(study_id, "user1", websocket)
        manager.disconnect_study(study_id, "user1")
        
        # Verify study removed when empty
        assert study_id not in manager.study_connections
        
    @pytest.mark.asyncio
    async def test_cleanup_all_connections(self, manager):
        # Setup multiple connections
        await manager.connect_study("study1", "user1", Mock())
        await manager.connect_study("study1", "user2", Mock())
        await manager.connect_study("study2", "user3", Mock())
        
        # Clear all
        manager.clear_all_connections()
        
        # Verify all cleared
        assert len(manager.study_connections) == 0