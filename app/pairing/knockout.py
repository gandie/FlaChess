from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.pairing.colors import allocate_colors
from app.pairing.ordering import order_by_seed
from app.pairing.round_counts import calculate_knockout_round_count
from app.pairing.types import (
    ColorAllocationContext,
    KnockoutPredecessor,
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PlannedGame,
    PlannedOutcome,
    PlannedOutcomeType,
)
from app.pairing.validation import validate_complete_plan, validate_participants


class KnockoutPairingError(ValueError):
    pass


def plan_knockout_round(
    participants: Sequence[PairingParticipant],
    round_number: int,
    predecessors: Sequence[KnockoutPredecessor] = (),
) -> PairingPlan:
    validate_participants(participants)
    round_count = calculate_knockout_round_count(len(participants))
    validate_round_number(round_number, round_count)
    if round_number == 1:
        if predecessors:
            raise KnockoutPairingError(
                "The first knockout round cannot have predecessor matches.",
            )
        return _plan_first_round(participants)
    winners = resolve_predecessors(
        participants,
        predecessors,
        round_number,
        round_count,
    )
    games = assign_colors(winners, round_number)
    return validate_complete_plan(
        PairingPlan(round_number, games),
        winners,
        PairingFormat.KNOCKOUT,
    )


def validate_round_number(round_number: int, round_count: int) -> None:
    if (
        isinstance(round_number, bool)
        or not isinstance(round_number, int)
        or not 1 <= round_number <= round_count
    ):
        raise KnockoutPairingError(
            f"Round number must be between 1 and {round_count}.",
        )


def resolve_predecessors(
    participants: Sequence[PairingParticipant],
    predecessors: Sequence[KnockoutPredecessor],
    round_number: int,
    round_count: int,
) -> tuple[PairingParticipant, ...]:
    bracket_size = 1 << round_count
    expected = bracket_size >> (round_number - 1)
    if len(predecessors) != expected:
        raise KnockoutPairingError(
            f"Round {round_number} requires {expected} ordered predecessors.",
        )
    participants_by_id = {
        participant.participant_id: participant for participant in participants
    }
    seen: set[int] = set()
    winners: list[PairingParticipant] = []
    for predecessor in predecessors:
        entrant_ids = predecessor_entrant_ids(predecessor, round_number)
        if not set(entrant_ids) <= participants_by_id.keys():
            raise KnockoutPairingError(
                "A predecessor match contains an unknown participant.",
            )
        if seen.intersection(entrant_ids):
            raise KnockoutPairingError(
                "A participant appears in more than one predecessor.",
            )
        seen.update(entrant_ids)
        winner_id = resolve_winner(predecessor)
        winners.append(participants_by_id[winner_id])
    return tuple(winners)


def predecessor_entrant_ids(
    predecessor: KnockoutPredecessor,
    round_number: int,
) -> tuple[int, ...]:
    second_id = predecessor.second_participant_id
    if second_id is None:
        if round_number != 2:
            raise KnockoutPairingError(
                "Structural byes are only valid after the first knockout round.",
            )
        if predecessor.first_score is not None or predecessor.second_score is not None:
            raise KnockoutPairingError(
                "A structural predecessor bye cannot carry a score.",
            )
        return (predecessor.first_participant_id,)
    if predecessor.first_participant_id == second_id:
        raise KnockoutPairingError(
            "A predecessor match cannot contain the same participant twice.",
        )
    return (predecessor.first_participant_id, second_id)


def resolve_winner(predecessor: KnockoutPredecessor) -> int:
    if predecessor.second_participant_id is None:
        return predecessor.first_participant_id
    first_score = predecessor.first_score
    second_score = predecessor.second_score
    if first_score is None or second_score is None:
        raise KnockoutPairingError(
            "Every predecessor match must be complete before advancement.",
        )
    valid_scores = (Decimal("0"), Decimal("0.5"), Decimal("1"))
    if first_score not in valid_scores or second_score not in valid_scores:
        raise KnockoutPairingError("Predecessor scores must be 0, 0.5, or 1.")
    if first_score + second_score != Decimal("1"):
        raise KnockoutPairingError("Predecessor scores must sum to 1.")
    if first_score == second_score:
        raise KnockoutPairingError(
            "A drawn predecessor match cannot advance a participant.",
        )
    return (
        predecessor.first_participant_id
        if first_score > second_score
        else predecessor.second_participant_id
    )


def _plan_first_round(
    participants: Sequence[PairingParticipant],
) -> PairingPlan:
    ordered = order_by_seed(participants)
    bracket_size = 1 << calculate_knockout_round_count(len(ordered))
    slots = standard_seed_slots(bracket_size)
    bracket = {
        seed: participant
        for seed, participant in enumerate(ordered, start=1)
    }
    pair_slots = (
        (slots[index], slots[index + 1])
        for index in range(0, bracket_size, 2)
    )
    games: list[PlannedGame] = []
    outcomes: list[PlannedOutcome] = []
    for pair_number, (first_seed, second_seed) in enumerate(pair_slots, start=1):
        first = bracket.get(first_seed)
        second = bracket.get(second_seed)
        if first is None or second is None:
            participant = first if second is None else second
            if participant is None:
                raise KnockoutPairingError("The bracket contains an empty pairing.")
            outcomes.append(
                PlannedOutcome(participant.participant_id, PlannedOutcomeType.BYE),
            )
            continue
        assignment = allocate_colors(
            first,
            second,
            ColorAllocationContext(PairingFormat.KNOCKOUT, 1, pair_number),
        )
        games.append(
            PlannedGame(
                assignment.white_participant_id,
                assignment.black_participant_id,
            ),
        )
    return validate_complete_plan(
        PairingPlan(1, tuple(games), tuple(outcomes)),
        participants,
        PairingFormat.KNOCKOUT,
    )


def standard_seed_slots(bracket_size: int) -> tuple[int, ...]:
    slots = (1, 2)
    size = 2
    while size < bracket_size:
        size *= 2
        slots = tuple(
            seed
            for slot in slots
            for seed in (slot, size + 1 - slot)
        )
    return slots


def assign_colors(
    participants: tuple[PairingParticipant, ...],
    round_number: int,
) -> tuple[PlannedGame, ...]:
    games: list[PlannedGame] = []
    for index in range(0, len(participants), 2):
        pair_number = index // 2 + 1
        assignment = allocate_colors(
            participants[index],
            participants[index + 1],
            ColorAllocationContext(
                PairingFormat.KNOCKOUT,
                round_number,
                pair_number,
            ),
        )
        games.append(
            PlannedGame(
                assignment.white_participant_id,
                assignment.black_participant_id,
            ),
        )
    return tuple(games)
