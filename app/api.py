from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import (
    SectionStanding,
    TournamentRound,
    TournamentSection,
)
from app.routes.crud import router as crud_router
from app.routes.games import router as games_router
from app.routes.lifecycle import router as lifecycle_router
from app.routes.memberships import router as memberships_router
from app.routes.player_registration import router as player_registration_router
from app.routes.round_participants import router as round_participants_router
from app.routes.tournament_catalog import router as tournament_catalog_router
from app.routes.tiebreaks import router as tiebreaks_router
from app.schemas import SectionStandingResponse
from app.tournament_standings import (
    StandingComputationError,
    StandingInputNotFoundError,
    recompute_section_standings,
)

router = APIRouter()
router.include_router(crud_router)
router.include_router(tiebreaks_router)
router.include_router(memberships_router)
router.include_router(round_participants_router)
router.include_router(games_router)
router.include_router(lifecycle_router)
router.include_router(tournament_catalog_router)
router.include_router(player_registration_router)


@router.get(
    "/tournament-sections/{section_id}/standings",
    response_model=list[SectionStandingResponse],
)
async def get_section_standings(
    section_id: int,
    through_round_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[SectionStanding]:
    section = await session.get(TournamentSection, section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    if through_round_id is not None:
        through_round = await session.get(TournamentRound, through_round_id)
        if through_round is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tournament round not found",
            )
        if through_round.section_id != section_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Through-round does not belong to the section",
            )

    statement = select(SectionStanding).where(
        SectionStanding.section_id == section_id,
    )
    if through_round_id is None:
        statement = statement.where(SectionStanding.through_round_id.is_(None))
    else:
        statement = statement.where(
            SectionStanding.through_round_id == through_round_id,
        )
    standings = await session.scalars(
        statement.order_by(SectionStanding.rank, SectionStanding.id),
    )
    return list(standings.all())


@router.post(
    "/tournament-sections/{section_id}/standings/recompute",
    response_model=list[SectionStandingResponse],
)
async def recompute_standings(
    section_id: int,
    through_round_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[SectionStanding]:
    try:
        standings = await recompute_section_standings(
            section_id,
            session,
            through_round_id,
        )
        await session.commit()
    except StandingInputNotFoundError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (StandingComputationError, IntegrityError) as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error) or "Standings violate a database constraint",
        ) from error
    return standings


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
