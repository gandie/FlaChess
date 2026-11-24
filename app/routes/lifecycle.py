from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.lifecycle import (
    LifecycleTransitionError,
    transition_section,
    transition_tournament,
)
from app.models import (
    SectionParticipant,
    SectionLifecycle,
    Tournament,
    TournamentLifecycle,
    TournamentSection,
)
from app.section_memberships import (
    SectionMembershipValidationError,
    validate_pairing_seed_positions,
)
from app.schemas import (
    SectionTransitionResponse,
    TournamentTransitionResponse,
)

router = APIRouter()


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
    except LifecycleTransitionError as error:
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


async def apply_section_transition(
    id: int,
    target: SectionLifecycle,
    session: AsyncSession,
) -> TournamentSection:
    section = await session.scalar(
        select(TournamentSection).where(TournamentSection.id == id),
    )
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )

    try:
        if target is SectionLifecycle.ACTIVE:
            result = await session.execute(
                select(
                    SectionParticipant.seed_position,
                    SectionParticipant.is_withdrawn,
                ).where(SectionParticipant.section_id == section.id),
            )
            validate_pairing_seed_positions(result.all())
        await transition_section(section, target, session)
    except (LifecycleTransitionError, SectionMembershipValidationError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    await session.commit()
    return section


@router.post(
    "/tournament-sections/{id}/activate",
    response_model=SectionTransitionResponse,
)
async def activate_section(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> TournamentSection:
    return await apply_section_transition(
        id,
        SectionLifecycle.ACTIVE,
        session,
    )


@router.post(
    "/tournament-sections/{id}/finish",
    response_model=SectionTransitionResponse,
)
async def finish_section(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> TournamentSection:
    return await apply_section_transition(
        id,
        SectionLifecycle.FINISHED,
        session,
    )
