"""Add backups table for backup restore system

Revision ID: 0c3010ae2ac1
Revises: widget_filtering_001
Create Date: 2025-08-25 18:57:02.562432

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0c3010ae2ac1'
down_revision = 'widget_filtering_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create backups table
    op.create_table(
        'backups',
        sa.Column('id', postgresql.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('size_mb', sa.Numeric(10, 2), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Audit fields for 21 CFR Part 11
        sa.Column('created_by', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by_name', sa.String(length=255), nullable=True),
        sa.Column('created_by_email', sa.String(length=255), nullable=True),
        
        # Metadata
        sa.Column('metadata', sa.JSON(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('filename'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    )
    
    # Create index for faster queries
    op.create_index('idx_backups_created', 'backups', ['created_at'], unique=False)


def downgrade():
    # Drop index
    op.drop_index('idx_backups_created', table_name='backups')
    
    # Drop table
    op.drop_table('backups')
