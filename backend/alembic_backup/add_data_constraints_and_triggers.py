# ABOUTME: Migration to add database constraints, triggers, and functions for data integrity
# ABOUTME: Ensures referential integrity, audit logging, and business rule enforcement

"""Add data constraints and triggers

Revision ID: add_data_constraints_and_triggers
Revises: add_final_indexes_and_seed_data
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'add_data_constraints_and_triggers'
down_revision = 'unify_dashboard_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Add check constraints for data validation
    
    # Widget definitions constraints
    op.create_check_constraint(
        'ck_widget_definitions_version_positive',
        'widget_definitions',
        'version > 0'
    )
    
    # Dashboard templates constraints
    op.create_check_constraint(
        'ck_dashboard_templates_version_positive',
        'dashboard_templates',
        'version > 0'
    )
    
    # Study constraints
    op.create_check_constraint(
        'ck_study_phase_valid',
        'study',
        "phase IN ('I', 'II', 'III', 'IV', 'I/II', 'II/III', 'III/IV')"
    )
    
    op.create_check_constraint(
        'ck_study_status_valid',
        'study',
        "status IN ('planning', 'active', 'completed', 'terminated', 'suspended')"
    )
    
    # Data source constraints
    op.create_check_constraint(
        'ck_data_source_type_valid',
        'data_source',
        "source_type IN ('medidata_rave', 'veeva_vault', 'oracle_clinical', 'sas_files', 'csv_files', 'api', 'database')"
    )
    
    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply updated_at triggers to all tables with updated_at column
    tables_with_updated_at = [
        'widget_definitions', 'dashboard_templates', 'study_dashboards',
        'study', 'organization', 'user', 'data_source', 'refresh_schedule'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
    
    # Create audit logging trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_config_changes()
        RETURNS TRIGGER AS $$
        DECLARE
            v_user_id uuid;
            v_old_data jsonb;
            v_new_data jsonb;
            v_entity_type text;
        BEGIN
            -- Get current user from session context (to be set by application)
            v_user_id := current_setting('app.current_user_id', true)::uuid;
            
            -- Determine entity type from table name
            v_entity_type := TG_TABLE_NAME;
            
            -- Prepare old and new data
            IF TG_OP = 'DELETE' THEN
                v_old_data := to_jsonb(OLD);
                v_new_data := NULL;
            ELSIF TG_OP = 'INSERT' THEN
                v_old_data := NULL;
                v_new_data := to_jsonb(NEW);
            ELSE -- UPDATE
                v_old_data := to_jsonb(OLD);
                v_new_data := to_jsonb(NEW);
            END IF;
            
            -- Insert audit record
            INSERT INTO dashboard_config_audit (
                id, entity_type, entity_id, action, changes, 
                performed_by, performed_at
            ) VALUES (
                gen_random_uuid(),
                v_entity_type,
                COALESCE(NEW.id, OLD.id),
                TG_OP,
                jsonb_build_object('old', v_old_data, 'new', v_new_data),
                v_user_id,
                CURRENT_TIMESTAMP
            );
            
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply audit triggers to critical tables
    audit_tables = [
        'widget_definitions', 'dashboard_templates', 'study_dashboards',
        'org_admin_permissions'
    ]
    
    for table in audit_tables:
        op.execute(f"""
            CREATE TRIGGER audit_{table}_changes
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION audit_config_changes();
        """)
    
    # Create function to validate template structure
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_template_structure(structure jsonb)
        RETURNS boolean AS $$
        BEGIN
            -- Check required top-level keys
            IF NOT (structure ? 'menu' AND structure ? 'dashboards' AND structure ? 'data_mappings') THEN
                RETURN false;
            END IF;
            
            -- Check menu structure
            IF NOT (structure->'menu' ? 'items' AND jsonb_typeof(structure->'menu'->'items') = 'array') THEN
                RETURN false;
            END IF;
            
            -- Check dashboards structure
            IF jsonb_typeof(structure->'dashboards') != 'object' THEN
                RETURN false;
            END IF;
            
            -- Check data_mappings structure
            IF NOT (structure->'data_mappings' ? 'required_datasets' AND 
                    structure->'data_mappings' ? 'field_mappings') THEN
                RETURN false;
            END IF;
            
            RETURN true;
        END;
        $$ language 'plpgsql' IMMUTABLE;
    """)
    
    # Add constraint to validate template structure
    op.create_check_constraint(
        'ck_dashboard_templates_structure_valid',
        'dashboard_templates',
        'validate_template_structure(template_structure)'
    )
    
    # Create function to enforce study dashboard uniqueness
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_active_dashboard_uniqueness()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.is_active = true THEN
                -- Deactivate other dashboards for the same study
                UPDATE study_dashboards 
                SET is_active = false 
                WHERE study_id = NEW.study_id 
                  AND id != NEW.id 
                  AND is_active = true;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger for active dashboard uniqueness
    op.execute("""
        CREATE TRIGGER enforce_one_active_dashboard
        BEFORE INSERT OR UPDATE ON study_dashboards
        FOR EACH ROW EXECUTE FUNCTION enforce_active_dashboard_uniqueness();
    """)
    
    # Add foreign key constraints with proper cascade behavior
    op.create_foreign_key(
        'fk_study_dashboards_created_by',
        'study_dashboards', 'user',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add partial unique indexes for business rules
    op.create_index(
        'idx_study_dashboards_one_active_per_study',
        'study_dashboards',
        ['study_id'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )
    
    op.create_index(
        'idx_widget_definitions_unique_active_code',
        'widget_definitions',
        ['code'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )
    
    op.create_index(
        'idx_dashboard_templates_unique_active_code',
        'dashboard_templates',
        ['code'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )


def downgrade():
    # Drop partial unique indexes
    op.drop_index('idx_dashboard_templates_unique_active_code', table_name='dashboard_templates')
    op.drop_index('idx_widget_definitions_unique_active_code', table_name='widget_definitions')
    op.drop_index('idx_study_dashboards_one_active_per_study', table_name='study_dashboards')
    
    # Drop foreign key
    op.drop_constraint('fk_study_dashboards_created_by', 'study_dashboards', type_='foreignkey')
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS enforce_one_active_dashboard ON study_dashboards")
    
    audit_tables = [
        'widget_definitions', 'dashboard_templates', 'study_dashboards',
        'org_admin_permissions'
    ]
    for table in audit_tables:
        op.execute(f"DROP TRIGGER IF EXISTS audit_{table}_changes ON {table}")
    
    tables_with_updated_at = [
        'widget_definitions', 'dashboard_templates', 'study_dashboards',
        'study', 'organization', 'user', 'data_source', 'refresh_schedule'
    ]
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS enforce_active_dashboard_uniqueness()")
    op.execute("DROP FUNCTION IF EXISTS validate_template_structure(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS audit_config_changes()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop check constraints
    op.drop_constraint('ck_dashboard_templates_structure_valid', 'dashboard_templates')
    op.drop_constraint('ck_data_source_type_valid', 'data_source')
    op.drop_constraint('ck_study_status_valid', 'study')
    op.drop_constraint('ck_study_phase_valid', 'study')
    op.drop_constraint('ck_dashboard_templates_version_positive', 'dashboard_templates')
    op.drop_constraint('ck_widget_definitions_version_positive', 'widget_definitions')