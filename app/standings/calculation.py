from typing import Sequence

from app.models import (
    Game,
    RoundParticipant,
    SectionParticipant,
    SectionTiebreak,
    TournamentRound,
)
from app.standings.ranking import ranking_values, ranks
from app.standings.totals import completed_games, participant_totals
from app.standings.types import CalculatedStanding


def calculate_standings(
    participants: Sequence[SectionParticipant],
    rounds: Sequence[TournamentRound],
    games: Sequence[Game],
    round_records: Sequence[RoundParticipant],
    tiebreaks: Sequence[SectionTiebreak],
) -> list[CalculatedStanding]:
    participant_ids = {participant.id for participant in participants}
    round_numbers = {round_.id: round_.number for round_ in rounds}
    completed = completed_games(games, round_numbers, participant_ids)
    totals, round_points = participant_totals(
        participant_ids,
        round_numbers,
        completed,
        round_records,
    )
    rules = sorted(
        (rule for rule in tiebreaks if rule.is_active),
        key=lambda rule: rule.sequence,
    )
    ranking, ranking_keys = ranking_values(
        [participant.id for participant in participants],
        totals,
        round_points,
        completed,
        round_numbers.values(),
        rules,
    )
    calculated_ranks = ranks(ranking_keys)
    return [
        CalculatedStanding(
            participant_id=participant.id,
            rank=calculated_ranks[participant.id],
            points=totals[participant.id].points,
            wins=totals[participant.id].wins,
            draws=totals[participant.id].draws,
            losses=totals[participant.id].losses,
            values=ranking[participant.id],
        )
        for participant in sorted(participants, key=lambda item: item.id)
    ]
