from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models import TournamentLifecycle, TournamentPhaseFormat


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
    tie_break_locked_at: datetime | None = None
    planned_round_count: int | None = Field(default=None, gt=0)


class TournamentSectionUpdate(BaseModel):
    phase_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sequence: int | None = Field(default=None, gt=0)
    tie_break_locked_at: datetime | None = None
    planned_round_count: int | None = Field(default=None, gt=0)


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
