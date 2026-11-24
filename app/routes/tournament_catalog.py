from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import (
    Tournament,
    TournamentParticipant,
    TournamentPhase,
    TournamentSection,
)
from app.schemas import TournamentSummary

router = APIRouter()


@router.get(
    "/tournament-summaries",
    response_model=list[TournamentSummary],
    tags=["Tournaments"],
)
async def list_tournament_summaries(
    session: AsyncSession = Depends(get_session),
) -> list[TournamentSummary]:
    participant_count = (
        select(func.count(TournamentParticipant.id))
        .where(TournamentParticipant.tournament_id == Tournament.id)
        .correlate(Tournament)
        .scalar_subquery()
    )
    phase_count = (
        select(func.count(TournamentPhase.id))
        .where(TournamentPhase.tournament_id == Tournament.id)
        .correlate(Tournament)
        .scalar_subquery()
    )
    section_count = (
        select(func.count(TournamentSection.id))
        .join(TournamentPhase, TournamentSection.phase_id == TournamentPhase.id)
        .where(TournamentPhase.tournament_id == Tournament.id)
        .correlate(Tournament)
        .scalar_subquery()
    )
    statement = select(
        Tournament.id,
        Tournament.name,
        Tournament.description,
        Tournament.lifecycle,
        Tournament.time_control,
        Tournament.starts_at,
        Tournament.ends_at,
        participant_count.label("participant_count"),
        phase_count.label("phase_count"),
        section_count.label("section_count"),
    ).order_by(Tournament.starts_at.nulls_last(), Tournament.id)

    result = await session.execute(statement)
    return [
        TournamentSummary.model_validate(row)
        for row in result.all()
    ]
