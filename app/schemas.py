from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models import TournamentLifecycle


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
