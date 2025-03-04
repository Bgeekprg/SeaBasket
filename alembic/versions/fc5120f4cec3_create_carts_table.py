"""create carts table

Revision ID: fc5120f4cec3
Revises: 00e5838bbde0
Create Date: 2025-03-04 20:35:31.642372

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "fc5120f4cec3"
down_revision: Union[str, None] = "00e5838bbde0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("productId", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "createdAt", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updatedAt",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["productId"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("carts")
