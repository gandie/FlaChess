from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.model_definitions.players import Player


class TournamentLifecycle(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"


class Tournament(Base):
    __tablename__ = "tournament"
    __table_args__ = (
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_tournament_dates",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle: Mapped[TournamentLifecycle] = mapped_column(
        SqlEnum(
            TournamentLifecycle,
            native_enum=False,
            length=20,
            values_callable=lambda values: [value.value for value in values],
            create_constraint=True,
        ),
        nullable=False,
        default=TournamentLifecycle.DRAFT,
        server_default=TournamentLifecycle.DRAFT.value,
    )
    time_control: Mapped[str | None] = mapped_column(String(255), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    participants: Mapped[list[TournamentParticipant]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    phases: Mapped[list[TournamentPhase]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return self.name


class TournamentParticipant(Base):
    __tablename__ = "tournament_participant"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "player_id",
            name="uq_tournament_participant",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournament.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("player.id", ondelete="CASCADE"),
        nullable=False,
    )
    tournament: Mapped[Tournament] = relationship(
        back_populates="participants",
        lazy="joined",
    )
    player: Mapped[Player] = relationship(lazy="joined")
    section_memberships: Mapped[list["SectionParticipant"]] = relationship(
        back_populates="participant",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return f"{self.player.name} @ {self.tournament.name}"


class TournamentPhaseFormat(str, Enum):
    KNOCKOUT = "knockout"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


class TournamentPhase(Base):
    __tablename__ = "tournament_phase"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id",
            "sequence",
            name="uq_tournament_phase_sequence",
        ),
        CheckConstraint(
            "sequence > 0",
            name="ck_tournament_phase_sequence_positive",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournament.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[TournamentPhaseFormat] = mapped_column(
        SqlEnum(
            TournamentPhaseFormat,
            native_enum=False,
            length=20,
            values_callable=lambda values: [value.value for value in values],
            create_constraint=True,
        ),
        nullable=False,
    )
    tournament: Mapped[Tournament] = relationship(back_populates="phases")
    sections: Mapped[list[TournamentSection]] = relationship(
        back_populates="phase",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return (
            f"Tournament {self.tournament_id} - Phase {self.sequence} "
            f"({self.format.value})"
        )


class SectionLifecycle(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FINISHED = "finished"


class TournamentSection(Base):
    __tablename__ = "tournament_section"
    __table_args__ = (
        UniqueConstraint(
            "phase_id",
            "sequence",
            name="uq_tournament_section_sequence",
        ),
        CheckConstraint(
            "sequence > 0",
            name="ck_tournament_section_sequence_positive",
        ),
        CheckConstraint(
            "planned_round_count IS NULL OR planned_round_count > 0",
            name="ck_tournament_section_round_count_positive",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phase_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_phase.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle: Mapped[SectionLifecycle] = mapped_column(
        SqlEnum(
            SectionLifecycle,
            native_enum=False,
            length=20,
            values_callable=lambda values: [value.value for value in values],
            create_constraint=True,
        ),
        nullable=False,
        default=SectionLifecycle.DRAFT,
        server_default=SectionLifecycle.DRAFT.value,
    )
    tie_break_locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    planned_round_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    phase: Mapped[TournamentPhase] = relationship(back_populates="sections")
    participants: Mapped[list["SectionParticipant"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        foreign_keys="SectionParticipant.section_id",
    )
    rounds: Mapped[list["TournamentRound"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
    )
    tiebreaks: Mapped[list["SectionTiebreak"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
    )
    standings: Mapped[list["SectionStanding"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
    )
    advanced_participants: Mapped[list["SectionParticipant"]] = relationship(
        back_populates="source_section",
        foreign_keys="SectionParticipant.source_section_id",
    )

    def __str__(self) -> str:
        return self.name
