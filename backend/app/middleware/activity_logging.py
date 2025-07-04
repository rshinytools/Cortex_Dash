# ABOUTME: Middleware for automatic activity logging
# ABOUTME: Logs API requests for audit trail and compliance

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import Session
import json
import time
from typing import Callable

from app.core.db import engine
from app.api.deps import get_current_user
from app.crud import activity_log as crud_activity


class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API activities for audit trail"""
    
    # Endpoints to exclude from logging
    EXCLUDED_PATHS = {
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
        "/api/v1/login/access-token",
        "/api/v1/utils/test-email",
    }
    
    # Methods to log
    LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Skip logging for GET requests (too noisy)
        if request.method not in self.LOGGED_METHODS:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get request details
        request_body = None
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode('utf-8')
                # Recreate request with body
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Try to get current user from request state
        user = None
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
        
        # Log activity if we have a user
        if user and response.status_code < 400:
            try:
                # Determine action and resource from path
                path_parts = request.url.path.strip("/").split("/")
                resource_type = None
                resource_id = None
                action = request.method.lower()
                
                # Parse common patterns
                if len(path_parts) >= 3:
                    resource_type = path_parts[2]  # e.g., "organizations", "studies"
                    if len(path_parts) >= 4:
                        resource_id = path_parts[3]
                
                # Map HTTP methods to actions
                action_map = {
                    "POST": "create",
                    "PUT": "update",
                    "PATCH": "update",
                    "DELETE": "delete"
                }
                
                if resource_type:
                    action = f"{action_map.get(request.method, request.method.lower())}_{resource_type.rstrip('s')}"
                
                # Create activity log
                with Session(engine) as db:
                    crud_activity.create_activity_log(
                        db,
                        user=user,
                        action=action,
                        resource_type=resource_type or "api",
                        resource_id=resource_id,
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "duration_ms": round(duration * 1000, 2),
                            "status_code": response.status_code,
                            "query_params": dict(request.query_params) if request.query_params else None,
                        },
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        success=response.status_code < 400
                    )
            except Exception as e:
                # Don't let logging errors break the application
                print(f"Error logging activity: {e}")
        
        return response


async def get_request_user(request: Request):
    """Helper to extract user from request"""
    # This would need to be implemented based on your authentication setup
    # For now, we'll rely on request.state.current_user being set by auth dependencies
    pass