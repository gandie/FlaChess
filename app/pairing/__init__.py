from app.pairing.colors import ColorAllocationError, allocate_colors
from app.pairing.ordering import (
    downward_float_order_key,
    order_by_seed,
    order_by_standings,
    order_for_downward_float,
    seed_order_key,
    standings_order_key,
)
from app.pairing.round_counts import (
    RoundCountError,
    calculate_knockout_round_count,
    calculate_round_robin_round_count,
    calculate_swiss_round_count,
    validate_planned_round_count,
)
from app.pairing.round_robin import (
    RoundRobinPairingError,
    plan_round_robin_round,
)
from app.pairing.swiss import SwissPairingError, plan_swiss_round
from app.pairing.types import (
    Color,
    ColorAllocationContext,
    ColorAssignment,
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PlannedGame,
    PlannedOutcome,
    PlannedOutcomeType,
)
from app.pairing.validation import (
    PairingValidationError,
    validate_complete_plan,
)

__all__ = [
    "Color",
    "ColorAllocationContext",
    "ColorAllocationError",
    "ColorAssignment",
    "PairingFormat",
    "PairingParticipant",
    "PairingPlan",
    "PairingValidationError",
    "PlannedGame",
    "PlannedOutcome",
    "PlannedOutcomeType",
    "RoundCountError",
    "RoundRobinPairingError",
    "SwissPairingError",
    "allocate_colors",
    "calculate_knockout_round_count",
    "calculate_round_robin_round_count",
    "calculate_swiss_round_count",
    "downward_float_order_key",
    "order_by_seed",
    "order_by_standings",
    "order_for_downward_float",
    "plan_round_robin_round",
    "plan_swiss_round",
    "seed_order_key",
    "standings_order_key",
    "validate_complete_plan",
    "validate_planned_round_count",
]
