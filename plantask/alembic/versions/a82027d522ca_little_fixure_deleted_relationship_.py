"""little fixure: Deleted relationship between 'project' and 'personal_chat'



Revision ID: a82027d522ca
Revises: fdf339bbd030
Create Date: 2025-04-09 14:33:30.677919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a82027d522ca'
down_revision: Union[str, None] = 'fdf339bbd030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
