"""fix migration chain

Revision ID: 175112332ca6
Revises: 1b251b722cc4
Create Date: 2026-02-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '175112332ca6'
down_revision: Union[str, Sequence[str], None] = '1b251b722cc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - no changes needed, this is a placeholder to fix migration chain"""
    pass


def downgrade() -> None:
    """Downgrade schema - no changes needed"""
    pass
