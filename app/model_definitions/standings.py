from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.model_definitions.rounds import TournamentRound
from app.model_definitions.sections import SectionParticipant, SectionTiebreak
from app.model_definitions.tournaments import TournamentSection


class SectionStanding(Base):
    __tablename__ = "section_standing"
    __table_args__ = (
        CheckConstraint(
            "rank IS NULL OR rank > 0",
            name="ck_section_standing_rank_positive",
        ),
        CheckConstraint(
            "points >= 0",
            name="ck_section_standing_points_nonnegative",
        ),
        CheckConstraint(
            "wins >= 0",
            name="ck_section_standing_wins_nonnegative",
        ),
        CheckConstraint(
            "draws >= 0",
            name="ck_section_standing_draws_nonnegative",
        ),
        CheckConstraint(
            "losses >= 0",
            name="ck_section_standing_losses_nonnegative",
        ),
        CheckConstraint(
            "game_points IS NULL OR game_points >= 0",
            name="ck_section_standing_game_points_nonnegative",
        ),
        Index(
            "uq_section_standing_snapshot",
            "section_id",
            "participant_id",
            text("coalesce(through_round_id, 0)"),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("section_participant.id", ondelete="CASCADE"),
        nullable=False,
    )
    through_round_id: Mapped[int | None] = mapped_column(
        ForeignKey("tournament_round.id", ondelete="CASCADE"),
        nullable=True,
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, nullable=False)
    game_points: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 1),
        nullable=True,
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    section: Mapped[TournamentSection] = relationship(back_populates="standings")
    participant: Mapped[SectionParticipant] = relationship(
        back_populates="standings",
        lazy="joined",
    )
    through_round: Mapped[TournamentRound | None] = relationship(
        back_populates="standings",
    )
    values: Mapped[list[SectionStandingValue]] = relationship(
        back_populates="standing",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SectionStandingValue.sequence",
    )


class SectionStandingValue(Base):
    __tablename__ = "section_standing_value"
    __table_args__ = (
        UniqueConstraint(
            "standing_id",
            "tiebreak_id",
            name="uq_section_standing_tiebreak",
        ),
        UniqueConstraint(
            "standing_id",
            "sequence",
            name="uq_section_standing_value_sequence",
        ),
        CheckConstraint(
            "sequence > 0",
            name="ck_section_standing_value_sequence_positive",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    standing_id: Mapped[int] = mapped_column(
        ForeignKey("section_standing.id", ondelete="CASCADE"),
        nullable=False,
    )
    tiebreak_id: Mapped[int] = mapped_column(
        ForeignKey("section_tiebreak.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    standing: Mapped[SectionStanding] = relationship(back_populates="values")
    tiebreak: Mapped[SectionTiebreak] = relationship(
        back_populates="standing_values",
    )
