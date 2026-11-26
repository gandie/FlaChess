"""Add player avatar storage.

Revision ID: d3e8f1a6b2c4
Revises: b4e7c9a1d2f3
Create Date: 2026-11-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e8f1a6b2c4"
down_revision: Union[str, Sequence[str], None] = "b4e7c9a1d2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("player", sa.Column("avatar", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("player", "avatar")
