from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import SectionParticipant
from app.schemas import (
    SectionParticipantCreate,
    SectionParticipantResponse,
    SectionParticipantUpdate,
)
from app.tournament_structure import membership_tournament_ids
from app.section_memberships import (
    SectionMembershipValidationError,
    ensure_seed_position_available,
)

router = APIRouter()


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


async def validate_seed_position(
    section_id: int,
    seed_position: int | None,
    session: AsyncSession,
    *,
    membership_id: int | None = None,
) -> None:
    try:
        await ensure_seed_position_available(
            section_id,
            seed_position,
            session,
            membership_id=membership_id,
        )
    except SectionMembershipValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


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
    await validate_seed_position(
        payload.section_id,
        payload.seed_position,
        session,
    )
    membership = SectionParticipant(**payload.model_dump(), is_withdrawn=False)
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
    seed_position = values.get("seed_position", membership.seed_position)
    await validate_seed_position(
        section_id,
        seed_position,
        session,
        membership_id=membership.id,
    )
    for field, value in values.items():
        setattr(membership, field, value)
    return await commit_section_membership(membership, session)


async def set_membership_withdrawal(
    id: int,
    is_withdrawn: bool,
    session: AsyncSession,
) -> SectionParticipant:
    membership = await session.get(SectionParticipant, id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )
    membership.is_withdrawn = is_withdrawn
    await session.commit()
    return membership


@router.post(
    "/section-participants/{id}/withdraw",
    response_model=SectionParticipantResponse,
)
async def withdraw_section_participant(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    return await set_membership_withdrawal(id, True, session)


@router.post(
    "/section-participants/{id}/re-enter",
    response_model=SectionParticipantResponse,
)
async def reenter_section_participant(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    return await set_membership_withdrawal(id, False, session)
