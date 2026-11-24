from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from decimal import Decimal

from app.pairing.types import (
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PlannedOutcomeType,
)


class PairingValidationError(ValueError):
    pass


def validate_complete_plan(
    plan: PairingPlan,
    participants: Sequence[PairingParticipant],
    pairing_format: PairingFormat,
    *,
    previous_pairs: Iterable[tuple[int, int]] = (),
    max_repeat_pairs: int = 0,
) -> PairingPlan:
    validate_participants(participants)
    validate_plan_controls(plan, pairing_format, max_repeat_pairs)
    normalized_previous = {_normalized_pair(pair) for pair in previous_pairs}
    participants_by_id = {
        participant.participant_id: participant for participant in participants
    }
    appearances = Counter[int]()
    repeated_pairs = 0
    planned_pairs: set[frozenset[int]] = set()
    for game in plan.games:
        pair = (game.white_participant_id, game.black_participant_id)
        normalized = _normalized_pair(pair)
        validate_game_pair(pair, normalized, participants_by_id)
        if normalized in planned_pairs:
            raise PairingValidationError("A pair appears more than once in the plan.")
        planned_pairs.add(normalized)
        if normalized in normalized_previous:
            repeated_pairs += 1
        appearances.update(pair)
    if repeated_pairs > max_repeat_pairs:
        raise PairingValidationError(
            f"Plan contains {repeated_pairs} repeat pair(s); "
            f"the limit is {max_repeat_pairs}.",
        )
    for outcome in plan.outcomes:
        if outcome.participant_id not in participants_by_id:
            raise PairingValidationError(
                f"Unknown outcome participant {outcome.participant_id}.",
            )
        appearances[outcome.participant_id] += 1
    validate_exact_coverage(appearances, participants_by_id)
    validate_format_outcomes(plan, participants_by_id, pairing_format)
    return plan


def validate_plan_controls(
    plan: PairingPlan,
    pairing_format: PairingFormat,
    max_repeat_pairs: int,
) -> None:
    if (
        isinstance(plan.round_number, bool)
        or not isinstance(plan.round_number, int)
        or plan.round_number <= 0
    ):
        raise PairingValidationError("Round number must be positive.")
    if (
        isinstance(max_repeat_pairs, bool)
        or not isinstance(max_repeat_pairs, int)
        or max_repeat_pairs < 0
    ):
        raise PairingValidationError(
            "The repeat-pair limit must be a non-negative integer.",
        )
    if not isinstance(pairing_format, PairingFormat):
        raise PairingValidationError("Pairing format is invalid.")


def validate_participants(participants: Sequence[PairingParticipant]) -> None:
    if not participants:
        raise PairingValidationError("A pairing plan requires participants.")
    ids = [participant.participant_id for participant in participants]
    seeds = [participant.seed_position for participant in participants]
    if any(participant_id <= 0 for participant_id in ids):
        raise PairingValidationError("Participant IDs must be positive.")
    if len(set(ids)) != len(ids):
        raise PairingValidationError("Participant IDs must be unique.")
    if any(seed <= 0 for seed in seeds):
        raise PairingValidationError("Seed positions must be positive.")
    if len(set(seeds)) != len(seeds):
        raise PairingValidationError("Seed positions must be unique.")
    if any(participant.bye_count < 0 for participant in participants):
        raise PairingValidationError("Bye counts cannot be negative.")


def validate_game_pair(
    pair: tuple[int, int],
    normalized: frozenset[int],
    participants_by_id: dict[int, PairingParticipant],
) -> None:
    if len(normalized) != 2:
        raise PairingValidationError("A participant cannot be paired with itself.")
    if any(participant_id not in participants_by_id for participant_id in pair):
        raise PairingValidationError("A planned game contains an unknown participant.")


def validate_exact_coverage(
    appearances: Counter[int],
    participants_by_id: dict[int, PairingParticipant],
) -> None:
    expected = set(participants_by_id)
    actual = set(appearances)
    if actual != expected:
        raise PairingValidationError(
            "The plan must contain exactly one result for every participant.",
        )
    duplicated = [participant_id for participant_id, count in appearances.items() if count != 1]
    if duplicated:
        raise PairingValidationError(
            "Each participant must appear exactly once in a complete plan.",
        )


def validate_format_outcomes(
    plan: PairingPlan,
    participants_by_id: dict[int, PairingParticipant],
    pairing_format: PairingFormat,
) -> None:
    valid_scores = {None, Decimal("0"), Decimal("0.5"), Decimal("1")}
    if any(
        not isinstance(outcome.outcome_type, PlannedOutcomeType)
        for outcome in plan.outcomes
    ):
        raise PairingValidationError("Outcome type is invalid.")
    if any(outcome.score_awarded not in valid_scores for outcome in plan.outcomes):
        raise PairingValidationError(
            "Outcome scores must be 0, 0.5, 1, or absent.",
        )
    byes = [
        outcome
        for outcome in plan.outcomes
        if outcome.outcome_type is PlannedOutcomeType.BYE
    ]
    if pairing_format is PairingFormat.SWISS:
        expected_byes = len(participants_by_id) % 2
        if len(byes) != expected_byes:
            raise PairingValidationError(
                f"Swiss plans require {expected_byes} bye(s) for this field.",
            )
        for outcome in byes:
            participant = participants_by_id[outcome.participant_id]
            if participant.bye_count:
                raise PairingValidationError(
                    f"Participant {participant.participant_id} already had a bye.",
                )
            if outcome.score_awarded != Decimal("1"):
                raise PairingValidationError("A Swiss bye must award 1 point.")
    for outcome in plan.outcomes:
        if outcome.outcome_type is not PlannedOutcomeType.BYE:
            continue
        if (
            pairing_format is not PairingFormat.SWISS
            and outcome.score_awarded is not None
        ):
            raise PairingValidationError(
                "Structural byes cannot carry an awarded score.",
            )


def _normalized_pair(pair: tuple[int, int]) -> frozenset[int]:
    return frozenset(pair)

