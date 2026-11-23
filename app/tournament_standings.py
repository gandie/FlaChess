from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Game,
    ParticipationType,
    RoundParticipant,
    SectionParticipant,
    SectionStanding,
    SectionStandingValue,
    SectionTiebreak,
    TournamentRound,
    TournamentSection,
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


def calculate_standings(
    participants: Sequence[SectionParticipant],
    rounds: Sequence[TournamentRound],
    games: Sequence[Game],
    round_records: Sequence[RoundParticipant],
    tiebreaks: Sequence[SectionTiebreak],
) -> list[CalculatedStanding]:
    participant_ids = {participant.id for participant in participants}
    round_numbers = {round_.id: round_.number for round_ in rounds}
    completed_games = _completed_games(games, round_numbers, participant_ids)
    totals, round_points = _participant_totals(
        participant_ids,
        round_numbers,
        completed_games,
        round_records,
    )
    rules = sorted(
        (rule for rule in tiebreaks if rule.is_active),
        key=lambda rule: rule.sequence,
    )
    ranking_values, ranking_keys = _ranking_values(
        participants,
        totals,
        round_points,
        completed_games,
        round_numbers.values(),
        rules,
    )
    ranks = _ranks(ranking_keys)
    return [
        CalculatedStanding(
            participant_id=participant.id,
            rank=ranks[participant.id],
            points=totals[participant.id].points,
            wins=totals[participant.id].wins,
            draws=totals[participant.id].draws,
            losses=totals[participant.id].losses,
            values=ranking_values[participant.id],
        )
        for participant in sorted(participants, key=lambda item: item.id)
    ]


async def recompute_section_standings(
    section_id: int,
    session: AsyncSession,
    through_round_id: int | None = None,
) -> list[SectionStanding]:
    section = await session.get(TournamentSection, section_id)
    if section is None:
        raise StandingInputNotFoundError("Tournament section not found")

    through_round = None
    if through_round_id is not None:
        through_round = await session.get(TournamentRound, through_round_id)
        if through_round is None:
            raise StandingInputNotFoundError("Tournament round not found")
        if through_round.section_id != section_id:
            raise StandingComputationError(
                "Through-round does not belong to the section",
            )

    rounds = await _section_rounds(section_id, session, through_round)
    participants = list(
        (
            await session.scalars(
                select(SectionParticipant)
                .where(SectionParticipant.section_id == section_id)
                .order_by(SectionParticipant.id),
            )
        ).all(),
    )
    round_ids = [round_.id for round_ in rounds]
    games = await _round_games(round_ids, session)
    records = await _round_records(round_ids, session)
    rules = list(
        (
            await session.scalars(
                select(SectionTiebreak)
                .where(
                    SectionTiebreak.section_id == section_id,
                    SectionTiebreak.is_active.is_(True),
                )
                .order_by(SectionTiebreak.sequence),
            )
        ).all(),
    )
    calculated = calculate_standings(
        participants,
        rounds,
        games,
        records,
        rules,
    )
    return await _replace_snapshot(
        section_id,
        through_round_id,
        calculated,
        rules,
        session,
    )


def _completed_games(
    games: Sequence[Game],
    round_numbers: dict[int, int],
    participant_ids: set[int],
) -> list[CompletedGame]:
    completed: list[CompletedGame] = []
    for game in games:
        if game.round_id not in round_numbers:
            raise StandingComputationError("Game is outside the snapshot rounds")
        if (
            game.white_participant_id not in participant_ids
            or game.black_participant_id not in participant_ids
        ):
            raise StandingComputationError(
                "Game participant is not a member of the section",
            )
        if game.white_score is None or game.black_score is None:
            continue
        completed.append(
            CompletedGame(
                round_number=round_numbers[game.round_id],
                white_id=game.white_participant_id,
                black_id=game.black_participant_id,
                white_score=game.white_score,
                black_score=game.black_score,
            ),
        )
    return completed


def _participant_totals(
    participant_ids: set[int],
    round_numbers: dict[int, int],
    games: Sequence[CompletedGame],
    round_records: Sequence[RoundParticipant],
) -> tuple[dict[int, ParticipantTotals], dict[int, dict[int, Decimal]]]:
    totals = {participant_id: ParticipantTotals() for participant_id in participant_ids}
    round_points: dict[int, dict[int, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: ZERO),
    )
    for game in games:
        _add_game_result(totals, round_points, game)
    for record in round_records:
        if record.participant_id not in participant_ids:
            raise StandingComputationError(
                "Round participant is not a member of the section",
            )
        if record.round_id not in round_numbers:
            raise StandingComputationError("Round record is outside the snapshot")
        if (
            record.participation_type != ParticipationType.PAIRED
            and record.score_awarded is not None
        ):
            score = record.score_awarded
            totals[record.participant_id].points += score
            round_points[record.participant_id][round_numbers[record.round_id]] += score
    return totals, round_points


def _add_game_result(
    totals: dict[int, ParticipantTotals],
    round_points: dict[int, dict[int, Decimal]],
    game: CompletedGame,
) -> None:
    white = totals[game.white_id]
    black = totals[game.black_id]
    white.points += game.white_score
    black.points += game.black_score
    round_points[game.white_id][game.round_number] += game.white_score
    round_points[game.black_id][game.round_number] += game.black_score
    if game.white_score > game.black_score:
        white.wins += 1
        black.losses += 1
    elif game.white_score < game.black_score:
        black.wins += 1
        white.losses += 1
    else:
        white.draws += 1
        black.draws += 1


def _ranking_values(
    participants: Sequence[SectionParticipant],
    totals: dict[int, ParticipantTotals],
    round_points: dict[int, dict[int, Decimal]],
    games: Sequence[CompletedGame],
    round_numbers: Iterable[int],
    rules: Sequence[SectionTiebreak],
) -> tuple[dict[int, dict[int, Decimal]], dict[int, tuple[Decimal, ...]]]:
    participant_ids = [participant.id for participant in participants]
    keys = {
        participant_id: (-totals[participant_id].points,)
        for participant_id in participant_ids
    }
    values = {participant_id: {} for participant_id in participant_ids}
    for rule in rules:
        groups = _equal_key_groups(participant_ids, keys)
        rule_values = _tiebreak_values(
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


def _tiebreak_values(
    code: str,
    participant_ids: list[int],
    totals: dict[int, ParticipantTotals],
    round_points: dict[int, dict[int, Decimal]],
    games: Sequence[CompletedGame],
    round_numbers: Iterable[int],
    groups: list[set[int]],
) -> dict[int, Decimal]:
    if code == "direct_encounter":
        return _direct_encounter(participant_ids, games, groups)
    if code == "number_of_wins":
        return {
            participant_id: Decimal(totals[participant_id].wins)
            for participant_id in participant_ids
        }
    if code == "progressive_score":
        return _progressive_scores(participant_ids, round_points, round_numbers)
    if code in {
        "buchholz",
        "buchholz_cut_1",
        "buchholz_cut_2",
        "buchholz_median_1",
        "buchholz_median_2",
    }:
        return _buchholz(code, participant_ids, totals, games)
    if code in {"sonneborn_berger", "sonneborn_berger_cut_1"}:
        return _sonneborn_berger(code, participant_ids, totals, games)
    raise UnsupportedTiebreakError(code)


def _direct_encounter(
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


def _progressive_scores(
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


def _buchholz(
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
        participant_id: sum(_trim_scores(opponents[participant_id], code), ZERO)
        for participant_id in participant_ids
    }


def _sonneborn_berger(
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


def _trim_scores(values: Sequence[Decimal], code: str) -> Sequence[Decimal]:
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


def _equal_key_groups(
    participant_ids: list[int],
    keys: dict[int, tuple[Decimal, ...]],
) -> list[set[int]]:
    groups: dict[tuple[Decimal, ...], set[int]] = defaultdict(set)
    for participant_id in participant_ids:
        groups[keys[participant_id]].add(participant_id)
    return list(groups.values())


def _ranks(keys: dict[int, tuple[Decimal, ...]]) -> dict[int, int]:
    ordered = sorted(
        keys,
        key=lambda participant_id: (keys[participant_id], participant_id),
    )
    ranks: dict[int, int] = {}
    previous_key: tuple[Decimal, ...] | None = None
    current_rank = 0
    for position, participant_id in enumerate(ordered, start=1):
        if keys[participant_id] != previous_key:
            current_rank = position
            previous_key = keys[participant_id]
        ranks[participant_id] = current_rank
    return ranks


async def _section_rounds(
    section_id: int,
    session: AsyncSession,
    through_round: TournamentRound | None,
) -> list[TournamentRound]:
    statement = select(TournamentRound).where(
        TournamentRound.section_id == section_id,
    )
    if through_round is not None:
        statement = statement.where(TournamentRound.number <= through_round.number)
    result = await session.scalars(statement.order_by(TournamentRound.number))
    return list(result.all())


async def _round_games(
    round_ids: Sequence[int],
    session: AsyncSession,
) -> list[Game]:
    if not round_ids:
        return []
    result = await session.scalars(select(Game).where(Game.round_id.in_(round_ids)))
    return list(result.all())


async def _round_records(
    round_ids: Sequence[int],
    session: AsyncSession,
) -> list[RoundParticipant]:
    if not round_ids:
        return []
    result = await session.scalars(
        select(RoundParticipant).where(RoundParticipant.round_id.in_(round_ids)),
    )
    return list(result.all())


async def _replace_snapshot(
    section_id: int,
    through_round_id: int | None,
    calculated: Sequence[CalculatedStanding],
    rules: Sequence[SectionTiebreak],
    session: AsyncSession,
) -> list[SectionStanding]:
    statement = delete(SectionStanding).where(
        SectionStanding.section_id == section_id,
    )
    if through_round_id is None:
        statement = statement.where(SectionStanding.through_round_id.is_(None))
    else:
        statement = statement.where(
            SectionStanding.through_round_id == through_round_id,
        )
    await session.execute(statement)
    computed_at = datetime.now(UTC)
    standings = [
        SectionStanding(
            section_id=section_id,
            participant_id=item.participant_id,
            through_round_id=through_round_id,
            rank=item.rank,
            points=item.points,
            wins=item.wins,
            draws=item.draws,
            losses=item.losses,
            computed_at=computed_at,
            values=[
                SectionStandingValue(
                    tiebreak_id=rule.id,
                    sequence=rule.sequence,
                    value=item.values[rule.id],
                )
                for rule in rules
            ],
        )
        for item in calculated
    ]
    session.add_all(standings)
    await session.flush()
    return standings
