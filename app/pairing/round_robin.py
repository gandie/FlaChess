from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from app.pairing.colors import allocate_colors
from app.pairing.ordering import order_by_seed
from app.pairing.round_counts import calculate_round_robin_round_count
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


class RoundRobinPairingError(ValueError):
    pass


SchedulePair = tuple[PairingParticipant | None, PairingParticipant | None]
ScheduleRound = tuple[SchedulePair, ...]
Schedule = tuple[ScheduleRound, ...]


def plan_round_robin_round(
    participants: Sequence[PairingParticipant],
    round_number: int,
) -> PairingPlan:
    validate_participants(participants)
    round_count = calculate_round_robin_round_count(len(participants))
    validate_round_number(round_number, round_count)
    ordered = order_by_seed(participants)
    schedule = build_circle_schedule(ordered)
    validate_schedule(schedule, ordered, round_count)
    plan = _build_plan(schedule[round_number - 1], round_number)
    return validate_complete_plan(
        plan,
        participants,
        PairingFormat.ROUND_ROBIN,
    )


def validate_round_number(round_number: int, round_count: int) -> None:
    if (
        isinstance(round_number, bool)
        or not isinstance(round_number, int)
        or not 1 <= round_number <= round_count
    ):
        raise RoundRobinPairingError(
            f"Round number must be between 1 and {round_count}.",
        )


def build_circle_schedule(
    participants: tuple[PairingParticipant, ...],
) -> Schedule:
    slots: list[PairingParticipant | None] = list(participants)
    if len(slots) % 2:
        slots.append(None)
    rounds: list[ScheduleRound] = []
    for _ in range(len(slots) - 1):
        rounds.append(
            tuple(
                (slots[index], slots[-index - 1])
                for index in range(len(slots) // 2)
            ),
        )
        slots = [slots[0], slots[-1], *slots[1:-1]]
    return tuple(rounds)


def validate_schedule(
    schedule: Schedule,
    participants: tuple[PairingParticipant, ...],
    round_count: int,
) -> None:
    if len(schedule) != round_count:
        raise RoundRobinPairingError("The circle schedule has an invalid round count.")
    expected_appearances = Counter(participant.participant_id for participant in participants)
    actual_pairs: list[frozenset[int]] = []
    expected_byes = len(participants) % 2
    for schedule_round in schedule:
        appearances: Counter[int] = Counter()
        byes = 0
        for first, second in schedule_round:
            if first is None and second is None:
                raise RoundRobinPairingError("The schedule contains an empty pairing.")
            if first is None or second is None:
                participant = first if second is None else second
                assert participant is not None
                appearances[participant.participant_id] += 1
                byes += 1
                continue
            appearances.update((first.participant_id, second.participant_id))
            actual_pairs.append(
                frozenset((first.participant_id, second.participant_id)),
            )
        if appearances != expected_appearances or byes != expected_byes:
            raise RoundRobinPairingError(
                "A round does not cover every participant exactly once.",
            )
    expected_pair_count = len(participants) * (len(participants) - 1) // 2
    if (
        len(actual_pairs) != expected_pair_count
        or len(set(actual_pairs)) != expected_pair_count
    ):
        raise RoundRobinPairingError(
            "The schedule does not contain every unordered pairing exactly once.",
        )


def _build_plan(schedule_round: ScheduleRound, round_number: int) -> PairingPlan:
    games: list[PlannedGame] = []
    outcomes: list[PlannedOutcome] = []
    pair_number = 0
    for first, second in schedule_round:
        if first is None or second is None:
            participant = first if second is None else second
            assert participant is not None
            outcomes.append(
                PlannedOutcome(participant.participant_id, PlannedOutcomeType.BYE),
            )
            continue
        pair_number += 1
        assignment = allocate_colors(
            first,
            second,
            ColorAllocationContext(
                PairingFormat.ROUND_ROBIN,
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
    return PairingPlan(round_number, tuple(games), tuple(outcomes))
