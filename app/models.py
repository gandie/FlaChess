from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    section_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_section.id", ondelete="CASCADE"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[TournamentSection] = relationship(back_populates="rounds")
    participants: Mapped[list["RoundParticipant"]] = relationship(
        back_populates="round",
        cascade="all, delete-orphan",
    )
    games: Mapped[list["Game"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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
    values: Mapped[list["SectionStandingValue"]] = relationship(
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

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
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
