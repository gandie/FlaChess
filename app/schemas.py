from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models import (
    GameResultType,
    ParticipationType,
    SectionLifecycle,
    TournamentLifecycle,
    TournamentPhaseFormat,
)


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class TournamentDateMixin(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_date_order(self) -> "TournamentDateMixin":
        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be after starts_at")
        return self


class TournamentCreate(TournamentDateMixin):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    time_control: str | None = Field(default=None, max_length=255)


class TournamentResponse(TournamentDateMixin):
    id: int
    name: str
    description: str | None
    lifecycle: TournamentLifecycle
    time_control: str | None

    model_config = {"from_attributes": True}


class TournamentSummary(TournamentResponse):
    participant_count: int
    phase_count: int
    section_count: int


class TournamentUpdate(TournamentDateMixin):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    time_control: str | None = Field(default=None, max_length=255)


class TournamentTransitionResponse(BaseModel):
    id: int
    lifecycle: TournamentLifecycle

    model_config = {"from_attributes": True}


class TournamentParticipantCreate(BaseModel):
    tournament_id: int = Field(gt=0)
    player_id: int = Field(gt=0)


class TournamentParticipantUpdate(BaseModel):
    tournament_id: int | None = Field(default=None, gt=0)
    player_id: int | None = Field(default=None, gt=0)


class TournamentPhaseCreate(BaseModel):
    tournament_id: int = Field(gt=0)
    sequence: int = Field(gt=0)
    format: TournamentPhaseFormat


class TournamentPhaseUpdate(BaseModel):
    tournament_id: int | None = Field(default=None, gt=0)
    sequence: int | None = Field(default=None, gt=0)
    format: TournamentPhaseFormat | None = None


class TournamentSectionCreate(BaseModel):
    phase_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)
    sequence: int = Field(gt=0)
    planned_round_count: int | None = Field(default=None, gt=0)


class TournamentSectionUpdate(BaseModel):
    phase_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sequence: int | None = Field(default=None, gt=0)
    planned_round_count: int | None = Field(default=None, gt=0)


class SectionTransitionResponse(BaseModel):
    id: int
    lifecycle: SectionLifecycle
    tie_break_locked_at: datetime | None

    model_config = {"from_attributes": True}


class SectionTiebreakCreate(BaseModel):
    section_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=64)
    sequence: int = Field(gt=0)
    parameter: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class SectionTiebreakUpdate(BaseModel):
    section_id: int | None = Field(default=None, gt=0)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    sequence: int | None = Field(default=None, gt=0)
    parameter: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_non_null_required_fields(self) -> "SectionTiebreakUpdate":
        for field in ("section_id", "code", "sequence", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class SectionTiebreakResponse(BaseModel):
    id: int
    section_id: int
    code: str
    sequence: int
    parameter: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class SectionStandingValueResponse(BaseModel):
    id: int
    standing_id: int
    tiebreak_id: int
    sequence: int
    value: Decimal

    model_config = {"from_attributes": True}


class SectionStandingResponse(BaseModel):
    id: int
    section_id: int
    participant_id: int
    through_round_id: int | None
    rank: int | None
    points: Decimal
    wins: int
    draws: int
    losses: int
    game_points: Decimal | None
    computed_at: datetime
    values: list[SectionStandingValueResponse]

    model_config = {"from_attributes": True}


class SectionParticipantCreate(BaseModel):
    participant_id: int = Field(gt=0)
    section_id: int = Field(gt=0)
    rating: int | None = Field(default=None, gt=0)
    rating_source: str | None = Field(default=None, max_length=64)
    source_section_id: int | None = Field(default=None, gt=0)
    source_rank: int | None = Field(default=None, gt=0)


class SectionParticipantUpdate(BaseModel):
    participant_id: int | None = Field(default=None, gt=0)
    section_id: int | None = Field(default=None, gt=0)
    rating: int | None = Field(default=None, gt=0)
    rating_source: str | None = Field(default=None, max_length=64)
    source_section_id: int | None = Field(default=None, gt=0)
    source_rank: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_non_null_relationship_ids(self) -> "SectionParticipantUpdate":
        if "participant_id" in self.model_fields_set and self.participant_id is None:
            raise ValueError("participant_id cannot be null")
        if "section_id" in self.model_fields_set and self.section_id is None:
            raise ValueError("section_id cannot be null")
        return self


class SectionParticipantResponse(BaseModel):
    id: int
    participant_id: int
    section_id: int
    rating: int | None
    rating_source: str | None
    source_section_id: int | None
    source_rank: int | None

    model_config = {"from_attributes": True}


class TournamentRoundCreate(BaseModel):
    section_id: int = Field(gt=0)
    number: int = Field(gt=0)


class TournamentRoundUpdate(BaseModel):
    section_id: int | None = Field(default=None, gt=0)
    number: int | None = Field(default=None, gt=0)


class ScoreMixin(BaseModel):
    @staticmethod
    def validate_score(value: Decimal | None) -> None:
        allowed_scores = {Decimal("0"), Decimal("0.5"), Decimal("1")}
        if value is not None and value not in allowed_scores:
            raise ValueError("score must be 0, 0.5, or 1")


class RoundParticipantCreate(ScoreMixin):
    round_id: int = Field(gt=0)
    participant_id: int = Field(gt=0)
    participation_type: ParticipationType
    score_awarded: Decimal | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_awarded_score(self) -> "RoundParticipantCreate":
        self.validate_score(self.score_awarded)
        if (
            self.participation_type == ParticipationType.PAIRED
            and self.score_awarded is not None
        ):
            raise ValueError("paired participation cannot have score_awarded")
        return self


class RoundParticipantUpdate(ScoreMixin):
    round_id: int | None = Field(default=None, gt=0)
    participant_id: int | None = Field(default=None, gt=0)
    participation_type: ParticipationType | None = None
    score_awarded: Decimal | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_awarded_score(self) -> "RoundParticipantUpdate":
        self.validate_score(self.score_awarded)
        if self.model_fields_set & {"round_id", "participant_id", "participation_type"}:
            for field in ("round_id", "participant_id", "participation_type"):
                if field in self.model_fields_set and getattr(self, field) is None:
                    raise ValueError(f"{field} cannot be null")
        return self


class GameCreate(ScoreMixin):
    round_id: int = Field(gt=0)
    white_participant_id: int = Field(gt=0)
    black_participant_id: int = Field(gt=0)
    white_score: Decimal | None = None
    black_score: Decimal | None = None
    result_type: GameResultType = GameResultType.NORMAL
    recorded_at: datetime | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def validate_game(self) -> "GameCreate":
        if self.white_participant_id == self.black_participant_id:
            raise ValueError("game participants must be different")
        self.validate_scores(self.white_score, self.black_score)
        return self

    @classmethod
    def validate_scores(
        cls,
        white_score: Decimal | None,
        black_score: Decimal | None,
    ) -> None:
        if (white_score is None) != (black_score is None):
            raise ValueError("white_score and black_score must be set together")
        cls.validate_score(white_score)
        cls.validate_score(black_score)
        if white_score is not None and white_score + black_score != 1:
            raise ValueError("game scores must sum to 1")


class GameUpdate(ScoreMixin):
    round_id: int | None = Field(default=None, gt=0)
    white_participant_id: int | None = Field(default=None, gt=0)
    black_participant_id: int | None = Field(default=None, gt=0)
    white_score: Decimal | None = None
    black_score: Decimal | None = None
    result_type: GameResultType | None = None
    recorded_at: datetime | None = None
    comment: str | None = None

    @model_validator(mode="after")
    def require_non_null_required_fields(self) -> "GameUpdate":
        for field in (
            "round_id",
            "white_participant_id",
            "black_participant_id",
            "result_type",
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class RoundParticipantResponse(BaseModel):
    id: int
    round_id: int
    participant_id: int
    participation_type: ParticipationType
    score_awarded: Decimal | None
    comment: str | None

    model_config = {"from_attributes": True}


class GameResponse(BaseModel):
    id: int
    round_id: int
    white_participant_id: int
    black_participant_id: int
    white_score: Decimal | None
    black_score: Decimal | None
    result_type: GameResultType
    recorded_at: datetime | None
    comment: str | None

    model_config = {"from_attributes": True}
