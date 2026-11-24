from __future__ import annotations

from collections import Counter

from app.models import (
    Game,
    ParticipationType,
    RoundParticipant,
    TournamentRound,
)
from app.pairing.generation_state import (
    GenerationState,
    PairingGenerationConflict,
)


def validate_history(state: GenerationState) -> None:
    member_ids = {participant.id for participant in state.participants}
    for round_ in state.rounds:
        validate_completed_round(
            round_,
            state.games,
            state.records,
            member_ids,
        )


def validate_completed_round(
    round_: TournamentRound,
    games: tuple[Game, ...],
    records: tuple[RoundParticipant, ...],
    member_ids: set[int],
) -> None:
    round_games = [game for game in games if game.round_id == round_.id]
    round_records = [
        record for record in records if record.round_id == round_.id
    ]
    if not round_games and not round_records:
        raise PairingGenerationConflict(
            f"Round {round_.number} has no games or participation records.",
        )
    game_participants = validate_games(round_, round_games, member_ids)
    validate_records(round_, round_records, game_participants, member_ids)


def validate_games(
    round_: TournamentRound,
    games: list[Game],
    member_ids: set[int],
) -> set[int]:
    appearances: list[int] = []
    for game in games:
        pair = (game.white_participant_id, game.black_participant_id)
        if not set(pair) <= member_ids:
            raise PairingGenerationConflict(
                f"Round {round_.number} contains a participant "
                "from another section.",
            )
        if game.white_score is None or game.black_score is None:
            raise PairingGenerationConflict(
                f"Round {round_.number} is incomplete.",
            )
        appearances.extend(pair)
    duplicated = participant_duplicates(appearances)
    if duplicated:
        raise PairingGenerationConflict(
            f"Round {round_.number} pairs a participant more than once.",
        )
    return set(appearances)


def validate_records(
    round_: TournamentRound,
    records: list[RoundParticipant],
    game_participants: set[int],
    member_ids: set[int],
) -> None:
    ids = [record.participant_id for record in records]
    if participant_duplicates(ids):
        raise PairingGenerationConflict(
            f"Round {round_.number} contains duplicate participation records.",
        )
    for record in records:
        if record.participant_id not in member_ids:
            raise PairingGenerationConflict(
                f"Round {round_.number} contains a participant "
                "from another section.",
            )
        paired = record.participation_type is ParticipationType.PAIRED
        in_game = record.participant_id in game_participants
        if paired != in_game:
            raise PairingGenerationConflict(
                f"Round {round_.number} has conflicting game participation.",
            )


def participant_duplicates(participant_ids: list[int]) -> list[int]:
    return [
        participant_id
        for participant_id, count in Counter(participant_ids).items()
        if count > 1
    ]


def round_participant_ids(
    round_: TournamentRound,
    games: tuple[Game, ...],
    records: tuple[RoundParticipant, ...],
) -> set[int]:
    ids = {
        participant_id
        for game in games
        if game.round_id == round_.id
        for participant_id in (
            game.white_participant_id,
            game.black_participant_id,
        )
    }
    ids.update(
        record.participant_id
        for record in records
        if record.round_id == round_.id
    )
    return ids
