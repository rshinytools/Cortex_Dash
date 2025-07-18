from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.api.v1.endpoints import organizations, studies, pipelines, data_sources, transformations, data_catalog, data_uploads, pipeline_config, data_mapping, study_initialization, websocket, study_wizard
# Temporarily disabled endpoints
# from app.api.v1.endpoints import data_versions, data_quality, data_archival, refresh_schedules
# from app.api.v1.endpoints import dashboards, widgets, visualizations, advanced_visualizations
# from app.api.v1.endpoints import reports, exports, dashboard_exports, scheduled_exports
from app.api.v1.endpoints import system_settings, notification_settings, integrations, custom_fields, workflows
from app.api.v1.endpoints import audit_trail, electronic_signatures, data_integrity, access_control, regulatory_compliance
from app.api.v1.endpoints import system_health, performance_monitoring, backup_recovery, job_monitoring
from app.api.v1.endpoints import users as users_v1, branding, documentation, dashboard_templates
from app.api.v1.endpoints.admin import widgets as admin_widgets, dashboards as admin_dashboards, menus as admin_menus
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Clinical dashboard endpoints
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(study_initialization.router, prefix="", tags=["study-initialization"])
api_router.include_router(study_wizard.router, prefix="/studies", tags=["study-wizard"])
api_router.include_router(websocket.router, prefix="", tags=["websocket"])
api_router.include_router(users_v1.router, prefix="/v1/users", tags=["users-clinical"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["data-sources"])
api_router.include_router(transformations.router, prefix="/transformations", tags=["transformations"])
api_router.include_router(data_catalog.router, prefix="/data-catalog", tags=["data-catalog"])
api_router.include_router(data_uploads.router, prefix="/data-uploads", tags=["data-uploads"])
api_router.include_router(pipeline_config.router, prefix="/pipeline-config", tags=["pipeline-config"])
api_router.include_router(data_mapping.router, prefix="/data-mapping", tags=["data-mapping"])

# Phase 4: Data Management & Storage APIs - temporarily disabled
# api_router.include_router(data_versions.router, prefix="/data-versions", tags=["data-versions"])
# api_router.include_router(data_quality.router, prefix="/data-quality", tags=["data-quality"])
# api_router.include_router(data_archival.router, prefix="/archival", tags=["archival"])
# api_router.include_router(refresh_schedules.router, prefix="/refresh-schedules", tags=["refresh-schedules"])

# Phase 5: Dashboard & Visualization APIs
# api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(dashboard_templates.router, prefix="/dashboard-templates", tags=["dashboard-templates"])
from app.api.v1.endpoints import widgets
api_router.include_router(widgets.router, prefix="/widgets", tags=["widgets"])
# api_router.include_router(visualizations.router, prefix="/visualizations", tags=["visualizations"])
# api_router.include_router(advanced_visualizations.router, prefix="/advanced-visualizations", tags=["advanced-visualizations"])

# Phase 6: Reporting & Export APIs - temporarily disabled
# api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
# api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
# api_router.include_router(dashboard_exports.router, tags=["dashboard-exports"])
# api_router.include_router(scheduled_exports.router, tags=["scheduled-exports"])

# Phase 7: Admin & Configuration APIs
api_router.include_router(system_settings.router, prefix="/system-settings", tags=["system-settings"])
api_router.include_router(notification_settings.router, prefix="/notification-settings", tags=["notification-settings"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(custom_fields.router, prefix="/custom-fields", tags=["custom-fields"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])

# Phase 8: Compliance & Audit APIs
api_router.include_router(audit_trail.router, prefix="/audit-trail", tags=["audit-trail"])
api_router.include_router(electronic_signatures.router, prefix="/electronic-signatures", tags=["electronic-signatures"])
api_router.include_router(data_integrity.router, prefix="/data-integrity", tags=["data-integrity"])
api_router.include_router(access_control.router, prefix="/access-control", tags=["access-control"])
api_router.include_router(regulatory_compliance.router, prefix="/regulatory-compliance", tags=["regulatory-compliance"])

# Phase 9: Monitoring & Operations APIs
api_router.include_router(system_health.router, prefix="/system-health", tags=["system-health"])
api_router.include_router(performance_monitoring.router, prefix="/performance", tags=["performance"])
api_router.include_router(backup_recovery.router, prefix="/backup-recovery", tags=["backup-recovery"])
api_router.include_router(job_monitoring.router, prefix="/jobs", tags=["jobs"])

# Branding APIs
api_router.include_router(branding.router, prefix="/branding", tags=["branding"])

# Documentation APIs
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])

# Admin APIs (System Administrator only)
api_router.include_router(admin_widgets.router, prefix="/admin/widgets", tags=["admin-widgets"])
api_router.include_router(admin_dashboards.router, prefix="/admin/dashboards", tags=["admin-dashboards"])
api_router.include_router(admin_menus.router, prefix="/admin/menus", tags=["admin-menus"])

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
