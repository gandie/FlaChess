from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game, RoundParticipant


async def commit_round_record(
    record: RoundParticipant | Game,
    session: AsyncSession,
) -> RoundParticipant | Game:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Round record violates a database constraint",
        ) from error
    return record
