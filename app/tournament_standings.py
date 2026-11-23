from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SectionStanding
from app.standings.calculation import calculate_standings
from app.standings.persistence import (
    load_snapshot_inputs,
    replace_snapshot,
    validate_through_round,
)
from app.standings.types import (
    StandingComputationError,
    StandingInputNotFoundError,
    UnsupportedTiebreakError,
)


async def recompute_section_standings(
    section_id: int,
    session: AsyncSession,
    through_round_id: int | None = None,
) -> list[SectionStanding]:
    through_round = await validate_through_round(
        section_id,
        through_round_id,
        session,
    )
    inputs = await load_snapshot_inputs(section_id, through_round, session)
    calculated = calculate_standings(
        inputs.participants,
        inputs.rounds,
        inputs.games,
        inputs.records,
        inputs.rules,
    )
    return await replace_snapshot(
        section_id,
        through_round_id,
        calculated,
        inputs.rules,
        session,
    )


__all__ = [
    "StandingComputationError",
    "StandingInputNotFoundError",
    "UnsupportedTiebreakError",
    "calculate_standings",
    "recompute_section_standings",
]
