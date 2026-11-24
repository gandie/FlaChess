from decimal import Decimal

from pydantic import BaseModel, Field

from app.pairing.types import PairingFormat, PlannedOutcomeType


class PairingConfirmationCommand(BaseModel):
    expected_round_number: int = Field(gt=0)


class PairingGameRead(BaseModel):
    white_participant_id: int
    black_participant_id: int


class PairingOutcomeRead(BaseModel):
    participant_id: int
    outcome_type: PlannedOutcomeType
    score_awarded: Decimal | None


class PairingSeedRead(BaseModel):
    participant_id: int
    seed_position: int


class PairingPlanRead(BaseModel):
    section_id: int
    round_id: int | None
    target_round: int
    format: PairingFormat
    planned_round_count: int
    calculated_round_count: int
    games: list[PairingGameRead]
    outcomes: list[PairingOutcomeRead]
    seed_order: list[PairingSeedRead]
    policy_labels: list[str]
    warnings: list[str]
