"""Increase precision for discount column

Revision ID: 32045d4c2d6c
Revises: 
Create Date: 2025-03-04 10:35:25.153137

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "32045d4c2d6c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "order_details",
        "discount",
        type_=sa.Numeric(7, 2),
        existing_type=sa.Numeric(5, 2),
        existing_nullable=False,
    )


def downgrade() -> None:
    pass
