from fastapi import APIRouter, Depends, HTTPException, status
from fastcrud import crud_router
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.lifecycle import TournamentTransitionError, transition_tournament
from app.models import (
    Player,
    SectionParticipant,
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
    TournamentPhase,
    TournamentSection,
)
from app.schemas import (
    PlayerCreate,
    PlayerUpdate,
    SectionParticipantCreate,
    SectionParticipantResponse,
    SectionParticipantUpdate,
    TournamentCreate,
    TournamentParticipantCreate,
    TournamentParticipantUpdate,
    TournamentPhaseCreate,
    TournamentPhaseUpdate,
    TournamentSectionCreate,
    TournamentSectionUpdate,
    TournamentTransitionResponse,
    TournamentUpdate,
)
from app.tournament_structure import membership_tournament_ids

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

tournament_phase_router = crud_router(
    session=get_session,
    model=TournamentPhase,
    create_schema=TournamentPhaseCreate,
    update_schema=TournamentPhaseUpdate,
    path="/tournament-phases",
    tags=["Tournament Phases"],
)
router.include_router(tournament_phase_router)

tournament_section_router = crud_router(
    session=get_session,
    model=TournamentSection,
    create_schema=TournamentSectionCreate,
    update_schema=TournamentSectionUpdate,
    path="/tournament-sections",
    tags=["Tournament Sections"],
)
router.include_router(tournament_section_router)

section_participant_router = crud_router(
    session=get_session,
    model=SectionParticipant,
    create_schema=SectionParticipantCreate,
    update_schema=SectionParticipantUpdate,
    path="/section-participants",
    tags=["Section Participants"],
    deleted_methods=["create", "update"],
)
router.include_router(section_participant_router)


async def validate_section_membership(
    participant_id: int,
    section_id: int,
    session: AsyncSession,
) -> None:
    (
        participant_tournament_id,
        section_tournament_id,
    ) = await membership_tournament_ids(participant_id, section_id, session)
    if participant_tournament_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament participant not found",
        )

    if section_tournament_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    if participant_tournament_id != section_tournament_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant and section belong to different tournaments",
        )


async def commit_section_membership(
    membership: SectionParticipant,
    session: AsyncSession,
) -> SectionParticipant:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section participant membership violates a database constraint",
        ) from error
    return membership


@router.post(
    "/section-participants",
    response_model=SectionParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_section_participant(
    payload: SectionParticipantCreate,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    await validate_section_membership(
        payload.participant_id,
        payload.section_id,
        session,
    )
    membership = SectionParticipant(**payload.model_dump())
    session.add(membership)
    return await commit_section_membership(membership, session)


@router.patch(
    "/section-participants/{id}",
    response_model=SectionParticipantResponse,
)
async def update_section_participant(
    id: int,
    payload: SectionParticipantUpdate,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    membership = await session.get(SectionParticipant, id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )

    values = payload.model_dump(exclude_unset=True)
    participant_id = values.get("participant_id", membership.participant_id)
    section_id = values.get("section_id", membership.section_id)
    await validate_section_membership(participant_id, section_id, session)
    for field, value in values.items():
        setattr(membership, field, value)
    return await commit_section_membership(membership, session)


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
