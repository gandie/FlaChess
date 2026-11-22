"""Add tournament round, participation, and game tables.

Revision ID: 2f38b6ad91d4
Revises: f47b9d2c6e31
Create Date: 2026-11-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f38b6ad91d4"
down_revision: Union[str, Sequence[str], None] = "f47b9d2c6e31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tournament_round",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "number > 0",
            name="ck_tournament_round_number_positive",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["tournament_section.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "section_id",
            "number",
            name="uq_tournament_round_number",
        ),
    )
    op.create_table(
        "round_participant",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("round_id", sa.BigInteger(), nullable=False),
        sa.Column("participant_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "participation_type",
            sa.Enum(
                "paired",
                "bye",
                "unplayed",
                "absent",
                name="participationtype",
                native_enum=False,
                length=20,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "score_awarded",
            sa.Numeric(precision=2, scale=1),
            nullable=True,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "score_awarded IS NULL OR score_awarded IN (0, 0.5, 1)",
            name="ck_round_participant_score_awarded",
        ),
        sa.CheckConstraint(
            "participation_type != 'paired' OR score_awarded IS NULL",
            name="ck_round_participant_paired_score_null",
        ),
        sa.ForeignKeyConstraint(
            ["round_id"],
            ["tournament_round.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["section_participant.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "round_id",
            "participant_id",
            name="uq_round_participant",
        ),
    )
    op.create_table(
        "game",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("round_id", sa.BigInteger(), nullable=False),
        sa.Column("white_participant_id", sa.BigInteger(), nullable=False),
        sa.Column("black_participant_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "white_score",
            sa.Numeric(precision=2, scale=1),
            nullable=True,
        ),
        sa.Column(
            "black_score",
            sa.Numeric(precision=2, scale=1),
            nullable=True,
        ),
        sa.Column(
            "result_type",
            sa.Enum(
                "normal",
                "white_forfeit",
                "black_forfeit",
                "double_forfeit",
                "adjusted",
                name="gameresulttype",
                native_enum=False,
                length=32,
                create_constraint=True,
            ),
            server_default="normal",
            nullable=False,
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "white_participant_id != black_participant_id",
            name="ck_game_distinct_participants",
        ),
        sa.CheckConstraint(
            "(white_score IS NULL AND black_score IS NULL) OR "
            "(white_score IS NOT NULL AND black_score IS NOT NULL)",
            name="ck_game_scores_together",
        ),
        sa.CheckConstraint(
            "white_score IS NULL OR white_score IN (0, 0.5, 1)",
            name="ck_game_white_score",
        ),
        sa.CheckConstraint(
            "black_score IS NULL OR black_score IN (0, 0.5, 1)",
            name="ck_game_black_score",
        ),
        sa.CheckConstraint(
            "white_score IS NULL OR white_score + black_score = 1",
            name="ck_game_scores_total",
        ),
        sa.ForeignKeyConstraint(
            ["black_participant_id"],
            ["section_participant.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["round_id"],
            ["tournament_round.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["white_participant_id"],
            ["section_participant.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("game")
    op.drop_table("round_participant")
    op.drop_table("tournament_round")
