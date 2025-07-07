"""Fix activity log columns

Revision ID: fix_activity_log_columns
Revises: add_widget_data_contract
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision = 'fix_activity_log_columns'
down_revision = 'add_widget_data_contract'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to activity_log table
    op.add_column('activity_log', sa.Column('timestamp', sa.DateTime(), nullable=True))
    op.add_column('activity_log', sa.Column('study_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('activity_log', sa.Column('system_timestamp', sa.DateTime(), nullable=True))
    op.add_column('activity_log', sa.Column('sequence_number', sa.BigInteger(), nullable=True))
    op.add_column('activity_log', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('activity_log', sa.Column('old_value', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('activity_log', sa.Column('new_value', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('activity_log', sa.Column('reason', sa.Text(), nullable=True))
    
    # Copy data from created_at to timestamp
    op.execute("UPDATE activity_log SET timestamp = created_at")
    
    # Make timestamp not null after copying data
    op.alter_column('activity_log', 'timestamp', nullable=False)
    
    # Set system_timestamp to current timestamp where null
    op.execute("UPDATE activity_log SET system_timestamp = CURRENT_TIMESTAMP WHERE system_timestamp IS NULL")
    
    # Set sequence_number using a CTE
    op.execute("""
        WITH numbered AS (
            SELECT id, row_number() OVER (ORDER BY created_at) as seq_num
            FROM activity_log
        )
        UPDATE activity_log 
        SET sequence_number = numbered.seq_num
        FROM numbered
        WHERE activity_log.id = numbered.id
    """)
    
    # Make required columns not null
    op.alter_column('activity_log', 'system_timestamp', nullable=False)
    op.alter_column('activity_log', 'sequence_number', nullable=False)
    
    # Create indexes
    op.create_index('idx_activity_timestamp_user', 'activity_log', ['timestamp', 'user_id'])
    op.create_index('idx_activity_resource', 'activity_log', ['resource_type', 'resource_id'])
    op.create_index('idx_activity_org_study', 'activity_log', ['org_id', 'study_id'])
    op.create_index(op.f('ix_activity_log_sequence_number'), 'activity_log', ['sequence_number'])
    
    # Create foreign keys
    op.create_foreign_key(None, 'activity_log', 'study', ['study_id'], ['id'])
    op.create_foreign_key(None, 'activity_log', 'organization', ['org_id'], ['id'])
    op.create_foreign_key(None, 'activity_log', 'user', ['user_id'], ['id'])


def downgrade() -> None:
    # Drop foreign keys
    op.drop_constraint(None, 'activity_log', type_='foreignkey')
    op.drop_constraint(None, 'activity_log', type_='foreignkey')
    op.drop_constraint(None, 'activity_log', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_activity_org_study', table_name='activity_log')
    op.drop_index('idx_activity_resource', table_name='activity_log')
    op.drop_index('idx_activity_timestamp_user', table_name='activity_log')
    op.drop_index(op.f('ix_activity_log_sequence_number'), table_name='activity_log')
    
    # Drop columns
    op.drop_column('activity_log', 'reason')
    op.drop_column('activity_log', 'new_value')
    op.drop_column('activity_log', 'old_value')
    op.drop_column('activity_log', 'checksum')
    op.drop_column('activity_log', 'sequence_number')
    op.drop_column('activity_log', 'system_timestamp')
    op.drop_column('activity_log', 'study_id')
    op.drop_column('activity_log', 'timestamp')