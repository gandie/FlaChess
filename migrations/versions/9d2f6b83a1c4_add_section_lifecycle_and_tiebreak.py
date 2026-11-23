"""Add section lifecycle and tie-break configuration.

Revision ID: 9d2f6b83a1c4
Revises: 2f38b6ad91d4
Create Date: 2026-11-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d2f6b83a1c4"
down_revision: Union[str, Sequence[str], None] = "2f38b6ad91d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tournament_section",
        sa.Column(
            "lifecycle",
            sa.Enum(
                "draft",
                "active",
                "finished",
                name="sectionlifecycle",
                native_enum=False,
                length=20,
                create_constraint=True,
            ),
            server_default="draft",
            nullable=False,
        ),
    )
    op.create_table(
        "section_tiebreak",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("parameter", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sequence > 0",
            name="ck_section_tiebreak_sequence_positive",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["tournament_section.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "section_id",
            "sequence",
            name="uq_section_tiebreak_sequence",
        ),
    )
    op.create_index(
        "uq_section_tiebreak_configuration",
        "section_tiebreak",
        [
            "section_id",
            "code",
            sa.text("coalesce(parameter, '')"),
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_section_tiebreak_configuration",
        table_name="section_tiebreak",
    )
    op.drop_table("section_tiebreak")
    op.drop_column("tournament_section", "lifecycle")
