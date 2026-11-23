from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import SectionLifecycle, SectionTiebreak, TournamentSection
from app.schemas import (
    SectionTiebreakCreate,
    SectionTiebreakResponse,
    SectionTiebreakUpdate,
)

router = APIRouter()


async def validate_section_is_draft(
    section_id: int,
    session: AsyncSession,
) -> None:
    lifecycle = await session.scalar(
        select(TournamentSection.lifecycle).where(
            TournamentSection.id == section_id,
        ),
    )
    if lifecycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    if lifecycle is not SectionLifecycle.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section tie-break configuration is locked",
        )


async def commit_tiebreak(
    tiebreak: SectionTiebreak,
    session: AsyncSession,
) -> SectionTiebreak:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section tie-break configuration violates a constraint",
        ) from error
    return tiebreak


@router.post(
    "/section-tiebreaks",
    response_model=SectionTiebreakResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_section_tiebreak(
    payload: SectionTiebreakCreate,
    session: AsyncSession = Depends(get_session),
) -> SectionTiebreak:
    await validate_section_is_draft(payload.section_id, session)
    tiebreak = SectionTiebreak(**payload.model_dump())
    session.add(tiebreak)
    return await commit_tiebreak(tiebreak, session)


@router.patch(
    "/section-tiebreaks/{id}",
    response_model=SectionTiebreakResponse,
)
async def update_section_tiebreak(
    id: int,
    payload: SectionTiebreakUpdate,
    session: AsyncSession = Depends(get_session),
) -> SectionTiebreak:
    tiebreak = await session.get(SectionTiebreak, id)
    if tiebreak is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section tie-break not found",
        )

    await validate_section_is_draft(tiebreak.section_id, session)
    values = payload.model_dump(exclude_unset=True)
    target_section_id = values.get("section_id", tiebreak.section_id)
    if target_section_id != tiebreak.section_id:
        await validate_section_is_draft(target_section_id, session)
    for field, value in values.items():
        setattr(tiebreak, field, value)
    return await commit_tiebreak(tiebreak, session)


@router.delete(
    "/section-tiebreaks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_section_tiebreak(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    tiebreak = await session.get(SectionTiebreak, id)
    if tiebreak is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section tie-break not found",
        )
    await validate_section_is_draft(tiebreak.section_id, session)
    await session.delete(tiebreak)
    await session.commit()
