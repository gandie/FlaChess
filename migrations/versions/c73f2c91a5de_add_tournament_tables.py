"""Add tournament tables.

Revision ID: c73f2c91a5de
Revises: 8d1c4f6a2b90
Create Date: 2026-11-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c73f2c91a5de"
down_revision: Union[str, Sequence[str], None] = "8d1c4f6a2b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tournament",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "lifecycle",
            sa.Enum(
                "draft",
                "active",
                "finished",
                name="tournamentlifecycle",
                native_enum=False,
                length=20,
                create_constraint=True,
            ),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("time_control", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_tournament_dates",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tournament_participant",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournament.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tournament_id",
            "player_id",
            name="uq_tournament_participant",
        ),
    )


def downgrade() -> None:
    op.drop_table("tournament_participant")
    op.drop_table("tournament")
