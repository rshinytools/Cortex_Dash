"""Add data_contract and permissions columns to widget_definitions

Revision ID: add_widget_data_contract
Revises: unify_dashboard_templates
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_widget_data_contract'
down_revision = 'unify_dashboard_templates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add data_contract column to widget_definitions
    op.add_column('widget_definitions',
        sa.Column('data_contract', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    # Remove column
    op.drop_column('widget_definitions', 'data_contract')