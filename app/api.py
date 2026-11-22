from fastapi import APIRouter, Depends, HTTPException, status
from fastcrud import crud_router
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.lifecycle import TournamentTransitionError, transition_tournament
from app.models import Player, Tournament, TournamentLifecycle, TournamentParticipant
from app.schemas import (
    PlayerCreate,
    PlayerUpdate,
    TournamentCreate,
    TournamentParticipantCreate,
    TournamentParticipantUpdate,
    TournamentTransitionResponse,
    TournamentUpdate,
)

router = APIRouter()

player_router = crud_router(
    session=get_session,
    model=Player,
    create_schema=PlayerCreate,
    update_schema=PlayerUpdate,
    path="/players",
    tags=["Players"],
)
router.include_router(player_router)

tournament_router = crud_router(
    session=get_session,
    model=Tournament,
    create_schema=TournamentCreate,
    update_schema=TournamentUpdate,
    path="/tournaments",
    tags=["Tournaments"],
)
router.include_router(tournament_router)

tournament_participant_router = crud_router(
    session=get_session,
    model=TournamentParticipant,
    create_schema=TournamentParticipantCreate,
    update_schema=TournamentParticipantUpdate,
    path="/tournament-participants",
    tags=["Tournament Participants"],
)
router.include_router(tournament_participant_router)


async def apply_tournament_transition(
    id: int,
    target: TournamentLifecycle,
    session: AsyncSession,
) -> Tournament:
    tournament = await session.scalar(select(Tournament).where(Tournament.id == id))
    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    try:
        await transition_tournament(tournament, target, session)
    except TournamentTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    await session.commit()
    return tournament


@router.post(
    "/tournaments/{id}/activate",
    response_model=TournamentTransitionResponse,
)
async def activate_tournament(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> Tournament:
    return await apply_tournament_transition(
        id,
        TournamentLifecycle.ACTIVE,
        session,
    )


@router.post(
    "/tournaments/{id}/finish",
    response_model=TournamentTransitionResponse,
)
async def finish_tournament(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> Tournament:
    return await apply_tournament_transition(
        id,
        TournamentLifecycle.FINISHED,
        session,
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
