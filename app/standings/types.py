from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from app.models import (
    Game,
    RoundParticipant,
    SectionParticipant,
    SectionTiebreak,
    TournamentRound,
)

ZERO = Decimal("0")
VALUE_PRECISION = Decimal("0.0001")


class StandingComputationError(ValueError):
    pass


class StandingInputNotFoundError(StandingComputationError):
    pass


class UnsupportedTiebreakError(StandingComputationError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Unsupported tie-break code: {code}")
        self.code = code


@dataclass
class ParticipantTotals:
    points: Decimal = ZERO
    wins: int = 0
    draws: int = 0
    losses: int = 0


@dataclass(frozen=True)
class CalculatedStanding:
    participant_id: int
    rank: int
    points: Decimal
    wins: int
    draws: int
    losses: int
    values: dict[int, Decimal]


@dataclass(frozen=True)
class CompletedGame:
    round_number: int
    white_id: int
    black_id: int
    white_score: Decimal
    black_score: Decimal


@dataclass(frozen=True)
class SnapshotInputs:
    participants: Sequence[SectionParticipant]
    rounds: Sequence[TournamentRound]
    games: Sequence[Game]
    records: Sequence[RoundParticipant]
    rules: Sequence[SectionTiebreak]
