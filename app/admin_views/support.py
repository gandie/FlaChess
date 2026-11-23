from typing import Any

from sqlalchemy import select

from app.models import SectionLifecycle, TournamentSection


async def ensure_section_is_draft(
    session_maker: Any,
    section_id: int,
) -> None:
    async with session_maker() as session:
        lifecycle = await session.scalar(
            select(TournamentSection.lifecycle).where(
                TournamentSection.id == section_id,
            ),
        )
    if lifecycle is None:
        raise ValueError("Section no longer exists")
    if lifecycle is not SectionLifecycle.DRAFT:
        raise ValueError("Section tie-break configuration is locked")
