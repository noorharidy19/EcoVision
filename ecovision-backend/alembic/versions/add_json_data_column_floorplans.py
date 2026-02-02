"""add json_data column to floorplans

Revision ID: add_json_data_column
Revises: 175112332ca6
Create Date: 2026-02-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_json_data_column'
down_revision: Union[str, Sequence[str], None] = '175112332ca6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add json_data column to floorplans."""
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('floorplans')]
    
    if 'json_data' not in columns:
        op.add_column('floorplans',
            sa.Column('json_data', postgresql.JSON(), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema - remove json_data column."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('floorplans')]
    
    if 'json_data' in columns:
        op.drop_column('floorplans', 'json_data')
