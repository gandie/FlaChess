from collections import defaultdict
from decimal import Decimal
from typing import Sequence

from app.models import Game, ParticipationType, RoundParticipant
from app.standings.types import (
    ZERO,
    CompletedGame,
    ParticipantTotals,
    StandingComputationError,
)


def completed_games(
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


def participant_totals(
    participant_ids: set[int],
    round_numbers: dict[int, int],
    games: Sequence[CompletedGame],
    round_records: Sequence[RoundParticipant],
) -> tuple[dict[int, ParticipantTotals], dict[int, dict[int, Decimal]]]:
    totals = {
        participant_id: ParticipantTotals()
        for participant_id in participant_ids
    }
    round_points: dict[int, dict[int, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: ZERO),
    )
    for game in games:
        add_game_result(totals, round_points, game)
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


def add_game_result(
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
