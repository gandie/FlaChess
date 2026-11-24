from __future__ import annotations

from app.models import (
    Game,
    ParticipationType,
    RoundParticipant,
    SectionParticipant,
    TournamentRound,
)
from app.pairing.generation_history import round_participant_ids
from app.pairing.generation_state import (
    GenerationState,
    PairingGenerationConflict,
    PairingGenerationError,
)
from app.pairing.knockout import standard_seed_slots
from app.pairing.types import KnockoutPredecessor


def first_round_field(
    state: GenerationState,
) -> tuple[SectionParticipant, ...]:
    initial_ids = round_participant_ids(
        state.rounds[0],
        state.games,
        state.records,
    )
    participants = tuple(
        participant
        for participant in state.participants
        if participant.id in initial_ids
    )
    if {participant.id for participant in participants} != initial_ids:
        raise PairingGenerationConflict(
            "The knockout entrants cannot be reconstructed from round 1.",
        )
    active_newcomers = {
        participant.id
        for participant in state.participants
        if not participant.is_withdrawn
    } - initial_ids
    if active_newcomers:
        raise PairingGenerationConflict(
            "Knockout membership cannot be added after round 1.",
        )
    return participants


def knockout_predecessors(
    state: GenerationState,
) -> tuple[KnockoutPredecessor, ...]:
    previous = state.rounds[-1]
    if previous.number == 1:
        return first_round_predecessors(state, previous)
    return tuple(
        KnockoutPredecessor(
            game.white_participant_id,
            game.black_participant_id,
            game.white_score,
            game.black_score,
        )
        for game in state.games
        if game.round_id == previous.id
    )


def first_round_predecessors(
    state: GenerationState,
    round_: TournamentRound,
) -> tuple[KnockoutPredecessor, ...]:
    entrants = first_round_field(state)
    participants = {
        participant.seed_position: participant
        for participant in entrants
    }
    round_games = [game for game in state.games if game.round_id == round_.id]
    round_records = [
        record for record in state.records if record.round_id == round_.id
    ]
    slots = standard_seed_slots(1 << (len(participants) - 1).bit_length())
    return tuple(
        bracket_predecessor(
            participants.get(slots[index]),
            participants.get(slots[index + 1]),
            round_games,
            round_records,
        )
        for index in range(0, len(slots), 2)
    )


def bracket_predecessor(
    first: SectionParticipant | None,
    second: SectionParticipant | None,
    games: list[Game],
    records: list[RoundParticipant],
) -> KnockoutPredecessor:
    if first is None and second is None:
        raise PairingGenerationError(
            "The knockout bracket contains an empty match.",
        )
    if first is None or second is None:
        return structural_bye(first, second, records)
    game = find_bracket_game(first.id, second.id, games)
    first_score = (
        game.white_score
        if game.white_participant_id == first.id
        else game.black_score
    )
    second_score = (
        game.white_score
        if game.white_participant_id == second.id
        else game.black_score
    )
    return KnockoutPredecessor(first.id, second.id, first_score, second_score)


def structural_bye(
    first: SectionParticipant | None,
    second: SectionParticipant | None,
    records: list[RoundParticipant],
) -> KnockoutPredecessor:
    participant = first if second is None else second
    assert participant is not None
    has_bye = any(
        record.participant_id == participant.id
        and record.participation_type is ParticipationType.BYE
        for record in records
    )
    if not has_bye:
        raise PairingGenerationConflict(
            "Round 1 is missing a knockout structural bye record.",
        )
    return KnockoutPredecessor(participant.id)


def find_bracket_game(
    first_id: int,
    second_id: int,
    games: list[Game],
) -> Game:
    game = next(
        (
            item
            for item in games
            if {
                item.white_participant_id,
                item.black_participant_id,
            }
            == {first_id, second_id}
        ),
        None,
    )
    if game is None:
        raise PairingGenerationConflict(
            "Round 1 does not match the seeded knockout bracket.",
        )
    return game
