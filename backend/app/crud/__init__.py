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

from .widget import (
    create_widget,
    get_widget,
    get_widget_by_code,
    get_widgets,
    update_widget,
    delete_widget,
    increment_widget_version,
    get_widget_count_by_category
)

from .dashboard import (
    create_dashboard,
    get_dashboard,
    get_dashboard_by_code,
    get_dashboards,
    update_dashboard,
    delete_dashboard,
    clone_dashboard,
    extract_data_requirements,
    validate_template_structure,
    create_study_dashboard,
    get_study_dashboards,
    update_study_dashboard,
    remove_study_dashboard,
    get_dashboard_count_by_category
)

# Menu imports removed - menu functionality is now integrated into dashboard templates

from .dashboard_audit import (
    create_dashboard_audit_log,
    get_audit_logs,
    get_entity_history,
    create_audit_log_for_create,
    create_audit_log_for_update,
    grant_org_admin_permission,
    revoke_org_admin_permission,
    get_user_org_permissions,
    get_org_admin_permissions,
    check_user_permission,
    get_audit_summary
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
    "log_login_attempt",
    # Widget
    "create_widget",
    "get_widget",
    "get_widget_by_code",
    "get_widgets",
    "update_widget",
    "delete_widget",
    "increment_widget_version",
    "get_widget_count_by_category",
    # Dashboard Templates
    "create_dashboard",
    "get_dashboard",
    "get_dashboard_by_code",
    "get_dashboards",
    "update_dashboard",
    "delete_dashboard",
    "clone_dashboard",
    "extract_data_requirements",
    "validate_template_structure",
    "create_study_dashboard",
    "get_study_dashboards",
    "update_study_dashboard",
    "remove_study_dashboard",
    "get_dashboard_count_by_category",
    # Dashboard Audit
    "create_dashboard_audit_log",
    "get_audit_logs",
    "get_entity_history",
    "create_audit_log_for_create",
    "create_audit_log_for_update",
    "grant_org_admin_permission",
    "revoke_org_admin_permission",
    "get_user_org_permissions",
    "get_org_admin_permissions",
    "check_user_permission",
    "get_audit_summary"
]