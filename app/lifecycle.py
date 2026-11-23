from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Generic, Protocol, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
    TournamentSection,
    SectionLifecycle,
)


LifecycleState = TypeVar("LifecycleState", bound=Enum)


class LifecycleEntity(Protocol[LifecycleState]):
    lifecycle: LifecycleState


LifecycleHook = Callable[
    [LifecycleEntity[LifecycleState], LifecycleState, AsyncSession],
    Awaitable[None],
]


class LifecycleTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class LifecycleMachine(Generic[LifecycleState]):
    allowed_transitions: Mapping[
        LifecycleState,
        frozenset[LifecycleState],
    ]
    on_leave: LifecycleHook[LifecycleState] | None = None
    on_enter: LifecycleHook[LifecycleState] | None = None

    async def transition(
        self,
        entity: LifecycleEntity[LifecycleState],
        target: LifecycleState,
        session: AsyncSession,
    ) -> LifecycleEntity[LifecycleState]:
        current = entity.lifecycle
        if target not in self.allowed_transitions[current]:
            raise LifecycleTransitionError(
                f"Cannot transition from {current.value} to {target.value}."
            )

        if self.on_leave is not None:
            await self.on_leave(entity, target, session)
        entity.lifecycle = target
        if self.on_enter is not None:
            await self.on_enter(entity, target, session)
        return entity


TournamentTransitionError = LifecycleTransitionError


TOURNAMENT_TRANSITIONS: Mapping[
    TournamentLifecycle,
    frozenset[TournamentLifecycle],
] = {
    TournamentLifecycle.DRAFT: frozenset({TournamentLifecycle.ACTIVE}),
    TournamentLifecycle.ACTIVE: frozenset({TournamentLifecycle.FINISHED}),
    TournamentLifecycle.FINISHED: frozenset(),
}


async def on_tournament_leave(
    entity: LifecycleEntity[TournamentLifecycle],
    target: TournamentLifecycle,
    session: AsyncSession,
) -> None:
    tournament = entity
    if not isinstance(tournament, Tournament):
        raise TypeError("Tournament lifecycle hook received the wrong entity")
    if tournament.lifecycle is not TournamentLifecycle.DRAFT:
        return

    participant_count = await session.scalar(
        select(func.count(TournamentParticipant.id)).where(
            TournamentParticipant.tournament_id == tournament.id
        )
    )
    if participant_count is None or participant_count < 2:
        raise TournamentTransitionError(
            "A tournament needs at least two registered players before activation."
        )


TOURNAMENT_LIFECYCLE = LifecycleMachine(
    TOURNAMENT_TRANSITIONS,
    on_leave=on_tournament_leave,
)


async def transition_tournament(
    tournament: Tournament,
    target: TournamentLifecycle,
    session: AsyncSession,
) -> Tournament:
    await TOURNAMENT_LIFECYCLE.transition(tournament, target, session)
    return tournament


SECTION_TRANSITIONS: Mapping[
    SectionLifecycle,
    frozenset[SectionLifecycle],
] = {
    SectionLifecycle.DRAFT: frozenset({SectionLifecycle.ACTIVE}),
    SectionLifecycle.ACTIVE: frozenset({SectionLifecycle.FINISHED}),
    SectionLifecycle.FINISHED: frozenset(),
}


async def on_section_enter(
    entity: LifecycleEntity[SectionLifecycle],
    target: SectionLifecycle,
    session: AsyncSession,
) -> None:
    section = entity
    if not isinstance(section, TournamentSection):
        raise TypeError("Section lifecycle hook received the wrong entity")
    if target is SectionLifecycle.ACTIVE:
        section.tie_break_locked_at = datetime.now(UTC)


SECTION_LIFECYCLE = LifecycleMachine(
    SECTION_TRANSITIONS,
    on_enter=on_section_enter,
)


async def transition_section(
    section: TournamentSection,
    target: SectionLifecycle,
    session: AsyncSession,
) -> TournamentSection:
    await SECTION_LIFECYCLE.transition(section, target, session)
    return section
