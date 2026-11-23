from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Game,
    RoundParticipant,
    SectionParticipant,
    SectionStanding,
    SectionStandingValue,
    SectionTiebreak,
    TournamentRound,
    TournamentSection,
)
from app.standings.types import (
    CalculatedStanding,
    SnapshotInputs,
    StandingComputationError,
    StandingInputNotFoundError,
)


async def validate_through_round(
    section_id: int,
    through_round_id: int | None,
    session: AsyncSession,
) -> TournamentRound | None:
    section = await session.get(TournamentSection, section_id)
    if section is None:
        raise StandingInputNotFoundError("Tournament section not found")
    if through_round_id is None:
        return None
    through_round = await session.get(TournamentRound, through_round_id)
    if through_round is None:
        raise StandingInputNotFoundError("Tournament round not found")
    if through_round.section_id != section_id:
        raise StandingComputationError(
            "Through-round does not belong to the section",
        )
    return through_round


async def load_snapshot_inputs(
    section_id: int,
    through_round: TournamentRound | None,
    session: AsyncSession,
) -> SnapshotInputs:
    rounds = await section_rounds(section_id, through_round, session)
    participants = list(
        (
            await session.scalars(
                select(SectionParticipant)
                .where(SectionParticipant.section_id == section_id)
                .order_by(SectionParticipant.id),
            )
        ).all(),
    )
    round_ids = [round_.id for round_ in rounds]
    games = await round_games(round_ids, session)
    records = await round_records(round_ids, session)
    rules = list(
        (
            await session.scalars(
                select(SectionTiebreak)
                .where(
                    SectionTiebreak.section_id == section_id,
                    SectionTiebreak.is_active.is_(True),
                )
                .order_by(SectionTiebreak.sequence),
            )
        ).all(),
    )
    return SnapshotInputs(participants, rounds, games, records, rules)


async def section_rounds(
    section_id: int,
    through_round: TournamentRound | None,
    session: AsyncSession,
) -> list[TournamentRound]:
    statement = select(TournamentRound).where(
        TournamentRound.section_id == section_id,
    )
    if through_round is not None:
        statement = statement.where(TournamentRound.number <= through_round.number)
    result = await session.scalars(statement.order_by(TournamentRound.number))
    return list(result.all())


async def round_games(
    round_ids: Sequence[int],
    session: AsyncSession,
) -> list[Game]:
    if not round_ids:
        return []
    result = await session.scalars(select(Game).where(Game.round_id.in_(round_ids)))
    return list(result.all())


async def round_records(
    round_ids: Sequence[int],
    session: AsyncSession,
) -> list[RoundParticipant]:
    if not round_ids:
        return []
    result = await session.scalars(
        select(RoundParticipant).where(RoundParticipant.round_id.in_(round_ids)),
    )
    return list(result.all())


async def replace_snapshot(
    section_id: int,
    through_round_id: int | None,
    calculated: Sequence[CalculatedStanding],
    rules: Sequence[SectionTiebreak],
    session: AsyncSession,
) -> list[SectionStanding]:
    statement = delete(SectionStanding).where(
        SectionStanding.section_id == section_id,
    )
    if through_round_id is None:
        statement = statement.where(SectionStanding.through_round_id.is_(None))
    else:
        statement = statement.where(
            SectionStanding.through_round_id == through_round_id,
        )
    await session.execute(statement)
    standings = snapshot_rows(
        section_id,
        through_round_id,
        calculated,
        rules,
    )
    session.add_all(standings)
    await session.flush()
    return standings


def snapshot_rows(
    section_id: int,
    through_round_id: int | None,
    calculated: Sequence[CalculatedStanding],
    rules: Sequence[SectionTiebreak],
) -> list[SectionStanding]:
    computed_at = datetime.now(UTC)
    return [
        SectionStanding(
            section_id=section_id,
            participant_id=item.participant_id,
            through_round_id=through_round_id,
            rank=item.rank,
            points=item.points,
            wins=item.wins,
            draws=item.draws,
            losses=item.losses,
            computed_at=computed_at,
            values=[
                SectionStandingValue(
                    tiebreak_id=rule.id,
                    sequence=rule.sequence,
                    value=item.values[rule.id],
                )
                for rule in rules
            ],
        )
        for item in calculated
    ]
