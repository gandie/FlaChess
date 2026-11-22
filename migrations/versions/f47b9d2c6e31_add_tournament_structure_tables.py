"""Add tournament structure tables.

Revision ID: f47b9d2c6e31
Revises: c73f2c91a5de
Create Date: 2026-11-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f47b9d2c6e31"
down_revision: Union[str, Sequence[str], None] = "c73f2c91a5de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tournament_phase",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tournament_id", sa.BigInteger(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "format",
            sa.Enum(
                "knockout",
                "round_robin",
                "swiss",
                name="tournamentphaseformat",
                native_enum=False,
                length=20,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sequence > 0",
            name="ck_tournament_phase_sequence_positive",
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournament.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tournament_id",
            "sequence",
            name="uq_tournament_phase_sequence",
        ),
    )
    op.create_table(
        "tournament_section",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("phase_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "tie_break_locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("planned_round_count", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "sequence > 0",
            name="ck_tournament_section_sequence_positive",
        ),
        sa.CheckConstraint(
            "planned_round_count IS NULL OR planned_round_count > 0",
            name="ck_tournament_section_round_count_positive",
        ),
        sa.ForeignKeyConstraint(
            ["phase_id"],
            ["tournament_phase.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "phase_id",
            "sequence",
            name="uq_tournament_section_sequence",
        ),
    )
    op.create_table(
        "section_participant",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("participant_id", sa.BigInteger(), nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("rating_source", sa.String(length=64), nullable=True),
        sa.Column("source_section_id", sa.BigInteger(), nullable=True),
        sa.Column("source_rank", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "rating IS NULL OR rating > 0",
            name="ck_section_participant_rating_positive",
        ),
        sa.CheckConstraint(
            "source_rank IS NULL OR source_rank > 0",
            name="ck_section_participant_source_rank_positive",
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["tournament_participant.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["tournament_section.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_section_id"],
            ["tournament_section.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "participant_id",
            "section_id",
            name="uq_section_participant_membership",
        ),
    )


def downgrade() -> None:
    op.drop_table("section_participant")
    op.drop_table("tournament_section")
    op.drop_table("tournament_phase")
