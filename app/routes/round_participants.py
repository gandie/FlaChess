from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import ParticipationType, RoundParticipant
from app.routes.round_records import commit_round_record
from app.schemas import (
    RoundParticipantCreate,
    RoundParticipantResponse,
    RoundParticipantUpdate,
)
from app.tournament_rounds import participant_section_id, round_section_id

router = APIRouter()


async def validate_round_member(
    round_id: int,
    participant_id: int,
    session: AsyncSession,
) -> None:
    actual_round_section_id = await round_section_id(round_id, session)
    actual_participant_section_id = await participant_section_id(
        participant_id,
        session,
    )
    if actual_round_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament round not found",
        )
    if actual_participant_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )
    if actual_round_section_id != actual_participant_section_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant does not belong to the round's section",
        )


@router.post(
    "/round-participants",
    response_model=RoundParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_round_participant(
    payload: RoundParticipantCreate,
    session: AsyncSession = Depends(get_session),
) -> RoundParticipant:
    await validate_round_member(
        payload.round_id,
        payload.participant_id,
        session,
    )
    record = RoundParticipant(**payload.model_dump())
    session.add(record)
    await commit_round_record(record, session)
    return record


@router.patch(
    "/round-participants/{id}",
    response_model=RoundParticipantResponse,
)
async def update_round_participant(
    id: int,
    payload: RoundParticipantUpdate,
    session: AsyncSession = Depends(get_session),
) -> RoundParticipant:
    record = await session.get(RoundParticipant, id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round participant not found",
        )

    values = payload.model_dump(exclude_unset=True)
    round_id = values.get("round_id", record.round_id)
    participant_id = values.get("participant_id", record.participant_id)
    await validate_round_member(round_id, participant_id, session)
    participation_type = values.get(
        "participation_type",
        record.participation_type,
    )
    score_awarded = values.get("score_awarded", record.score_awarded)
    if participation_type == ParticipationType.PAIRED and score_awarded is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="paired participation cannot have score_awarded",
        )
    for field, value in values.items():
        setattr(record, field, value)
    await commit_round_record(record, session)
    return record
