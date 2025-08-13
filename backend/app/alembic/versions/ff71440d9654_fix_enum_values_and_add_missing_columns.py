"""Fix enum values and add missing columns

Revision ID: ff71440d9654
Revises: e577b224964e
Create Date: 2025-08-13 01:20:20.659636

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'ff71440d9654'
down_revision = 'e577b224964e'
branch_labels = None
depends_on = None


def upgrade():
    """Apply all production fixes for enums and missing columns"""
    conn = op.get_bind()
    
    # 1. Fix StudyStatus enum to have uppercase values and include DRAFT
    conn.execute(text("ALTER TYPE studystatus RENAME TO studystatus_old"))
    conn.execute(text("""
        CREATE TYPE studystatus AS ENUM (
            'DRAFT', 'PLANNING', 'SETUP', 'ACTIVE', 'PAUSED', 'COMPLETED', 'ARCHIVED'
        )
    """))
    conn.execute(text("""
        ALTER TABLE study 
        ALTER COLUMN status TYPE studystatus 
        USING status::text::studystatus
    """))
    conn.execute(text("DROP TYPE studystatus_old"))
    
    # 2. Skip TemplateStatus enum fix for fresh install - it's already correct in the migration
    # The enum is created with DRAFT, PUBLISHED, DEPRECATED, ARCHIVED which is fine
    
    # 3. Create default organization if it doesn't exist
    org_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM organization LIMIT 1
        )
    """)).scalar()
    
    if not org_exists:
        # Check if organization table has type column
        has_type_column = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'organization' 
                AND column_name = 'type'
            )
        """)).scalar()
        
        if has_type_column:
            conn.execute(text("""
                INSERT INTO organization (id, name, type, is_active, settings, created_at, updated_at)
                VALUES (
                    gen_random_uuid(),
                    'Sagarmatha AI',
                    'pharmaceutical',
                    true,
                    '{}',
                    NOW(),
                    NOW()
                )
            """))
        else:
            # Old schema without type column
            conn.execute(text("""
                INSERT INTO organization (id, name, slug, active, features, compliance_settings, created_at, updated_at, license_type, max_users, max_studies)
                VALUES (
                    gen_random_uuid(),
                    'Sagarmatha AI',
                    'sagarmatha-ai',
                    true,
                    '{}',
                    '{}',
                    NOW(),
                    NOW(),
                    'enterprise',
                    100,
                    100
                )
            """))
        
        # Assign admin user to organization
        conn.execute(text("""
            UPDATE "user" 
            SET org_id = (SELECT id FROM organization LIMIT 1)
            WHERE email = 'admin@sagarmatha.ai' AND org_id IS NULL
        """))
    
    # 4. Ensure all study columns exist (these might already exist from previous migrations)
    # Check if columns exist before adding
    columns_to_check = [
        ('study', 'initialization_status'),
        ('study', 'initialization_progress'),
        ('study', 'initialization_steps'),
        ('study', 'template_applied_at'),
        ('study', 'data_uploaded_at'),
        ('study', 'mappings_configured_at'),
        ('study', 'activated_at'),
        ('study', 'last_transformation_at'),
        ('study', 'transformation_status'),
        ('study', 'transformation_count'),
        ('study', 'derived_datasets'),
        ('study', 'transformation_errors')
    ]
    
    for table, column in columns_to_check:
        exists = conn.execute(text(f"""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND column_name = '{column}'
            )
        """)).scalar()
        
        if not exists:
            if column == 'initialization_status':
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(50) DEFAULT 'not_started'"))
            elif column == 'initialization_progress':
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER DEFAULT 0"))
            elif column == 'transformation_count':
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} INTEGER DEFAULT 0"))
            elif column == 'transformation_status':
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR(50)"))
            elif column in ['initialization_steps', 'derived_datasets', 'transformation_errors']:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} JSON DEFAULT '{{}}'::json"))
            else:  # datetime columns
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} TIMESTAMP"))
    
    # 5. Fix NULL JSON fields in organization table
    # Ensure features and compliance_settings are never NULL
    conn.execute(text("""
        UPDATE organization 
        SET features = '{}' 
        WHERE features IS NULL
    """))
    
    conn.execute(text("""
        UPDATE organization 
        SET compliance_settings = '{}' 
        WHERE compliance_settings IS NULL
    """))
    
    # 6. Set default template status to PUBLISHED for all existing templates
    # Check if dashboard_templates table exists first
    table_exists = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'dashboard_templates'
        )
    """)).scalar()
    
    if table_exists:
        # Check if there are any templates
        has_templates = conn.execute(text("""
            SELECT EXISTS (SELECT 1 FROM dashboard_templates LIMIT 1)
        """)).scalar()
        
        if has_templates:
            conn.execute(text("""
                UPDATE dashboard_templates 
                SET status = 'PUBLISHED' 
                WHERE status = 'DRAFT'
            """))


def downgrade():
    """Revert changes"""
    conn = op.get_bind()
    
    # 1. Revert StudyStatus enum
    conn.execute(text("ALTER TYPE studystatus RENAME TO studystatus_old"))
    conn.execute(text("""
        CREATE TYPE studystatus AS ENUM (
            'planning', 'setup', 'active', 'paused', 'completed', 'archived'
        )
    """))
    # Remove DRAFT studies or convert them
    conn.execute(text("""
        UPDATE study 
        SET status = 'SETUP' 
        WHERE status = 'DRAFT'
    """))
    conn.execute(text("""
        ALTER TABLE study 
        ALTER COLUMN status TYPE studystatus 
        USING status::text::studystatus
    """))
    conn.execute(text("DROP TYPE studystatus_old"))
    
    # 2. Revert TemplateStatus enum
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'templatestatus'
        )
    """)).scalar()
    
    if result:
        conn.execute(text("ALTER TYPE templatestatus RENAME TO templatestatus_old"))
        conn.execute(text("""
            CREATE TYPE templatestatus AS ENUM (
                'DRAFT', 'PUBLISHED', 'DEPRECATED', 'ARCHIVED'
            )
        """))
        conn.execute(text("""
            ALTER TABLE dashboard_templates 
            ALTER COLUMN status TYPE templatestatus 
            USING status::text::templatestatus
        """))
        conn.execute(text("DROP TYPE templatestatus_old CASCADE"))
    
    # Note: We don't remove the organization or columns as they might contain data