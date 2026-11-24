from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import (
    Player,
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
)
from app.player_registration_schemas import (
    PlayerSummary,
    TournamentParticipantRegistration,
    TournamentParticipantSummary,
)

router = APIRouter()


@router.get(
    "/player-summaries",
    response_model=list[PlayerSummary],
    tags=["Players"],
)
async def list_player_summaries(
    session: AsyncSession = Depends(get_session),
) -> list[PlayerSummary]:
    result = await session.execute(
        select(Player.id, Player.name).order_by(Player.name, Player.id),
    )
    return [PlayerSummary.model_validate(row) for row in result.all()]


async def get_tournament(
    tournament_id: int,
    session: AsyncSession,
) -> Tournament:
    tournament = await session.get(Tournament, tournament_id)
    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )
    return tournament


def require_draft(tournament: Tournament) -> None:
    if tournament.lifecycle != TournamentLifecycle.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player registration is available only for draft tournaments",
        )


async def get_player(player_id: int, session: AsyncSession) -> Player:
    player = await session.get(Player, player_id)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    return player


@router.get(
    "/tournaments/{tournament_id}/participants",
    response_model=list[TournamentParticipantSummary],
    tags=["Tournament Participants"],
)
async def list_tournament_participants(
    tournament_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[TournamentParticipantSummary]:
    await get_tournament(tournament_id, session)
    result = await session.execute(
        select(
            TournamentParticipant.id.label("registration_id"),
            TournamentParticipant.player_id,
            Player.name.label("player_name"),
        )
        .join(Player, Player.id == TournamentParticipant.player_id)
        .where(TournamentParticipant.tournament_id == tournament_id)
        .order_by(Player.name, TournamentParticipant.id),
    )
    return [
        TournamentParticipantSummary.model_validate(row)
        for row in result.all()
    ]


@router.post(
    "/tournaments/{tournament_id}/participants",
    response_model=TournamentParticipantSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Tournament Participants"],
)
async def register_tournament_participant(
    tournament_id: int,
    payload: TournamentParticipantRegistration,
    session: AsyncSession = Depends(get_session),
) -> TournamentParticipantSummary:
    tournament = await get_tournament(tournament_id, session)
    require_draft(tournament)
    player = await get_player(payload.player_id, session)
    registration = TournamentParticipant(
        tournament_id=tournament_id,
        player_id=player.id,
    )
    session.add(registration)
    try:
        await session.commit()
        await session.refresh(registration)
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player is already registered for this tournament",
        ) from error
    return TournamentParticipantSummary(
        registration_id=registration.id,
        player_id=player.id,
        player_name=player.name,
    )


@router.delete(
    "/tournaments/{tournament_id}/participants/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tournament Participants"],
)
async def unregister_tournament_participant(
    tournament_id: int,
    registration_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    tournament = await get_tournament(tournament_id, session)
    require_draft(tournament)
    registration = await session.get(TournamentParticipant, registration_id)
    if registration is None or registration.tournament_id != tournament_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament participant not found",
        )
    await session.delete(registration)
    await session.commit()
