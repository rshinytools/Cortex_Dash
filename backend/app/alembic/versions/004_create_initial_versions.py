# ABOUTME: Migration to create initial version records for existing templates
# ABOUTME: Ensures all templates have at least one version record for version history

"""Create initial version records for existing templates

Revision ID: 004_create_initial_versions
Revises: 003_add_template_versioning
Create Date: 2025-07-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

# revision identifiers, used by Alembic.
revision = '004_create_initial_versions'
down_revision = '003_add_template_versioning'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, ensure all templates have version numbers (in case any don't)
    op.execute("""
        UPDATE dashboard_templates 
        SET major_version = COALESCE(major_version, 1),
            minor_version = COALESCE(minor_version, 0),
            patch_version = COALESCE(patch_version, 0)
        WHERE major_version IS NULL 
           OR minor_version IS NULL 
           OR patch_version IS NULL
    """)
    
    # Create initial version records for templates that don't have any versions yet
    # This handles the structure transformation from old format to versioning format
    op.execute("""
        INSERT INTO template_versions (
            id,
            template_id,
            major_version,
            minor_version,
            patch_version,
            change_description,
            template_structure,
            is_published,
            breaking_changes,
            created_by,
            created_at,
            version_type,
            auto_created,
            change_summary,
            created_by_name
        )
        SELECT 
            gen_random_uuid(),
            dt.id,
            dt.major_version,
            dt.minor_version,
            dt.patch_version,
            'Initial version - Created from existing template',
            CASE 
                -- If template has the new structure format, use as-is
                WHEN dt.template_structure::jsonb ? 'menu_structure' THEN dt.template_structure
                -- Otherwise, transform from old format to new format
                ELSE jsonb_build_object(
                    'name', dt.name,
                    'description', dt.description,
                    'menu_structure', COALESCE(dt.template_structure::jsonb->'menu', '{"items": []}'::jsonb),
                    'dashboards', COALESCE(
                        -- Extract dashboards from menu items
                        (SELECT jsonb_agg(
                            item->'dashboard' || jsonb_build_object('menuItemId', item->>'id')
                        )
                        FROM jsonb_array_elements(
                            COALESCE(dt.template_structure::jsonb->'menu'->'items', '[]'::jsonb)
                        ) AS item
                        WHERE item->>'type' = 'dashboard_page' 
                          AND item ? 'dashboard'),
                        '[]'::jsonb
                    ),
                    'theme', COALESCE(dt.template_structure::jsonb->'theme', '{}'::jsonb),
                    'settings', COALESCE(dt.template_structure::jsonb->'settings', '{}'::jsonb),
                    'data_mappings', COALESCE(dt.template_structure::jsonb->'data_mappings', '{}'::jsonb)
                )::json
            END,
            true,  -- is_published
            false, -- no breaking changes
            dt.created_by,
            dt.created_at,
            'major',
            true,  -- auto_created
            '["Initial version created during migration to versioning system"]'::json,
            'System Migration'
        FROM dashboard_templates dt
        WHERE NOT EXISTS (
            SELECT 1 FROM template_versions tv 
            WHERE tv.template_id = dt.id
        )
    """)
    
    # Log the migration completion
    op.execute("""
        INSERT INTO template_change_logs (
            id,
            template_id,
            change_type,
            change_category,
            change_description,
            created_by,
            created_at
        )
        SELECT 
            gen_random_uuid(),
            dt.id,
            'migration',
            'system',
            'Initial version created from existing template during migration',
            dt.created_by,
            CURRENT_TIMESTAMP
        FROM dashboard_templates dt
        WHERE EXISTS (
            SELECT 1 FROM template_versions tv 
            WHERE tv.template_id = dt.id 
              AND tv.created_by_name = 'System Migration'
        )
    """)


def downgrade() -> None:
    # Remove the migration-created change logs
    op.execute("""
        DELETE FROM template_change_logs 
        WHERE change_type = 'migration' 
          AND change_category = 'system'
          AND change_description = 'Initial version created from existing template during migration'
    """)
    
    # Remove auto-created version records
    op.execute("""
        DELETE FROM template_versions 
        WHERE created_by_name = 'System Migration'
          AND change_description = 'Initial version - Created from existing template'
    """)
    
    # Note: We don't reset version numbers to NULL because the columns are NOT NULL