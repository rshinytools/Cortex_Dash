# ABOUTME: Final migration to add performance indexes and seed essential widget and template data
# ABOUTME: Ensures all tables have proper indexes and populates system with default widgets/templates

"""Add final indexes and seed data

Revision ID: add_final_indexes_and_seed_data
Revises: unify_dashboard_templates
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'add_final_indexes_and_seed_data'
down_revision = 'unify_dashboard_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Add composite indexes for frequently queried combinations
    op.create_index('idx_study_dashboards_study_template', 'study_dashboards', 
                    ['study_id', 'dashboard_template_id'], unique=False)
    
    op.create_index('idx_dashboard_templates_category_active', 'dashboard_templates',
                    ['category', 'is_active'], unique=False)
    
    op.create_index('idx_widget_definitions_category_active', 'widget_definitions',
                    ['category', 'is_active'], unique=False)
    
    # Add index for activity log performance
    op.create_index('idx_activity_log_user_timestamp', 'activity_log',
                    ['user_id', 'timestamp'], unique=False)
    
    op.create_index('idx_activity_log_org_timestamp', 'activity_log',
                    ['org_id', 'timestamp'], unique=False)
    
    # Add indexes for data source queries
    op.create_index('idx_data_source_study_type', 'data_source',
                    ['study_id', 'source_type'], unique=False)
    
    # Add indexes for refresh schedules
    op.create_index('idx_refresh_schedule_study_active', 'refresh_schedule',
                    ['study_id', 'is_active'], unique=False)
    
    # Seed default system widgets
    op.execute("""
        INSERT INTO widget_definitions (id, code, name, description, category, version, config_schema, default_config, size_constraints, data_requirements, is_active, created_at, updated_at)
        VALUES 
        -- Metric Card Widget
        (gen_random_uuid(), 'metric_card', 'Metric Card', 'Display a single metric with trend', 'metrics', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "format": {"type": "string"}, "trend": {"type": "boolean"}}}',
         '{"trend": true, "format": "number"}',
         '{"minWidth": 2, "minHeight": 2, "maxWidth": 4, "maxHeight": 4}',
         '{"datasets": ["primary"], "fields": ["value", "comparison"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Line Chart Widget
        (gen_random_uuid(), 'line_chart', 'Line Chart', 'Time series line chart', 'charts', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "xAxis": {"type": "string"}, "yAxis": {"type": "array"}}}',
         '{"showLegend": true, "showGrid": true}',
         '{"minWidth": 4, "minHeight": 4, "maxWidth": 12, "maxHeight": 8}',
         '{"datasets": ["primary"], "fields": ["date", "value"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Data Table Widget
        (gen_random_uuid(), 'data_table', 'Data Table', 'Tabular data display with sorting and filtering', 'tables', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "columns": {"type": "array"}, "pageSize": {"type": "number"}}}',
         '{"pageSize": 10, "sortable": true, "filterable": true}',
         '{"minWidth": 6, "minHeight": 4, "maxWidth": 12, "maxHeight": 12}',
         '{"datasets": ["primary"], "fields": ["*"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Pie Chart Widget
        (gen_random_uuid(), 'pie_chart', 'Pie Chart', 'Distribution visualization', 'charts', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "categoryField": {"type": "string"}, "valueField": {"type": "string"}}}',
         '{"showLegend": true, "showLabels": true}',
         '{"minWidth": 4, "minHeight": 4, "maxWidth": 6, "maxHeight": 6}',
         '{"datasets": ["primary"], "fields": ["category", "value"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Bar Chart Widget
        (gen_random_uuid(), 'bar_chart', 'Bar Chart', 'Categorical comparison chart', 'charts', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "orientation": {"type": "string"}, "categoryField": {"type": "string"}}}',
         '{"orientation": "vertical", "showValues": true}',
         '{"minWidth": 4, "minHeight": 4, "maxWidth": 8, "maxHeight": 8}',
         '{"datasets": ["primary"], "fields": ["category", "value"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- KPI Comparison Widget
        (gen_random_uuid(), 'kpi_comparison', 'KPI Comparison', 'Compare multiple KPIs', 'metrics', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "kpis": {"type": "array"}}}',
         '{"layout": "horizontal"}',
         '{"minWidth": 6, "minHeight": 2, "maxWidth": 12, "maxHeight": 4}',
         '{"datasets": ["primary"], "fields": ["*"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Patient Timeline Widget
        (gen_random_uuid(), 'patient_timeline', 'Patient Timeline', 'Visualize patient journey', 'clinical', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "dateField": {"type": "string"}, "eventField": {"type": "string"}}}',
         '{"groupBy": "patient", "showMilestones": true}',
         '{"minWidth": 8, "minHeight": 6, "maxWidth": 12, "maxHeight": 12}',
         '{"datasets": ["events"], "fields": ["patient_id", "event_date", "event_type"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Compliance Status Widget
        (gen_random_uuid(), 'compliance_status', 'Compliance Status', 'Track study compliance metrics', 'clinical', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "metrics": {"type": "array"}}}',
         '{"showTrend": true, "alertThreshold": 0.95}',
         '{"minWidth": 4, "minHeight": 3, "maxWidth": 8, "maxHeight": 6}',
         '{"datasets": ["compliance"], "fields": ["metric", "value", "target"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Data Quality Indicator Widget
        (gen_random_uuid(), 'data_quality_indicator', 'Data Quality Indicator', 'Monitor data quality metrics', 'monitoring', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "qualityChecks": {"type": "array"}}}',
         '{"showDetails": true, "refreshInterval": 300}',
         '{"minWidth": 3, "minHeight": 3, "maxWidth": 6, "maxHeight": 6}',
         '{"datasets": ["quality"], "fields": ["check_name", "status", "score"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Statistical Summary Widget
        (gen_random_uuid(), 'statistical_summary', 'Statistical Summary', 'Display statistical analysis results', 'analytics', 1,
         '{"type": "object", "properties": {"title": {"type": "string"}, "variables": {"type": "array"}, "statistics": {"type": "array"}}}',
         '{"statistics": ["mean", "median", "std", "min", "max"]}',
         '{"minWidth": 6, "minHeight": 4, "maxWidth": 12, "maxHeight": 8}',
         '{"datasets": ["primary"], "fields": ["*"]}',
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (code) DO NOTHING;
    """)
    
    # Seed default dashboard templates
    op.execute("""
        INSERT INTO dashboard_templates (id, code, name, description, category, version, template_structure, is_active, created_at, updated_at)
        VALUES 
        -- Clinical Trial Overview Template
        (gen_random_uuid(), 'clinical_trial_overview', 'Clinical Trial Overview', 'Standard clinical trial monitoring dashboard', 'clinical', 1,
         '{
            "menu": {
                "items": [
                    {"id": "overview", "label": "Overview", "icon": "dashboard", "path": "/overview"},
                    {"id": "enrollment", "label": "Enrollment", "icon": "users", "path": "/enrollment"},
                    {"id": "safety", "label": "Safety", "icon": "shield", "path": "/safety"},
                    {"id": "efficacy", "label": "Efficacy", "icon": "chart", "path": "/efficacy"},
                    {"id": "compliance", "label": "Compliance", "icon": "check", "path": "/compliance"}
                ]
            },
            "dashboards": {
                "overview": {
                    "title": "Study Overview",
                    "layout": {"cols": 12, "rows": 8},
                    "widgets": [
                        {
                            "id": "enrollment_metric",
                            "type": "metric_card",
                            "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                            "config": {"title": "Total Enrolled", "field": "enrolled_count"}
                        },
                        {
                            "id": "screening_metric",
                            "type": "metric_card",
                            "position": {"x": 3, "y": 0, "w": 3, "h": 2},
                            "config": {"title": "Screening", "field": "screening_count"}
                        },
                        {
                            "id": "enrollment_trend",
                            "type": "line_chart",
                            "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                            "config": {"title": "Enrollment Trend", "xAxis": "date", "yAxis": ["enrolled"]}
                        }
                    ]
                }
            },
            "data_mappings": {
                "required_datasets": ["demographics", "enrollment", "adverse_events"],
                "field_mappings": {
                    "enrolled_count": "dm.count(*) where armcd is not null",
                    "screening_count": "dm.count(*) where armcd is null",
                    "date": "dm.rfstdtc",
                    "enrolled": "dm.count(*)"
                }
            }
         }'::jsonb,
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Safety Monitoring Template
        (gen_random_uuid(), 'safety_monitoring', 'Safety Monitoring', 'Comprehensive safety data monitoring', 'safety', 1,
         '{
            "menu": {
                "items": [
                    {"id": "ae_overview", "label": "AE Overview", "icon": "alert", "path": "/ae-overview"},
                    {"id": "sae_tracking", "label": "SAE Tracking", "icon": "warning", "path": "/sae-tracking"},
                    {"id": "lab_results", "label": "Lab Results", "icon": "flask", "path": "/lab-results"}
                ]
            },
            "dashboards": {
                "ae_overview": {
                    "title": "Adverse Events Overview",
                    "layout": {"cols": 12, "rows": 8},
                    "widgets": [
                        {
                            "id": "total_ae",
                            "type": "metric_card",
                            "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                            "config": {"title": "Total AEs", "field": "ae_count"}
                        },
                        {
                            "id": "ae_by_severity",
                            "type": "pie_chart",
                            "position": {"x": 4, "y": 0, "w": 4, "h": 4},
                            "config": {"title": "AEs by Severity", "categoryField": "aesev", "valueField": "count"}
                        }
                    ]
                }
            },
            "data_mappings": {
                "required_datasets": ["adverse_events", "lab_results"],
                "field_mappings": {
                    "ae_count": "ae.count(*)",
                    "aesev": "ae.aesev",
                    "count": "ae.count(*)"
                }
            }
         }'::jsonb,
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
         
        -- Data Quality Dashboard Template
        (gen_random_uuid(), 'data_quality_dashboard', 'Data Quality Dashboard', 'Monitor data quality across all domains', 'quality', 1,
         '{
            "menu": {
                "items": [
                    {"id": "quality_overview", "label": "Quality Overview", "icon": "gauge", "path": "/quality-overview"},
                    {"id": "missing_data", "label": "Missing Data", "icon": "alert-circle", "path": "/missing-data"},
                    {"id": "validation_errors", "label": "Validation Errors", "icon": "x-circle", "path": "/validation-errors"}
                ]
            },
            "dashboards": {
                "quality_overview": {
                    "title": "Data Quality Overview",
                    "layout": {"cols": 12, "rows": 8},
                    "widgets": [
                        {
                            "id": "overall_quality",
                            "type": "metric_card",
                            "position": {"x": 0, "y": 0, "w": 3, "h": 2},
                            "config": {"title": "Overall Quality Score", "field": "quality_score", "format": "percentage"}
                        },
                        {
                            "id": "quality_by_domain",
                            "type": "bar_chart",
                            "position": {"x": 0, "y": 2, "w": 6, "h": 4},
                            "config": {"title": "Quality by Domain", "categoryField": "domain", "valueField": "score"}
                        }
                    ]
                }
            },
            "data_mappings": {
                "required_datasets": ["data_quality_metrics"],
                "field_mappings": {
                    "quality_score": "avg(score)",
                    "domain": "domain",
                    "score": "score"
                }
            }
         }'::jsonb,
         true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (code) DO NOTHING;
    """)


def downgrade():
    # Drop the indexes
    op.drop_index('idx_study_dashboards_study_template', table_name='study_dashboards')
    op.drop_index('idx_dashboard_templates_category_active', table_name='dashboard_templates')
    op.drop_index('idx_widget_definitions_category_active', table_name='widget_definitions')
    op.drop_index('idx_activity_log_user_timestamp', table_name='activity_log')
    op.drop_index('idx_activity_log_org_timestamp', table_name='activity_log')
    op.drop_index('idx_data_source_study_type', table_name='data_source')
    op.drop_index('idx_refresh_schedule_study_active', table_name='refresh_schedule')
    
    # Remove seeded data
    op.execute("DELETE FROM dashboard_templates WHERE code IN ('clinical_trial_overview', 'safety_monitoring', 'data_quality_dashboard')")
    op.execute("DELETE FROM widget_definitions WHERE code IN ('metric_card', 'line_chart', 'data_table', 'pie_chart', 'bar_chart', 'kpi_comparison', 'patient_timeline', 'compliance_status', 'data_quality_indicator', 'statistical_summary')")