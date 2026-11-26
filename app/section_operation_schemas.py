from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models import (
    GameResultType,
    ParticipationType,
    SectionLifecycle,
    TournamentLifecycle,
)


class OperationParticipant(BaseModel):
    id: int
    player_name: str
    player_avatar: str | None = None
    rating: int | None

    model_config = {"from_attributes": True}


class OperationGame(BaseModel):
    id: int
    round_id: int
    white_participant_id: int
    white_player_name: str
    white_player_avatar: str | None = None
    black_participant_id: int
    black_player_name: str
    black_player_avatar: str | None = None
    white_score: Decimal | None
    black_score: Decimal | None
    result_type: GameResultType
    recorded_at: datetime | None
    comment: str | None

    model_config = {"from_attributes": True}


class OperationRoundParticipant(BaseModel):
    id: int
    round_id: int
    participant_id: int
    player_name: str
    player_avatar: str | None = None
    participation_type: ParticipationType
    score_awarded: Decimal | None
    comment: str | None

    model_config = {"from_attributes": True}


class OperationTiebreak(BaseModel):
    id: int
    code: str
    sequence: int
    parameter: str | None

    model_config = {"from_attributes": True}


class OperationRound(BaseModel):
    id: int
    number: int
    games: list[OperationGame]
    records: list[OperationRoundParticipant]


class SectionOperationResponse(BaseModel):
    id: int
    tournament_id: int
    tournament_name: str
    tournament_lifecycle: TournamentLifecycle
    name: str
    sequence: int
    lifecycle: SectionLifecycle
    tie_break_locked_at: datetime | None
    planned_round_count: int | None
    participants: list[OperationParticipant]
    rounds: list[OperationRound]
    tiebreaks: list[OperationTiebreak]
