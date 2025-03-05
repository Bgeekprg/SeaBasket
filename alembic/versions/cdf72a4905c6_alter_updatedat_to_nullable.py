"""alter updatedAt to nullable

Revision ID: cdf72a4905c6
Revises: 4fac4deccf15
Create Date: 2025-03-05 10:57:06.446626

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "cdf72a4905c6"
down_revision: Union[str, None] = "4fac4deccf15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "carts",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        type_=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "categories",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        type_=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "order_details",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        type_=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "orders",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        type_=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "product_images",
        "updatedAt",
        existing_type=mysql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "products",
        "updatedAt",
        existing_type=mysql.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "reviews",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        type_=sa.TIMESTAMP(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "users",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        nullable=True,
        existing_server_default=sa.text("(now())"),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "updatedAt",
        existing_type=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "reviews",
        "updatedAt",
        existing_type=sa.TIMESTAMP(),
        type_=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "products",
        "updatedAt",
        existing_type=mysql.TIMESTAMP(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "product_images",
        "updatedAt",
        existing_type=mysql.TIMESTAMP(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "orders",
        "updatedAt",
        existing_type=sa.TIMESTAMP(),
        type_=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "order_details",
        "updatedAt",
        existing_type=sa.TIMESTAMP(),
        type_=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "categories",
        "updatedAt",
        existing_type=sa.TIMESTAMP(),
        type_=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
    op.alter_column(
        "carts",
        "updatedAt",
        existing_type=sa.TIMESTAMP(),
        type_=mysql.DATETIME(),
        nullable=False,
        existing_server_default=sa.text("(now())"),
    )
