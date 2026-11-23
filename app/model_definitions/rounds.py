from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.model_definitions.sections import SectionParticipant
from app.model_definitions.tournaments import TournamentSection


class TournamentRound(Base):
    __tablename__ = "tournament_round"
    __table_args__ = (
        UniqueConstraint(
            "section_id",
            "number",
            name="uq_tournament_round_number",
        ),
        CheckConstraint(
            "number > 0",
            name="ck_tournament_round_number_positive",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="CASCADE"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[TournamentSection] = relationship(back_populates="rounds")
    participants: Mapped[list[RoundParticipant]] = relationship(
        back_populates="round",
        cascade="all, delete-orphan",
    )
    games: Mapped[list[Game]] = relationship(
        back_populates="round",
        cascade="all, delete-orphan",
    )
    standings: Mapped[list["SectionStanding"]] = relationship(
        back_populates="through_round",
    )

    def __str__(self) -> str:
        return f"Section {self.section_id} - Round {self.number}"


class ParticipationType(str, Enum):
    PAIRED = "paired"
    BYE = "bye"
    UNPLAYED = "unplayed"
    ABSENT = "absent"


class RoundParticipant(Base):
    __tablename__ = "round_participant"
    __table_args__ = (
        UniqueConstraint(
            "round_id",
            "participant_id",
            name="uq_round_participant",
        ),
        CheckConstraint(
            "score_awarded IS NULL OR score_awarded IN (0, 0.5, 1)",
            name="ck_round_participant_score_awarded",
        ),
        CheckConstraint(
            "participation_type != 'paired' OR score_awarded IS NULL",
            name="ck_round_participant_paired_score_null",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_round.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("section_participant.id", ondelete="CASCADE"),
        nullable=False,
    )
    participation_type: Mapped[ParticipationType] = mapped_column(
        SqlEnum(
            ParticipationType,
            native_enum=False,
            length=20,
            values_callable=lambda values: [value.value for value in values],
            create_constraint=True,
        ),
        nullable=False,
    )
    score_awarded: Mapped[Decimal | None] = mapped_column(
        Numeric(2, 1),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    round: Mapped[TournamentRound] = relationship(
        back_populates="participants",
        lazy="joined",
    )
    participant: Mapped[SectionParticipant] = relationship(
        back_populates="round_records",
        lazy="joined",
    )

    def __str__(self) -> str:
        return (
            f"{self.participant.participant.player.name} @ "
            f"{self.participant.section.name} @ Round {self.round.number} @ "
            f"{self.participant.participant.tournament.name}"
        )


class GameResultType(str, Enum):
    NORMAL = "normal"
    WHITE_FORFEIT = "white_forfeit"
    BLACK_FORFEIT = "black_forfeit"
    DOUBLE_FORFEIT = "double_forfeit"
    ADJUSTED = "adjusted"


class Game(Base):
    __tablename__ = "game"
    __table_args__ = (
        CheckConstraint(
            "white_participant_id != black_participant_id",
            name="ck_game_distinct_participants",
        ),
        CheckConstraint(
            "(white_score IS NULL AND black_score IS NULL) OR "
            "(white_score IS NOT NULL AND black_score IS NOT NULL)",
            name="ck_game_scores_together",
        ),
        CheckConstraint(
            "white_score IS NULL OR white_score IN (0, 0.5, 1)",
            name="ck_game_white_score",
        ),
        CheckConstraint(
            "black_score IS NULL OR black_score IN (0, 0.5, 1)",
            name="ck_game_black_score",
        ),
        CheckConstraint(
            "white_score IS NULL OR white_score + black_score = 1",
            name="ck_game_scores_total",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_round.id", ondelete="CASCADE"),
        nullable=False,
    )
    white_participant_id: Mapped[int] = mapped_column(
        ForeignKey("section_participant.id", ondelete="CASCADE"),
        nullable=False,
    )
    black_participant_id: Mapped[int] = mapped_column(
        ForeignKey("section_participant.id", ondelete="CASCADE"),
        nullable=False,
    )
    white_score: Mapped[Decimal | None] = mapped_column(
        Numeric(2, 1),
        nullable=True,
    )
    black_score: Mapped[Decimal | None] = mapped_column(
        Numeric(2, 1),
        nullable=True,
    )
    result_type: Mapped[GameResultType] = mapped_column(
        SqlEnum(
            GameResultType,
            native_enum=False,
            length=32,
            values_callable=lambda values: [value.value for value in values],
            create_constraint=True,
        ),
        nullable=False,
        default=GameResultType.NORMAL,
        server_default=GameResultType.NORMAL.value,
    )
    recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    round: Mapped[TournamentRound] = relationship(back_populates="games")
    white_participant: Mapped[SectionParticipant] = relationship(
        back_populates="white_games",
        foreign_keys=[white_participant_id],
    )
    black_participant: Mapped[SectionParticipant] = relationship(
        back_populates="black_games",
        foreign_keys=[black_participant_id],
    )
