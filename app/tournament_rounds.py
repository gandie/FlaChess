from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SectionParticipant, TournamentRound


async def round_section_id(
    round_id: int,
    session: AsyncSession,
) -> int | None:
    return await session.scalar(
        select(TournamentRound.section_id).where(TournamentRound.id == round_id),
    )


async def participant_section_id(
    participant_id: int,
    session: AsyncSession,
) -> int | None:
    return await session.scalar(
        select(SectionParticipant.section_id).where(
            SectionParticipant.id == participant_id,
        ),
    )


async def game_section_ids(
    round_id: int,
    white_participant_id: int,
    black_participant_id: int,
    session: AsyncSession,
) -> tuple[int | None, int | None, int | None]:
    return (
        await round_section_id(round_id, session),
        await participant_section_id(white_participant_id, session),
        await participant_section_id(black_participant_id, session),
    )
