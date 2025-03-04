"""create categories table

Revision ID: 1f39874e385b
Revises: b183e093a3dd
Create Date: 2025-03-04 20:00:25.925728

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f39874e385b"
down_revision: Union[str, None] = "b183e093a3dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoryName", sa.String(length=100), nullable=False),
        sa.Column("status", sa.Boolean(), default=True, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("categories")
