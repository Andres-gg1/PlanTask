"""little fixure: Deleted relationship between 'project' and 'personal_chat'

Revision ID: 2a08dcf7f8f9
Revises: a82027d522ca
Create Date: 2025-04-09 14:35:28.921297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a08dcf7f8f9'
down_revision: Union[str, None] = 'a82027d522ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
