"""create product_images table

Revision ID: 00e5838bbde0
Revises: 85ce7a5ec91d
Create Date: 2025-03-04 20:30:28.379354

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "00e5838bbde0"
down_revision: Union[str, None] = "85ce7a5ec91d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("productId", sa.Integer(), nullable=False),
        sa.Column("imageUrl", sa.String(length=255), nullable=False),
        sa.Column(
            "createdAt", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updatedAt",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["productId"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("product_images")
