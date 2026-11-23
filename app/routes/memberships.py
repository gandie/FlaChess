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
