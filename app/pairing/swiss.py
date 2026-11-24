from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from app.pairing.colors import allocate_colors
from app.pairing.ordering import order_by_seed, order_by_standings
from app.pairing.types import (
    ColorAllocationContext,
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PlannedGame,
    PlannedOutcome,
    PlannedOutcomeType,
)
from app.pairing.validation import validate_complete_plan, validate_participants

MAX_SEARCH_STEPS = 100_000


class SwissPairingError(ValueError):
    pass


ParticipantPair = tuple[PairingParticipant, PairingParticipant]
SearchPair = frozenset[int]


def plan_swiss_round(
    participants: Sequence[PairingParticipant],
    round_number: int,
    previous_pairs: Iterable[tuple[int, int]] = (),
) -> PairingPlan:
    validate_participants(participants)
    validate_round_number(round_number)
    prior_pairs = normalize_previous_pairs(previous_pairs, participants)
    ordered = (
        order_by_seed(participants)
        if round_number == 1
        else order_by_standings(participants)
    )
    bye, pairable = select_bye(ordered)
    pairs = (
        pair_first_round(pairable)
        if round_number == 1
        else find_later_round_pairs(
            prioritize_downward_floaters(pairable),
            prior_pairs,
        )
    )
    games = assign_colors(pairs, round_number)
    outcomes = build_bye_outcome(bye)
    repeats = sum(normalized_pair(pair) in prior_pairs for pair in pairs)
    return validate_complete_plan(
        PairingPlan(round_number, games, outcomes),
        participants,
        PairingFormat.SWISS,
        previous_pairs=prior_pairs,
        max_repeat_pairs=repeats,
    )


def validate_round_number(round_number: int) -> None:
    if (
        isinstance(round_number, bool)
        or not isinstance(round_number, int)
        or round_number <= 0
    ):
        raise SwissPairingError("Round number must be a positive integer.")


def normalize_previous_pairs(
    previous_pairs: Iterable[tuple[int, int]],
    participants: Sequence[PairingParticipant],
) -> set[SearchPair]:
    participant_ids = {
        participant.participant_id for participant in participants
    }
    normalized: set[SearchPair] = set()
    for pair in previous_pairs:
        if len(pair) != 2 or pair[0] == pair[1]:
            raise SwissPairingError("Previous pairs must contain two distinct IDs.")
        if not set(pair) <= participant_ids:
            raise SwissPairingError("A previous pair contains an unknown participant.")
        normalized.add(frozenset(pair))
    return normalized


def select_bye(
    ordered: tuple[PairingParticipant, ...],
) -> tuple[PairingParticipant | None, tuple[PairingParticipant, ...]]:
    if len(ordered) % 2 == 0:
        return None, ordered
    eligible = [participant for participant in reversed(ordered) if not participant.bye_count]
    if not eligible:
        raise SwissPairingError(
            "An odd field cannot receive a second bye for any participant.",
        )
    bye = eligible[0]
    return bye, tuple(participant for participant in ordered if participant != bye)


def pair_first_round(
    ordered: tuple[PairingParticipant, ...],
) -> tuple[ParticipantPair, ...]:
    half = len(ordered) // 2
    return tuple(
        (ordered[index], ordered[-index - 1])
        for index in range(half)
    )


def prioritize_downward_floaters(
    ordered: tuple[PairingParticipant, ...],
) -> tuple[PairingParticipant, ...]:
    groups: list[list[PairingParticipant]] = []
    for participant in ordered:
        if not groups or groups[-1][0].points != participant.points:
            groups.append([])
        groups[-1].append(participant)
    reordered: list[PairingParticipant] = []
    for index, group in enumerate(groups):
        if len(group) % 2 and index < len(groups) - 1:
            floater = max(
                group,
                key=lambda participant: (
                    participant.seed_position,
                    participant.participant_id,
                ),
            )
            group = [
                participant
                for participant in group
                if participant != floater
            ]
            group.append(floater)
        reordered.extend(group)
    return tuple(reordered)


def find_later_round_pairs(
    ordered: tuple[PairingParticipant, ...],
    previous_pairs: set[SearchPair],
) -> tuple[ParticipantPair, ...]:
    steps = [0]
    for repeat_limit in range(len(ordered) // 2 + 1):
        result = search_matching(
            ordered,
            previous_pairs,
            repeat_limit,
            steps,
            (),
            0,
        )
        if result is not None:
            return result
    raise SwissPairingError("No legal complete Swiss pairing exists.")


def search_matching(
    remaining: tuple[PairingParticipant, ...],
    previous_pairs: set[SearchPair],
    repeat_limit: int,
    steps: list[int],
    pairs: tuple[ParticipantPair, ...],
    repeats: int,
) -> tuple[ParticipantPair, ...] | None:
    if not remaining:
        return pairs
    advance_search(steps)
    first = remaining[0]
    for second in ordered_opponents(first, remaining[1:]):
        pair = (first, second)
        next_repeats = repeats + int(normalized_pair(pair) in previous_pairs)
        if next_repeats > repeat_limit:
            continue
        rest = tuple(
            participant
            for participant in remaining[1:]
            if participant.participant_id != second.participant_id
        )
        result = search_matching(
            rest,
            previous_pairs,
            repeat_limit,
            steps,
            (*pairs, pair),
            next_repeats,
        )
        if result is not None:
            return result
    return None


def advance_search(steps: list[int]) -> None:
    steps[0] += 1
    if steps[0] > MAX_SEARCH_STEPS:
        raise SwissPairingError(
            f"Swiss pairing search exceeded the {MAX_SEARCH_STEPS}-step limit.",
        )


def ordered_opponents(
    first: PairingParticipant,
    opponents: tuple[PairingParticipant, ...],
) -> tuple[PairingParticipant, ...]:
    return tuple(
        sorted(
            opponents,
            key=lambda participant: (
                abs(first.points - participant.points),
                participant.points != first.points,
                participant.seed_position,
                participant.participant_id,
            ),
        ),
    )


def normalized_pair(pair: ParticipantPair) -> SearchPair:
    return frozenset(
        (pair[0].participant_id, pair[1].participant_id),
    )


def assign_colors(
    pairs: tuple[ParticipantPair, ...],
    round_number: int,
) -> tuple[PlannedGame, ...]:
    games: list[PlannedGame] = []
    for pair_number, pair in enumerate(pairs, start=1):
        assignment = allocate_colors(
            *pair,
            ColorAllocationContext(
                PairingFormat.SWISS,
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


def build_bye_outcome(
    bye: PairingParticipant | None,
) -> tuple[PlannedOutcome, ...]:
    if bye is None:
        return ()
    return (
        PlannedOutcome(
            bye.participant_id,
            PlannedOutcomeType.BYE,
            Decimal("1"),
        ),
    )
