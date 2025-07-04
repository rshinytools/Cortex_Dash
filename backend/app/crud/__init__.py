# ABOUTME: CRUD operations module for Clinical Dashboard Platform
# ABOUTME: Exports all CRUD functions for easy access

from .user import (
    get_user_by_email,
    create_user,
    update_user,
    get_user,
    authenticate
)

from .organization import (
    create_organization,
    get_organization,
    get_organization_by_slug,
    get_organizations,
    update_organization,
    delete_organization,
    get_organization_user_count,
    get_organization_study_count,
    check_organization_limits
)

from .study import (
    create_study,
    get_study,
    get_study_by_protocol,
    get_studies,
    get_user_studies,
    update_study,
    delete_study,
    get_study_statistics
)

from .activity_log import (
    create_activity_log,
    get_activity_logs,
    get_user_activities,
    get_audit_trail,
    log_login_attempt
)

__all__ = [
    # User
    "get_user_by_email",
    "create_user", 
    "update_user",
    "get_user",
    "authenticate",
    # Organization
    "create_organization",
    "get_organization",
    "get_organization_by_slug",
    "get_organizations",
    "update_organization",
    "delete_organization",
    "get_organization_user_count",
    "get_organization_study_count",
    "check_organization_limits",
    # Study
    "create_study",
    "get_study",
    "get_study_by_protocol",
    "get_studies",
    "get_user_studies",
    "update_study",
    "delete_study",
    "get_study_statistics",
    # Activity Log
    "create_activity_log",
    "get_activity_logs",
    "get_user_activities",
    "get_audit_trail",
    "log_login_attempt"
]