"""Add section standings snapshots.

Revision ID: a5e2c7d91f43
Revises: 9d2f6b83a1c4
Create Date: 2026-11-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a5e2c7d91f43"
down_revision: Union[str, Sequence[str], None] = "9d2f6b83a1c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "section_standing",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("participant_id", sa.BigInteger(), nullable=False),
        sa.Column("through_round_id", sa.BigInteger(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("points", sa.Numeric(precision=6, scale=1), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("draws", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column(
            "game_points",
            sa.Numeric(precision=6, scale=1),
            nullable=True,
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rank IS NULL OR rank > 0",
            name="ck_section_standing_rank_positive",
        ),
        sa.CheckConstraint(
            "points >= 0",
            name="ck_section_standing_points_nonnegative",
        ),
        sa.CheckConstraint(
            "wins >= 0",
            name="ck_section_standing_wins_nonnegative",
        ),
        sa.CheckConstraint(
            "draws >= 0",
            name="ck_section_standing_draws_nonnegative",
        ),
        sa.CheckConstraint(
            "losses >= 0",
            name="ck_section_standing_losses_nonnegative",
        ),
        sa.CheckConstraint(
            "game_points IS NULL OR game_points >= 0",
            name="ck_section_standing_game_points_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["section_participant.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["tournament_section.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["through_round_id"],
            ["tournament_round.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_section_standing_snapshot",
        "section_standing",
        [
            "section_id",
            "participant_id",
            sa.text("coalesce(through_round_id, 0)"),
        ],
        unique=True,
    )
    op.create_table(
        "section_standing_value",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("standing_id", sa.BigInteger(), nullable=False),
        sa.Column("tiebreak_id", sa.BigInteger(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.CheckConstraint(
            "sequence > 0",
            name="ck_section_standing_value_sequence_positive",
        ),
        sa.ForeignKeyConstraint(
            ["standing_id"],
            ["section_standing.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tiebreak_id"],
            ["section_tiebreak.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "standing_id",
            "tiebreak_id",
            name="uq_section_standing_tiebreak",
        ),
        sa.UniqueConstraint(
            "standing_id",
            "sequence",
            name="uq_section_standing_value_sequence",
        ),
    )


def downgrade() -> None:
    op.drop_table("section_standing_value")
    op.drop_index(
        "uq_section_standing_snapshot",
        table_name="section_standing",
    )
    op.drop_table("section_standing")
