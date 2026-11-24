from __future__ import annotations

from dataclasses import dataclass

from app.models import SectionLifecycle, SectionParticipant
from app.pairing.generation_history import (
    round_participant_ids,
    validate_history,
)
from app.pairing.generation_knockout import (
    first_round_field,
    knockout_predecessors,
)
from app.pairing.generation_state import (
    GenerationState,
    PairingGenerationConflict,
    PairingGenerationError,
    pairing_participants,
)
from app.pairing.knockout import plan_knockout_round
from app.pairing.round_counts import validate_planned_round_count
from app.pairing.round_robin import plan_round_robin_round
from app.pairing.swiss import plan_swiss_round
from app.pairing.types import (
    PairingFormat,
    PairingPlan,
    PairingParticipant,
)


@dataclass(frozen=True)
class PreparedPairing:
    plan: PairingPlan
    participants: tuple[PairingParticipant, ...]
    calculated_round_count: int


def prepare_pairing_plan(
    state: GenerationState,
    expected_round_number: int | None,
) -> tuple[PairingPlan, tuple[PairingParticipant, ...]]:
    prepared = prepare_pairing(state, expected_round_number)
    return prepared.plan, prepared.participants


def prepare_pairing(
    state: GenerationState,
    expected_round_number: int | None,
) -> PreparedPairing:
    try:
        validate_section_state(state)
        target_round = validate_round_sequence(state, expected_round_number)
        validate_history(state)
        entrants = select_entrants(state, target_round)
        pairing_field = pairing_participants(state, participants=entrants)
        round_count = validate_round_count(state, pairing_field)
        if target_round > round_count:
            raise PairingGenerationConflict(
                f"Round {target_round} exceeds the planned {round_count} rounds.",
            )
        plan = dispatch_plan(state, pairing_field, target_round)
        validate_plan_eligibility(state, plan)
        return PreparedPairing(plan, pairing_field, round_count)
    except PairingGenerationError:
        raise
    except ValueError as error:
        raise PairingGenerationError(str(error)) from error


def validate_section_state(state: GenerationState) -> None:
    if state.section.lifecycle is not SectionLifecycle.ACTIVE:
        raise PairingGenerationConflict(
            "Pairing generation requires an active section.",
        )
    if state.section.planned_round_count is None:
        raise PairingGenerationError(
            "The section is missing a planned round count.",
        )


def validate_round_sequence(
    state: GenerationState,
    expected_round_number: int | None,
) -> int:
    numbers = [round_.number for round_ in state.rounds]
    required = list(range(1, len(numbers) + 1))
    if numbers != required:
        raise PairingGenerationConflict(
            "Existing rounds must use uninterrupted numbering from 1.",
        )
    target = len(numbers) + 1
    invalid_expected = (
        expected_round_number is not None
        and (
            isinstance(expected_round_number, bool)
            or not isinstance(expected_round_number, int)
            or expected_round_number != target
        )
    )
    if invalid_expected:
        raise PairingGenerationConflict(
            f"Round {expected_round_number} is stale or invalid; "
            f"the next round is {target}.",
        )
    return target


def validate_round_count(
    state: GenerationState,
    participants: tuple[PairingParticipant, ...],
) -> int:
    planned = state.section.planned_round_count
    assert planned is not None
    return validate_planned_round_count(
        state.pairing_format,
        len(participants),
        planned,
    )


def select_entrants(
    state: GenerationState,
    target_round: int,
) -> tuple[SectionParticipant, ...]:
    eligible = tuple(
        participant
        for participant in state.participants
        if not participant.is_withdrawn
    )
    if not eligible:
        raise PairingGenerationError("No eligible participants exist.")
    if state.pairing_format is PairingFormat.ROUND_ROBIN and target_round > 1:
        return frozen_round_robin_field(state, eligible)
    if state.pairing_format is PairingFormat.KNOCKOUT and target_round > 1:
        return first_round_field(state)
    return eligible


def frozen_round_robin_field(
    state: GenerationState,
    eligible: tuple[
        SectionParticipant,
        ...,
    ],
) -> tuple[SectionParticipant, ...]:
    first_round = state.rounds[0]
    initial_ids = round_participant_ids(
        first_round,
        state.games,
        state.records,
    )
    eligible_ids = {participant.id for participant in eligible}
    if initial_ids != eligible_ids:
        raise PairingGenerationConflict(
            "Round-robin membership is fixed; withdrawal, re-entry, "
            "or membership changes are not supported mid-cycle.",
        )
    return eligible


def dispatch_plan(
    state: GenerationState,
    participants: tuple[PairingParticipant, ...],
    target_round: int,
) -> PairingPlan:
    if state.pairing_format is PairingFormat.ROUND_ROBIN:
        return plan_round_robin_round(participants, target_round)
    if state.pairing_format is PairingFormat.SWISS:
        return plan_swiss_round(
            participants,
            target_round,
            previous_pairs(state),
        )
    return plan_knockout_round(
        participants,
        target_round,
        knockout_predecessors(state) if target_round > 1 else (),
    )


def previous_pairs(state: GenerationState) -> tuple[tuple[int, int], ...]:
    pairs = tuple(
        (game.white_participant_id, game.black_participant_id)
        for game in state.games
    )
    return pairs


def validate_plan_eligibility(
    state: GenerationState,
    plan: PairingPlan,
) -> None:
    eligible_ids = {
        participant.id
        for participant in state.participants
        if not participant.is_withdrawn
    }
    planned_ids = {
        participant_id
        for game in plan.games
        for participant_id in (
            game.white_participant_id,
            game.black_participant_id,
        )
    }
    outcome_ids = {
        outcome.participant_id
        for outcome in plan.outcomes
    }
    planned_ids.update(outcome_ids)
    ineligible = planned_ids - eligible_ids
    if ineligible:
        raise PairingGenerationConflict(
            "A withdrawn participant cannot advance into the next round.",
        )
