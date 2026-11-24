"""Add section pairing prerequisites.

Revision ID: b4e7c9a1d2f3
Revises: a5e2c7d91f43
Create Date: 2026-11-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4e7c9a1d2f3"
down_revision: Union[str, Sequence[str], None] = "a5e2c7d91f43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "section_participant",
        sa.Column("seed_position", sa.Integer(), nullable=True),
    )
    op.add_column(
        "section_participant",
        sa.Column(
            "is_withdrawn",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_section_participant_seed_position_positive",
        "section_participant",
        "seed_position IS NULL OR seed_position > 0",
    )
    op.create_unique_constraint(
        "uq_section_participant_seed_position",
        "section_participant",
        ["section_id", "seed_position"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_section_participant_seed_position",
        "section_participant",
        type_="unique",
    )
    op.drop_constraint(
        "ck_section_participant_seed_position_positive",
        "section_participant",
        type_="check",
    )
    op.drop_column("section_participant", "is_withdrawn")
    op.drop_column("section_participant", "seed_position")
