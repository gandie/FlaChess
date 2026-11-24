from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SectionParticipant


class SectionMembershipValidationError(ValueError):
    pass


async def ensure_seed_position_available(
    section_id: int,
    seed_position: int | None,
    session: AsyncSession,
    *,
    membership_id: int | None = None,
) -> None:
    if seed_position is None:
        return

    statement = select(SectionParticipant.id).where(
        SectionParticipant.section_id == section_id,
        SectionParticipant.seed_position == seed_position,
    )
    if membership_id is not None:
        statement = statement.where(SectionParticipant.id != membership_id)
    conflict_id = await session.scalar(statement)
    if conflict_id is not None:
        raise SectionMembershipValidationError(
            f"Seed position {seed_position} is already assigned in this section.",
        )


def validate_pairing_seed_positions(
    memberships: Iterable[tuple[int | None, bool]],
) -> None:
    eligible_seeds = [
        seed_position
        for seed_position, is_withdrawn in memberships
        if not is_withdrawn
    ]
    if len(eligible_seeds) < 2:
        return
    if any(seed_position is None for seed_position in eligible_seeds):
        raise SectionMembershipValidationError(
            "Every eligible participant needs a seed position before section "
            "activation.",
        )
    if any(seed_position <= 0 for seed_position in eligible_seeds):
        raise SectionMembershipValidationError(
            "Seed positions must be positive integers.",
        )
    if len(set(eligible_seeds)) != len(eligible_seeds):
        raise SectionMembershipValidationError(
            "Seed positions must be unique within a section.",
        )
