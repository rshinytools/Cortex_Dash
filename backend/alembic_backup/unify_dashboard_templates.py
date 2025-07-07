# ABOUTME: Migration to unify dashboard and menu templates into a single comprehensive template model
# ABOUTME: Merges menu_templates into dashboard_templates and restructures the JSON schema

"""unify dashboard templates

Revision ID: unify_dashboard_templates
Revises: add_remaining_study_fields
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'unify_dashboard_templates'
down_revision = 'add_study_template_fields'
branch_labels = None
depends_on = None


def upgrade():
    # First, add new columns to dashboard_templates
    op.add_column('dashboard_templates', 
        sa.Column('template_structure', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    
    # Migrate existing data - combine dashboard layout with empty menu structure
    op.execute("""
        UPDATE dashboard_templates
        SET template_structure = jsonb_build_object(
            'menu', jsonb_build_object(
                'items', '[]'::jsonb
            ),
            'dashboards', jsonb_build_object(
                'default', jsonb_build_object(
                    'layout', layout_config,
                    'widgets', '[]'::jsonb
                )
            ),
            'data_mappings', jsonb_build_object(
                'required_datasets', '[]'::jsonb,
                'field_mappings', '{}'::jsonb
            )
        )
        WHERE template_structure IS NULL
    """)
    
    # Make template_structure required
    op.alter_column('dashboard_templates', 'template_structure',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    nullable=False)
    
    # Drop the old layout_config column
    op.drop_column('dashboard_templates', 'layout_config')
    
    # Remove menu_template_id from study_dashboards
    op.drop_constraint('study_dashboards_menu_template_id_fkey', 'study_dashboards', type_='foreignkey')
    op.drop_column('study_dashboards', 'menu_template_id')
    
    # Add data_mappings column to study_dashboards
    op.add_column('study_dashboards',
        sa.Column('data_mappings', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    
    # Drop dashboard_widgets table as widgets are now embedded in template_structure
    op.drop_table('dashboard_widgets')
    
    # Drop menu_templates table
    op.drop_table('menu_templates')


def downgrade():
    # Recreate menu_templates table
    op.create_table('menu_templates',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('menu_structure', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_templates_code'), 'menu_templates', ['code'], unique=True)
    
    # Recreate dashboard_widgets table
    op.create_table('dashboard_widgets',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('dashboard_template_id', postgresql.UUID(), nullable=False),
        sa.Column('widget_definition_id', postgresql.UUID(), nullable=False),
        sa.Column('instance_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('position', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('data_binding', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dashboard_template_id'], ['dashboard_templates.id'], ),
        sa.ForeignKeyConstraint(['widget_definition_id'], ['widget_definitions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add layout_config back to dashboard_templates
    op.add_column('dashboard_templates',
        sa.Column('layout_config', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    
    # Extract layout from template_structure
    op.execute("""
        UPDATE dashboard_templates
        SET layout_config = template_structure->'dashboards'->'default'->'layout'
        WHERE template_structure IS NOT NULL
    """)
    
    # Make layout_config required
    op.alter_column('dashboard_templates', 'layout_config',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    nullable=False)
    
    # Drop template_structure
    op.drop_column('dashboard_templates', 'template_structure')
    
    # Add menu_template_id back to study_dashboards
    op.add_column('study_dashboards',
        sa.Column('menu_template_id', postgresql.UUID(), nullable=True)
    )
    op.create_foreign_key('study_dashboards_menu_template_id_fkey', 'study_dashboards', 'menu_templates', ['menu_template_id'], ['id'])
    
    # Drop data_mappings from study_dashboards
    op.drop_column('study_dashboards', 'data_mappings')