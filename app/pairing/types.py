from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class PairingFormat(str, Enum):
    KNOCKOUT = "knockout"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


class Color(str, Enum):
    WHITE = "white"
    BLACK = "black"


class PlannedOutcomeType(str, Enum):
    BYE = "bye"
    UNPLAYED = "unplayed"
    ABSENT = "absent"


@dataclass(frozen=True)
class PairingParticipant:
    participant_id: int
    seed_position: int
    points: Decimal = Decimal("0")
    ranking_values: tuple[Decimal, ...] = ()
    color_history: tuple[Color, ...] = ()
    bye_count: int = 0


@dataclass(frozen=True)
class PlannedGame:
    white_participant_id: int
    black_participant_id: int


@dataclass(frozen=True)
class PlannedOutcome:
    participant_id: int
    outcome_type: PlannedOutcomeType
    score_awarded: Decimal | None = None


@dataclass(frozen=True)
class KnockoutPredecessor:
    first_participant_id: int
    second_participant_id: int | None = None
    first_score: Decimal | None = None
    second_score: Decimal | None = None


@dataclass(frozen=True)
class PairingPlan:
    round_number: int
    games: tuple[PlannedGame, ...] = ()
    outcomes: tuple[PlannedOutcome, ...] = ()


@dataclass(frozen=True)
class ColorAllocationContext:
    pairing_format: PairingFormat
    round_number: int
    pair_number: int


@dataclass(frozen=True)
class ColorAssignment:
    white_participant_id: int
    black_participant_id: int

