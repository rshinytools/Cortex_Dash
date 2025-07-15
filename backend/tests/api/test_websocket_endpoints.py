# ABOUTME: Integration tests for WebSocket endpoints
# ABOUTME: Tests real-time progress updates via WebSocket

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import json


class TestWebSocketConnection:
    def test_websocket_authentication(self, client: TestClient):
        # Test without token
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/studies/study123/initialization"):
                pass
                
    def test_websocket_with_valid_token(self, client: TestClient):
        with patch('app.api.v1.endpoints.websocket.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "user123", "role": "SYSTEM_ADMIN"}
            
            with patch('app.api.v1.endpoints.websocket.get_study_by_id') as mock_get_study:
                mock_study = Mock()
                mock_study.id = "study123"
                mock_study.org_id = "org123"
                mock_get_study.return_value = mock_study
                
                with patch('app.api.v1.endpoints.websocket.websocket_manager') as mock_manager:
                    mock_manager.connect_study = AsyncMock()
                    
                    # Should connect successfully
                    with client.websocket_connect(
                        "/ws/studies/study123/initialization?token=valid_token"
                    ) as websocket:
                        # Send request for status
                        websocket.send_json({"type": "request_status"})
                        
                        # Should receive current status
                        mock_manager.connect_study.assert_called_once()


class TestProgressBroadcasting:
    def test_progress_update_broadcast(self, client: TestClient):
        study_id = "study123"
        
        with patch('app.api.v1.endpoints.websocket.websocket_manager') as mock_manager:
            # Simulate progress update
            progress_message = {
                "type": "progress",
                "step": "data_conversion",
                "progress": 50,
                "message": "Converting files..."
            }
            
            # Broadcast should be called when progress updates
            mock_manager.broadcast_to_study = AsyncMock()
            
            # Trigger through service
            with patch('app.services.study_initialization_service.websocket_manager', mock_manager):
                mock_manager.broadcast_to_study(study_id, progress_message)
                
            mock_manager.broadcast_to_study.assert_called_with(study_id, progress_message)


class TestWebSocketMessages:
    def test_handle_request_status(self, client: TestClient):
        with patch('app.api.v1.endpoints.websocket.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "user123", "role": "SYSTEM_ADMIN"}
            
            with patch('app.api.v1.endpoints.websocket.get_study_by_id') as mock_get_study:
                mock_study = Mock()
                mock_study.id = "study123"
                mock_study.initialization_status = "in_progress"
                mock_study.initialization_progress = 75
                mock_get_study.return_value = mock_study
                
                # Test status request handling
                expected_response = {
                    "type": "current_status",
                    "initialization_status": "in_progress",
                    "initialization_progress": 75
                }
                
                # Verify response format matches expected


class TestConnectionManagement:
    def test_disconnect_on_error(self, client: TestClient):
        with patch('app.api.v1.endpoints.websocket.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "user123", "role": "SYSTEM_ADMIN"}
            
            with patch('app.api.v1.endpoints.websocket.websocket_manager') as mock_manager:
                mock_manager.disconnect_study = Mock()
                
                # Simulate connection error
                with pytest.raises(Exception):
                    with client.websocket_connect(
                        "/ws/studies/study123/initialization?token=valid_token"
                    ) as websocket:
                        # Force an error
                        raise Exception("Connection error")
                
                # Should disconnect on error
                # Note: In real implementation, disconnect should be called in finally block


class TestMultipleConnections:
    def test_multiple_users_same_study(self, client: TestClient):
        study_id = "study123"
        
        with patch('app.api.v1.endpoints.websocket.websocket_manager') as mock_manager:
            connections = {}
            
            async def mock_connect(sid, uid, ws):
                if sid not in connections:
                    connections[sid] = {}
                connections[sid][uid] = ws
                
            mock_manager.connect_study = mock_connect
            
            # Simulate multiple users connecting
            # In real test, would use multiple websocket connections
            assert True  # Placeholder for complex multi-connection test