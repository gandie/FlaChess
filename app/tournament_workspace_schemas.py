from datetime import datetime

from pydantic import BaseModel

from app.models import (
    SectionLifecycle,
    TournamentLifecycle,
    TournamentPhaseFormat,
)


class WorkspaceParticipant(BaseModel):
    registration_id: int
    player_id: int
    player_name: str

    model_config = {"from_attributes": True}


class WorkspaceSectionParticipant(BaseModel):
    id: int
    registration_id: int
    player_id: int
    player_name: str
    rating: int | None
    rating_source: str | None
    source_section_id: int | None
    source_section_name: str | None
    source_rank: int | None

    model_config = {"from_attributes": True}


class WorkspaceTiebreak(BaseModel):
    id: int
    code: str
    sequence: int
    parameter: str | None
    is_active: bool
    supported: bool


class WorkspaceSection(BaseModel):
    id: int
    phase_id: int
    name: str
    sequence: int
    lifecycle: SectionLifecycle
    tie_break_locked_at: datetime | None
    planned_round_count: int | None
    participants: list[WorkspaceSectionParticipant]
    tiebreaks: list[WorkspaceTiebreak]

    model_config = {"from_attributes": True}


class WorkspacePhase(BaseModel):
    id: int
    sequence: int
    format: TournamentPhaseFormat
    sections: list[WorkspaceSection]

    model_config = {"from_attributes": True}


class TournamentReadiness(BaseModel):
    can_activate: bool
    blocking_issues: list[str]
    setup_warnings: list[str]


class TournamentWorkspaceResponse(BaseModel):
    id: int
    name: str
    lifecycle: TournamentLifecycle
    participants: list[WorkspaceParticipant]
    phases: list[WorkspacePhase]
    supported_tiebreak_codes: list[str]
    readiness: TournamentReadiness
