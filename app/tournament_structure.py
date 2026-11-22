from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TournamentParticipant, TournamentPhase, TournamentSection


async def membership_tournament_ids(
    participant_id: int,
    section_id: int,
    session: AsyncSession,
) -> tuple[int | None, int | None]:
    participant_tournament_id = await session.scalar(
        select(TournamentParticipant.tournament_id).where(
            TournamentParticipant.id == participant_id,
        ),
    )
    section_tournament_id = await session.scalar(
        select(TournamentPhase.tournament_id)
        .select_from(TournamentSection)
        .join(TournamentPhase, TournamentSection.phase_id == TournamentPhase.id)
        .where(TournamentSection.id == section_id),
    )
    return participant_tournament_id, section_tournament_id
