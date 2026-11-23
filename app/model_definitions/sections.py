from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.model_definitions.tournaments import (
    SectionLifecycle,
    TournamentParticipant,
    TournamentSection,
)


class SectionTiebreak(Base):
    __tablename__ = "section_tiebreak"
    __table_args__ = (
        UniqueConstraint(
            "section_id",
            "sequence",
            name="uq_section_tiebreak_sequence",
        ),
        CheckConstraint(
            "sequence > 0",
            name="ck_section_tiebreak_sequence_positive",
        ),
        Index(
            "uq_section_tiebreak_configuration",
            "section_id",
            "code",
            text("coalesce(parameter, '')"),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    parameter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    section: Mapped[TournamentSection] = relationship(
        back_populates="tiebreaks",
        lazy="joined",
    )
    standing_values: Mapped[list["SectionStandingValue"]] = relationship(
        back_populates="tiebreak",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        parameter = f" ({self.parameter})" if self.parameter is not None else ""
        return f"{self.sequence}. {self.code}{parameter} @ {self.section.name}"


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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
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
        lazy="joined",
    )
    section: Mapped[TournamentSection] = relationship(
        back_populates="participants",
        foreign_keys=[section_id],
        lazy="joined",
    )
    source_section: Mapped[TournamentSection | None] = relationship(
        back_populates="advanced_participants",
        foreign_keys=[source_section_id],
    )
    round_records: Mapped[list["RoundParticipant"]] = relationship(
        back_populates="participant",
        cascade="all, delete-orphan",
    )
    white_games: Mapped[list["Game"]] = relationship(
        back_populates="white_participant",
        foreign_keys="Game.white_participant_id",
    )
    black_games: Mapped[list["Game"]] = relationship(
        back_populates="black_participant",
        foreign_keys="Game.black_participant_id",
    )
    standings: Mapped[list["SectionStanding"]] = relationship(
        back_populates="participant",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return (
            f"{self.participant.player.name} @ {self.section.name} @ "
            f"{self.participant.tournament.name}"
        )


__all__ = ["SectionLifecycle", "SectionParticipant", "SectionTiebreak"]
