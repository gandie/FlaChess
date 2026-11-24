from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Game,
    ParticipationType,
    RoundParticipant,
    TournamentRound,
)
from app.pairing.generation_plan import prepare_pairing_plan
from app.pairing.generation_state import (
    PairingGenerationConflict,
    load_generation_state,
)
from app.pairing.types import PairingPlan, PlannedOutcomeType


@dataclass(frozen=True)
class GeneratedRound:
    round: TournamentRound
    games: tuple[Game, ...]
    records: tuple[RoundParticipant, ...]
    plan: PairingPlan


async def generate_next_round(
    section_id: int,
    session: AsyncSession,
    expected_round_number: int | None = None,
) -> GeneratedRound:
    try:
        state = await load_generation_state(section_id, session)
        plan, _ = prepare_pairing_plan(state, expected_round_number)
        generated = await persist_plan(state.section.id, plan, session)
        await session.commit()
        return generated
    except IntegrityError as error:
        await session.rollback()
        raise PairingGenerationConflict(
            "The generated round conflicts with existing persistent data.",
        ) from error
    except Exception:
        await session.rollback()
        raise


async def persist_plan(
    section_id: int,
    plan: PairingPlan,
    session: AsyncSession,
) -> GeneratedRound:
    round_ = TournamentRound(section_id=section_id, number=plan.round_number)
    session.add(round_)
    await session.flush()
    games = tuple(
        Game(
            round_id=round_.id,
            white_participant_id=game.white_participant_id,
            black_participant_id=game.black_participant_id,
        )
        for game in plan.games
    )
    paired_records = tuple(
        record
        for game in games
        for record in paired_participant_records(round_.id, game)
    )
    outcome_records = tuple(
        RoundParticipant(
            round_id=round_.id,
            participant_id=outcome.participant_id,
            participation_type=participation_type(outcome.outcome_type),
            score_awarded=outcome.score_awarded,
        )
        for outcome in plan.outcomes
    )
    records = (*paired_records, *outcome_records)
    session.add_all((*games, *records))
    return GeneratedRound(round_, games, records, plan)


def paired_participant_records(
    round_id: int,
    game: Game,
) -> tuple[RoundParticipant, RoundParticipant]:
    return (
        RoundParticipant(
            round_id=round_id,
            participant_id=game.white_participant_id,
            participation_type=ParticipationType.PAIRED,
        ),
        RoundParticipant(
            round_id=round_id,
            participant_id=game.black_participant_id,
            participation_type=ParticipationType.PAIRED,
        ),
    )


def participation_type(value: PlannedOutcomeType) -> ParticipationType:
    if value is PlannedOutcomeType.BYE:
        return ParticipationType.BYE
    if value is PlannedOutcomeType.UNPLAYED:
        return ParticipationType.UNPLAYED
    return ParticipationType.ABSENT
