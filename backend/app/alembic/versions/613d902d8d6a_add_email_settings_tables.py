"""Add email settings tables

Revision ID: 613d902d8d6a
Revises: 0c3010ae2ac1
Create Date: 2025-08-26 05:35:16.876267

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '613d902d8d6a'
down_revision = '0c3010ae2ac1'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_settings table
    op.create_table('email_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('smtp_host', sa.String(), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False),
        sa.Column('smtp_username', sa.String(), nullable=True),
        sa.Column('smtp_password', sa.String(), nullable=True),
        sa.Column('smtp_from_email', sa.String(), nullable=False),
        sa.Column('smtp_from_name', sa.String(), nullable=True),
        sa.Column('smtp_use_tls', sa.Boolean(), nullable=False),
        sa.Column('smtp_use_ssl', sa.Boolean(), nullable=False),
        sa.Column('smtp_timeout', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('test_recipient_email', sa.String(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('retry_delay', sa.Integer(), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_key', sa.String(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('html_template', sa.Text(), nullable=False),
        sa.Column('plain_text_template', sa.Text(), nullable=True),
        sa.Column('variables', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_key')
    )
    op.create_index(op.f('ix_email_templates_template_key'), 'email_templates', ['template_key'], unique=False)
    
    # Create email_queue table
    op.create_table('email_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=True),
        sa.Column('cc_emails', sa.String(), nullable=True),
        sa.Column('bcc_emails', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('plain_text_content', sa.Text(), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_variables', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_queue_recipient_email'), 'email_queue', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_email_queue_scheduled_at'), 'email_queue', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_email_queue_status'), 'email_queue', ['status'], unique=False)
    
    # Create email_history table
    op.create_table('email_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('queue_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('template_used', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('opened_count', sa.Integer(), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_links', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('bounced', sa.Boolean(), nullable=False),
        sa.Column('bounce_type', sa.String(), nullable=True),
        sa.Column('bounce_reason', sa.Text(), nullable=True),
        sa.Column('marked_as_spam', sa.Boolean(), nullable=False),
        sa.Column('unsubscribed', sa.Boolean(), nullable=False),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('provider_response', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('send_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['queue_id'], ['email_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_history_recipient_email'), 'email_history', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_email_history_sent_at'), 'email_history', ['sent_at'], unique=False)
    
    # Create user_email_preferences table
    op.create_table('user_email_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receive_account_updates', sa.Boolean(), nullable=False),
        sa.Column('receive_study_updates', sa.Boolean(), nullable=False),
        sa.Column('receive_data_updates', sa.Boolean(), nullable=False),
        sa.Column('receive_system_alerts', sa.Boolean(), nullable=False),
        sa.Column('receive_backup_notifications', sa.Boolean(), nullable=False),
        sa.Column('receive_audit_reports', sa.Boolean(), nullable=False),
        sa.Column('receive_security_alerts', sa.Boolean(), nullable=False),
        sa.Column('receive_pipeline_updates', sa.Boolean(), nullable=False),
        sa.Column('receive_collaboration_invites', sa.Boolean(), nullable=False),
        sa.Column('receive_marketing', sa.Boolean(), nullable=False),
        sa.Column('digest_frequency', sa.String(), nullable=False),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False),
        sa.Column('quiet_hours_start', sa.String(), nullable=True),
        sa.Column('quiet_hours_end', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False),
        sa.Column('prefer_plain_text', sa.Boolean(), nullable=False),
        sa.Column('include_attachments', sa.Boolean(), nullable=False),
        sa.Column('language_code', sa.String(), nullable=False),
        sa.Column('unsubscribe_token', sa.String(), nullable=False),
        sa.Column('last_email_sent_at', sa.DateTime(), nullable=True),
        sa.Column('custom_preferences', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('user_email_preferences')
    op.drop_index(op.f('ix_email_history_sent_at'), table_name='email_history')
    op.drop_index(op.f('ix_email_history_recipient_email'), table_name='email_history')
    op.drop_table('email_history')
    op.drop_index(op.f('ix_email_queue_status'), table_name='email_queue')
    op.drop_index(op.f('ix_email_queue_scheduled_at'), table_name='email_queue')
    op.drop_index(op.f('ix_email_queue_recipient_email'), table_name='email_queue')
    op.drop_table('email_queue')
    op.drop_index(op.f('ix_email_templates_template_key'), table_name='email_templates')
    op.drop_table('email_templates')
    op.drop_table('email_settings')