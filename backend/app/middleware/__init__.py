# ABOUTME: Middleware module for Clinical Dashboard Platform
# ABOUTME: Contains middleware for logging, security, and compliance

from .activity_logging import ActivityLoggingMiddleware

__all__ = ["ActivityLoggingMiddleware"]