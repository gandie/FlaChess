from collections.abc import Mapping

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tournament, TournamentLifecycle, TournamentParticipant


class TournamentTransitionError(ValueError):
    pass


ALLOWED_TRANSITIONS: Mapping[
    TournamentLifecycle,
    frozenset[TournamentLifecycle],
] = {
    TournamentLifecycle.DRAFT: frozenset({TournamentLifecycle.ACTIVE}),
    TournamentLifecycle.ACTIVE: frozenset({TournamentLifecycle.FINISHED}),
    TournamentLifecycle.FINISHED: frozenset(),
}


async def on_leave(
    tournament: Tournament,
    target: TournamentLifecycle,
    session: AsyncSession,
) -> None:
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


def on_enter(tournament: Tournament, target: TournamentLifecycle) -> None:
    tournament.lifecycle = target


async def transition_tournament(
    tournament: Tournament,
    target: TournamentLifecycle,
    session: AsyncSession,
) -> Tournament:
    if target not in ALLOWED_TRANSITIONS[tournament.lifecycle]:
        raise TournamentTransitionError(
            f"Cannot transition tournament from {tournament.lifecycle.value} "
            f"to {target.value}."
        )

    await on_leave(tournament, target, session)
    on_enter(tournament, target)
    return tournament
