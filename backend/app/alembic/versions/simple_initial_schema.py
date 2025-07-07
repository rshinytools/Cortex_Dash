# ABOUTME: Simple initial schema migration without ENUM pre-creation
# ABOUTME: Lets SQLAlchemy handle ENUM types automatically

"""Simple initial schema

Revision ID: simple_initial_schema
Revises: 
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'simple_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Empty for now - let's just get the app running
    pass


def downgrade():
    # Empty for now
    pass