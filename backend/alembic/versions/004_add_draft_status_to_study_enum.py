# ABOUTME: Migration to add DRAFT status to studystatus enum
# ABOUTME: Enables draft study functionality for initialization wizard

"""Add DRAFT status to StudyStatus enum

Revision ID: 004_add_draft_status
Revises: 003_add_study_initialization_fields
Create Date: 2024-01-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_draft_status'
down_revision = '003_add_study_initialization_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add DRAFT to the studystatus enum
    op.execute("ALTER TYPE studystatus ADD VALUE IF NOT EXISTS 'draft' BEFORE 'planning'")


def downgrade():
    # Note: PostgreSQL doesn't support removing values from enums
    # This would require creating a new enum type without the value
    # and migrating all data, which is complex and risky
    pass