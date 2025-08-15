"""Initialize widget definitions

Revision ID: widget_init_data_002
Revises: rbac_init_data_001
Create Date: 2025-01-14 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime
import json

# revision identifiers, used by Alembic.
revision = 'widget_init_data_002'
down_revision = 'phase1_widget_arch'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Populate widget_definitions table with core widgets"""
    
    # Get system admin user ID (first user created)
    result = op.get_bind().execute(
        "SELECT id FROM \"user\" WHERE email = 'admin@sagarmatha.ai' LIMIT 1"
    )
    admin_user = result.fetchone()
    if admin_user:
        admin_id = str(admin_user[0])
    else:
        # Create a default system user ID if admin doesn't exist yet
        admin_id = str(uuid4())
    
    # Core widget definitions based on WIDGET_ARCHITECTURE_IMPLEMENTATION.md
    widgets = [
        {
            "id": str(uuid4()),
            "name": "KPI Metric Card",
            "code": "kpi_card",
            "category": "METRICS",  # Must match WidgetCategory enum
            "description": "Display key performance indicators with comparisons and trends",
            "version": 1,
            "data_contract": {
                "required_fields": ["value_field"],
                "optional_fields": ["comparison_field", "target_field", "trend_field"],
                "aggregations": ["SUM", "AVG", "COUNT", "MIN", "MAX"],
                "filters": True,
                "grouping": False
            },
            "default_config": {
                "display": {
                    "show_trend": True,
                    "show_comparison": True,
                    "format": "number",
                    "decimals": 2
                }
            },
            "config_schema": {},
            "size_constraints": {"min_width": 2, "min_height": 2, "max_width": 4, "max_height": 4},
            "data_requirements": {},
            "permissions": {},
            "is_active": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "name": "Time Series Chart",
            "code": "time_series",
            "category": "CHARTS",
            "description": "Visualize data trends over time with multiple aggregation periods",
            "version": 1,
            "data_contract": {
                "required_fields": ["date_field", "value_field"],
                "optional_fields": ["group_field", "filter_field"],
                "aggregations": ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "chart_type": "line",
                "show_legend": True,
                "show_grid": True,
                "interpolation": "linear"
            },
            "config_schema": {},
            "size_constraints": {"min_width": 4, "min_height": 3, "max_width": 12, "max_height": 6},
            "data_requirements": {},
            "permissions": {},
            "is_active": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "name": "Distribution Chart",
            "code": "distribution",
            "category": "CHARTS",
            "description": "Show data distribution with various chart types",
            "version": 1,
            "data_contract": {
                "required_fields": ["category_field", "value_field"],
                "optional_fields": ["sub_category_field"],
                "chart_types": ["pie", "bar", "histogram", "donut"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "chart_type": "bar",
                "show_values": True,
                "show_legend": True,
                "orientation": "vertical"
            },
            "config_schema": {},
            "size_constraints": {"min_width": 4, "min_height": 3, "max_width": 8, "max_height": 6},
            "data_requirements": {},
            "permissions": {},
            "is_active": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "name": "Data Table",
            "code": "data_table",
            "category": "TABLES",
            "description": "Flexible data tables with sorting, filtering, and computed columns",
            "version": 1,
            "data_contract": {
                "required_fields": ["columns"],
                "optional_fields": ["computed_columns", "filters", "sort_config"],
                "features": ["sorting", "filtering", "pagination", "export"],
                "exports": ["CSV", "EXCEL", "PDF"]
            },
            "default_config": {
                "pagination": True,
                "page_size": 25,
                "show_filters": True,
                "allow_export": True
            },
            "config_schema": {},
            "size_constraints": {"min_width": 6, "min_height": 4, "max_width": 12, "max_height": 10},
            "data_requirements": {},
            "permissions": {},
            "is_active": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "name": "Subject Timeline",
            "code": "timeline",
            "category": "SPECIALIZED",
            "description": "Visualize subject events and milestones over time",
            "version": 1,
            "data_contract": {
                "required_fields": ["subject_field", "date_field", "event_field"],
                "optional_fields": ["duration_field", "category_field", "status_field"],
                "view_modes": ["gantt", "calendar", "list", "swimlane"],
                "filters": True,
                "grouping": True
            },
            "default_config": {
                "view_mode": "gantt",
                "show_milestones": True,
                "color_by": "category",
                "zoom_level": "month"
            },
            "config_schema": {},
            "size_constraints": {"min_width": 8, "min_height": 4, "max_width": 12, "max_height": 8},
            "data_requirements": {},
            "permissions": {},
            "is_active": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Insert widgets using raw SQL
    for widget in widgets:
        op.execute(
            f"""INSERT INTO widget_definitions 
                (id, code, name, description, category, version, config_schema, 
                 default_config, size_constraints, data_requirements, data_contract, 
                 permissions, is_active, created_by, created_at, updated_at)
                VALUES (
                    '{widget['id']}'::UUID,
                    '{widget['code']}',
                    '{widget['name']}',
                    '{widget['description']}',
                    '{widget['category']}',
                    {widget['version']},
                    '{json.dumps(widget['config_schema'])}',
                    '{json.dumps(widget['default_config'])}',
                    '{json.dumps(widget['size_constraints'])}',
                    '{json.dumps(widget['data_requirements'])}',
                    '{json.dumps(widget['data_contract'])}',
                    '{json.dumps(widget['permissions'])}',
                    {widget['is_active']},
                    '{widget['created_by']}'::UUID,
                    '{widget['created_at']}',
                    '{widget['updated_at']}'
                )"""
        )


def downgrade() -> None:
    """Remove default widget definitions"""
    op.execute("""
        DELETE FROM widget_definitions 
        WHERE code IN ('kpi_card', 'time_series', 'distribution', 'data_table', 'timeline')
    """)