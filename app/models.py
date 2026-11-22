from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
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
    tournament: Mapped[Tournament] = relationship(back_populates="participants")
    player: Mapped[Player] = relationship()
