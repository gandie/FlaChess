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


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __str__(self) -> str:
        return self.name


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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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
    participants: Mapped[list["TournamentParticipant"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
    phases: Mapped[list["TournamentPhase"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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
    sections: Mapped[list["TournamentSection"]] = relationship(
        back_populates="phase",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return (
            f"Tournament {self.tournament_id} - Phase {self.sequence} "
            f"({self.format.value})"
        )


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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    phase_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_phase.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
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
    advanced_participants: Mapped[list["SectionParticipant"]] = relationship(
        back_populates="source_section",
        foreign_keys="SectionParticipant.source_section_id",
    )

    def __str__(self) -> str:
        return self.name


class SectionParticipant(Base):
    __tablename__ = "section_participant"
    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "section_id",
            name="uq_section_participant_membership",
        ),
        CheckConstraint(
            "rating IS NULL OR rating > 0",
            name="ck_section_participant_rating_positive",
        ),
        CheckConstraint(
            "source_rank IS NULL OR source_rank > 0",
            name="ck_section_participant_source_rank_positive",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_participant.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_section_id: Mapped[int | None] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    participant: Mapped[TournamentParticipant] = relationship(
        back_populates="section_memberships",
    )
    section: Mapped[TournamentSection] = relationship(
        back_populates="participants",
        foreign_keys=[section_id],
    )
    source_section: Mapped[TournamentSection | None] = relationship(
        back_populates="advanced_participants",
        foreign_keys=[source_section_id],
    )
