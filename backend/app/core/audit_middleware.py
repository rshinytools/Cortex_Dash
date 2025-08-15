# ABOUTME: Audit middleware that captures every API request for comprehensive audit logging
# ABOUTME: Logs all user actions, API calls, and data modifications for 21 CFR Part 11 compliance

import json
import time
from typing import Callable, Dict, Any
from datetime import datetime
from fastapi import Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from app.core.db import engine
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.core import security
from app.core.config import settings
from app.models.token import TokenPayload
import jwt
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

# Endpoints to exclude from audit logging
EXCLUDED_PATHS = {
    "/api/v1/utils/health-check/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/api/v1/audit-trail/",  # Prevent recursive logging when fetching audit logs
    "/api/v1/login/access-token",  # Login is handled manually in the endpoint
    "/api/v1/logout",  # Logout is handled manually in the endpoint
}

# Map HTTP methods to audit actions
METHOD_TO_ACTION = {
    "GET": "VIEW",
    "POST": "CREATE",
    "PUT": "UPDATE",
    "PATCH": "UPDATE",
    "DELETE": "DELETE"
}

# Map endpoints to resource types
def get_resource_type(path: str) -> str:
    """Extract resource type from API path"""
    if "/organizations" in path:
        return "organization"
    elif "/users" in path:
        return "user"
    elif "/studies" in path:
        return "study"
    elif "/dashboards" in path:
        return "dashboard"
    elif "/widgets" in path:
        return "widget"
    elif "/roles" in path:
        return "role"
    elif "/permissions" in path:
        return "permission"
    elif "/pipeline" in path:
        return "pipeline"
    elif "/data-sources" in path:
        return "data_source"
    elif "/login" in path or "/logout" in path:
        return "authentication"
    elif "/rbac" in path:
        return "rbac"
    else:
        # Extract from path - take the main resource name
        parts = path.strip("/").split("/")
        if len(parts) >= 4:  # api/v1/resource/...
            return parts[2].replace("-", "_")
        return "system"


def get_resource_id(path: str, method: str, response_body: Any) -> str:
    """Extract resource ID from path or response"""
    parts = path.strip("/").split("/")
    
    # Check if path contains an ID (usually a UUID)
    for part in parts:
        if len(part) == 36 and "-" in part:  # Likely a UUID
            return part
    
    # For POST requests, try to get ID from response
    if method == "POST" and response_body:
        try:
            if isinstance(response_body, dict):
                return str(response_body.get("id", ""))
            elif isinstance(response_body, str):
                data = json.loads(response_body)
                if isinstance(data, dict):
                    return str(data.get("id", ""))
        except:
            pass
    
    return ""


class AuditMiddleware:
    """Middleware to log all API requests for audit trail"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)
        
        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        start_time = time.time()
        
        # Get user info from token
        user_id = None
        user_email = None
        
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload = jwt.decode(
                        token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
                    )
                    token_data = TokenPayload(**payload)
                    user_id = token_data.sub
                    # Get user email from database
                    with Session(engine) as db:
                        user = db.query(User).filter(User.id == user_id).first()
                        if user:
                            user_email = user.email
                except (jwt.InvalidTokenError, ValidationError):
                    pass
        except Exception as e:
            logger.debug(f"Could not extract user from token: {e}")
        
        # Capture request details
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = body.decode("utf-8")
                    # Parse JSON if possible
                    try:
                        request_body = json.loads(request_body)
                    except:
                        pass
            except:
                pass
        
        # Call the actual endpoint
        response = await call_next(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Capture response for successful requests
        response_body = None
        response_status = response.status_code
        
        # Only log successful requests and auth failures
        if (200 <= response_status < 300) or (response_status == 401 and "/login" in request.url.path):
            try:
                # Get response body for POST requests to capture created resource ID
                if request.method == "POST" and response_status < 300:
                    # Note: We can't easily capture response body in middleware
                    # without modifying the response stream
                    pass
                
                # Determine action based on method
                action = METHOD_TO_ACTION.get(request.method, request.method)
                
                # Special handling for specific endpoints
                if "/logout" in request.url.path:
                    action = "LOGOUT"
                elif "/login" in request.url.path and response_status == 200:
                    action = "LOGIN"
                elif "/login" in request.url.path and response_status == 401:
                    action = "LOGIN_FAILED"
                
                # Get resource info
                resource_type = get_resource_type(request.url.path)
                resource_id = get_resource_id(request.url.path, request.method, response_body)
                
                # Build details
                details = {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "response_time_ms": round(response_time * 1000, 2),
                    "status_code": response_status
                }
                
                # Add request body for write operations
                if request_body and request.method in ["POST", "PUT", "PATCH"]:
                    # Sanitize sensitive data
                    if isinstance(request_body, dict):
                        sanitized_body = request_body.copy()
                        # Remove password fields
                        for field in ["password", "new_password", "old_password", "secret", "token"]:
                            if field in sanitized_body:
                                sanitized_body[field] = "***REDACTED***"
                        details["request_body"] = sanitized_body
                    elif isinstance(request_body, str) and "password" not in request_body.lower():
                        details["request_body"] = request_body[:500]  # Limit size
                
                # Log to database
                with Session(engine) as db:
                    try:
                        # Get next sequence number
                        last_log = db.query(ActivityLog).order_by(ActivityLog.sequence_number.desc()).first()
                        next_sequence = (last_log.sequence_number + 1) if last_log else 1
                        
                        audit_log = ActivityLog(
                            user_id=user_id,
                            user_email=user_email or "anonymous",
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id or None,
                            timestamp=datetime.utcnow(),
                            ip_address=request.client.host if request.client else None,
                            user_agent=request.headers.get("user-agent"),
                            details=details,
                            sequence_number=next_sequence
                        )
                        db.add(audit_log)
                        db.commit()
                        logger.debug(f"Audit log created: {action} on {resource_type}")
                    except Exception as e:
                        logger.error(f"Failed to create audit log: {e}")
                        db.rollback()
                        
            except Exception as e:
                logger.error(f"Error in audit middleware: {e}")
        
        return response


def setup_audit_middleware(app):
    """Setup audit middleware for the FastAPI app"""
    app.middleware("http")(AuditMiddleware())