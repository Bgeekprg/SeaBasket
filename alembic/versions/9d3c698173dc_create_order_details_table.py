"""create order_details  table

Revision ID: 9d3c698173dc
Revises: ac600ddea7f3
Create Date: 2025-03-04 21:45:55.604367

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "9d3c698173dc"
down_revision: Union[str, None] = "ac600ddea7f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("orderId", sa.Integer(), nullable=False),
        sa.Column("productId", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("discount", sa.DECIMAL(precision=7, scale=2), nullable=True),
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
            ["orderId"],
            ["orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["productId"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("order_details")
