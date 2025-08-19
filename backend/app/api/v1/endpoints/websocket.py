# ABOUTME: WebSocket endpoints for real-time communication
# ABOUTME: Handles study initialization progress and other real-time updates

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlmodel import Session
import logging
import uuid
from typing import Optional

from app.api.deps import get_db, get_current_user_ws
from app.models import User, Study
from app.core.websocket_manager import websocket_manager
from app.core.permissions import has_permission_for_study
from app.core.db import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/studies/{study_id}/initialization")
async def websocket_initialization_endpoint(
    websocket: WebSocket,
    study_id: uuid.UUID,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for study initialization progress updates.
    
    Authentication is done via query parameter since WebSocket doesn't support headers well.
    
    Message types sent to client:
    - connection: Initial connection confirmation
    - progress: Progress updates with current step and percentage
    - status_change: When initialization status changes
    - error: Error messages
    - complete: When initialization is complete
    """
    db: Session = Session(engine)
    
    try:
        # Authenticate user via token
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user = await get_current_user_ws(token, db)
        if not user:
            logger.error(f"WebSocket auth failed: No user found for token")
            await websocket.close(code=4001, reason="Invalid authentication")
            return
        
        logger.info(f"WebSocket auth: User {user.email} (superuser: {user.is_superuser})")
        
        # Check if user has access to the study
        study = db.get(Study, study_id)
        if not study:
            logger.error(f"WebSocket: Study {study_id} not found")
            await websocket.close(code=4004, reason="Study not found")
            return
        
        logger.info(f"WebSocket: Study found - {study.name} (org: {study.org_id})")
        
        has_access = await has_permission_for_study(user, study, db)
        logger.info(f"WebSocket: Permission check result: {has_access}")
        
        if not has_access:
            logger.error(f"WebSocket: Access denied for user {user.email} to study {study_id}")
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, str(study_id), str(user.id))
        
        # Send current initialization status
        await websocket.send_json({
            "type": "current_status",
            "initialization_status": study.initialization_status,
            "initialization_progress": study.initialization_progress,
            "initialization_steps": study.initialization_steps
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client (can be ping/pong)
                data = await websocket.receive_json()
                
                # Handle different message types from client
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "request_status":
                    # Re-fetch and send current status
                    db.refresh(study)
                    await websocket.send_json({
                        "type": "current_status",
                        "initialization_status": study.initialization_status,
                        "initialization_progress": study.initialization_progress,
                        "initialization_steps": study.initialization_steps
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket communication: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error for study {study_id}: {e}")
        await websocket.close(code=4000, reason="Internal error")
    
    finally:
        # Disconnect from manager
        websocket_manager.disconnect(websocket)
        db.close()


@router.websocket("/ws/studies/{study_id}/updates")
async def websocket_general_updates(
    websocket: WebSocket,
    study_id: uuid.UUID,
    token: Optional[str] = Query(None)
):
    """
    General WebSocket endpoint for study updates (data refresh, new uploads, etc.)
    
    Message types:
    - data_refresh: When study data is refreshed
    - upload_complete: When a new data upload is processed
    - mapping_update: When field mappings are updated
    - dashboard_update: When dashboard configuration changes
    """
    db: Session = Session(engine)
    
    try:
        # Similar authentication flow
        if not token:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication")
            return
        
        study = db.get(Study, study_id)
        if not study:
            await websocket.close(code=4004, reason="Study not found")
            return
        
        if not await has_permission_for_study(user, study, db):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager with different channel
        await websocket_manager.connect(websocket, f"{study_id}_updates", str(user.id))
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket communication: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error for study {study_id} updates: {e}")
        await websocket.close(code=4000, reason="Internal error")
    
    finally:
        websocket_manager.disconnect(websocket)
        db.close()


# Import engine for session creation
from app.core.db import engine