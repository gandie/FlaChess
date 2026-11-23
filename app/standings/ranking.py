from collections import defaultdict
from decimal import Decimal
from typing import Iterable, Sequence

from app.models import SectionTiebreak
from app.standings.types import (
    ZERO,
    VALUE_PRECISION,
    CompletedGame,
    ParticipantTotals,
    UnsupportedTiebreakError,
)


def ranking_values(
    participant_ids: list[int],
    totals: dict[int, ParticipantTotals],
    round_points: dict[int, dict[int, Decimal]],
    games: Sequence[CompletedGame],
    round_numbers: Iterable[int],
    rules: Sequence[SectionTiebreak],
) -> tuple[dict[int, dict[int, Decimal]], dict[int, tuple[Decimal, ...]]]:
    keys = {
        participant_id: (-totals[participant_id].points,)
        for participant_id in participant_ids
    }
    values = {participant_id: {} for participant_id in participant_ids}
    for rule in rules:
        groups = equal_key_groups(participant_ids, keys)
        rule_values = tiebreak_values(
            rule.code,
            participant_ids,
            totals,
            round_points,
            games,
            round_numbers,
            groups,
        )
        for participant_id in participant_ids:
            value = rule_values[participant_id].quantize(VALUE_PRECISION)
            values[participant_id][rule.id] = value
            keys[participant_id] += (-value,)
    return values, keys


def tiebreak_values(
    code: str,
    participant_ids: list[int],
    totals: dict[int, ParticipantTotals],
    round_points: dict[int, dict[int, Decimal]],
    games: Sequence[CompletedGame],
    round_numbers: Iterable[int],
    groups: list[set[int]],
) -> dict[int, Decimal]:
    if code == "direct_encounter":
        return direct_encounter(participant_ids, games, groups)
    if code == "number_of_wins":
        return {
            participant_id: Decimal(totals[participant_id].wins)
            for participant_id in participant_ids
        }
    if code == "progressive_score":
        return progressive_scores(participant_ids, round_points, round_numbers)
    if code in {
        "buchholz",
        "buchholz_cut_1",
        "buchholz_cut_2",
        "buchholz_median_1",
        "buchholz_median_2",
    }:
        return buchholz(code, participant_ids, totals, games)
    if code in {"sonneborn_berger", "sonneborn_berger_cut_1"}:
        return sonneborn_berger(code, participant_ids, totals, games)
    raise UnsupportedTiebreakError(code)


def direct_encounter(
    participant_ids: list[int],
    games: Sequence[CompletedGame],
    groups: list[set[int]],
) -> dict[int, Decimal]:
    values = dict.fromkeys(participant_ids, ZERO)
    group_by_participant = {
        participant_id: group
        for group in groups
        for participant_id in group
    }
    for game in games:
        if game.black_id not in group_by_participant[game.white_id]:
            continue
        values[game.white_id] += game.white_score
        values[game.black_id] += game.black_score
    return values


def progressive_scores(
    participant_ids: list[int],
    round_points: dict[int, dict[int, Decimal]],
    round_numbers: Iterable[int],
) -> dict[int, Decimal]:
    ordered_rounds = sorted(set(round_numbers))
    values: dict[int, Decimal] = {}
    for participant_id in participant_ids:
        running = ZERO
        progressive = ZERO
        for round_number in ordered_rounds:
            running += round_points[participant_id].get(round_number, ZERO)
            progressive += running
        values[participant_id] = progressive
    return values


def buchholz(
    code: str,
    participant_ids: list[int],
    totals: dict[int, ParticipantTotals],
    games: Sequence[CompletedGame],
) -> dict[int, Decimal]:
    opponents: dict[int, list[Decimal]] = {
        participant_id: [] for participant_id in participant_ids
    }
    for game in games:
        opponents[game.white_id].append(totals[game.black_id].points)
        opponents[game.black_id].append(totals[game.white_id].points)
    return {
        participant_id: sum(trim_scores(opponents[participant_id], code), ZERO)
        for participant_id in participant_ids
    }


def sonneborn_berger(
    code: str,
    participant_ids: list[int],
    totals: dict[int, ParticipantTotals],
    games: Sequence[CompletedGame],
) -> dict[int, Decimal]:
    contributions: dict[int, list[Decimal]] = {
        participant_id: [] for participant_id in participant_ids
    }
    for game in games:
        contributions[game.white_id].append(
            totals[game.black_id].points * game.white_score,
        )
        contributions[game.black_id].append(
            totals[game.white_id].points * game.black_score,
        )
    if code == "sonneborn_berger_cut_1":
        contributions = {
            participant_id: sorted(values)[1:]
            for participant_id, values in contributions.items()
        }
    return {
        participant_id: sum(values, ZERO)
        for participant_id, values in contributions.items()
    }


def trim_scores(values: Sequence[Decimal], code: str) -> Sequence[Decimal]:
    ordered = sorted(values)
    low_cuts = {
        "buchholz": 0,
        "buchholz_cut_1": 1,
        "buchholz_cut_2": 2,
        "buchholz_median_1": 1,
        "buchholz_median_2": 2,
    }[code]
    high_cuts = low_cuts if "median" in code else 0
    if len(ordered) <= low_cuts + high_cuts:
        return []
    end = len(ordered) - high_cuts if high_cuts else len(ordered)
    return ordered[low_cuts:end]


def equal_key_groups(
    participant_ids: list[int],
    keys: dict[int, tuple[Decimal, ...]],
) -> list[set[int]]:
    groups: dict[tuple[Decimal, ...], set[int]] = defaultdict(set)
    for participant_id in participant_ids:
        groups[keys[participant_id]].add(participant_id)
    return list(groups.values())


def ranks(keys: dict[int, tuple[Decimal, ...]]) -> dict[int, int]:
    ordered = sorted(
        keys,
        key=lambda participant_id: (keys[participant_id], participant_id),
    )
    result: dict[int, int] = {}
    previous_key: tuple[Decimal, ...] | None = None
    current_rank = 0
    for position, participant_id in enumerate(ordered, start=1):
        if keys[participant_id] != previous_key:
            current_rank = position
            previous_key = keys[participant_id]
        result[participant_id] = current_rank
    return result
