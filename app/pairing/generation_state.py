from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Game,
    ParticipationType,
    RoundParticipant,
    SectionParticipant,
    SectionTiebreak,
    TournamentPhaseFormat,
    TournamentRound,
    TournamentSection,
)
from app.pairing.types import Color, PairingFormat, PairingParticipant
from app.standings.calculation import calculate_standings


class PairingGenerationError(ValueError):
    pass


class PairingGenerationConflict(PairingGenerationError):
    pass


class PairingGenerationNotFound(PairingGenerationError):
    pass


@dataclass(frozen=True)
class GenerationState:
    section: TournamentSection
    pairing_format: PairingFormat
    participants: tuple[SectionParticipant, ...]
    rounds: tuple[TournamentRound, ...]
    games: tuple[Game, ...]
    records: tuple[RoundParticipant, ...]
    tiebreaks: tuple[SectionTiebreak, ...]


async def load_generation_state(
    section_id: int,
    session: AsyncSession,
) -> GenerationState:
    section = await load_section(section_id, session)
    participants = await load_participants(section_id, session)
    rounds = await load_rounds(section_id, session)
    round_ids = [round_.id for round_ in rounds]
    games = await load_games(round_ids, session)
    records = await load_records(round_ids, session)
    tiebreaks = await load_tiebreaks(section_id, session)
    return GenerationState(
        section=section,
        pairing_format=PairingFormat(section.phase.format.value),
        participants=participants,
        rounds=rounds,
        games=games,
        records=records,
        tiebreaks=tiebreaks,
    )


async def load_section(
    section_id: int,
    session: AsyncSession,
) -> TournamentSection:
    statement = (
        select(TournamentSection)
        .options(selectinload(TournamentSection.phase))
        .where(TournamentSection.id == section_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    section = await session.scalar(statement)
    if section is None:
        raise PairingGenerationNotFound(
            f"Tournament section {section_id} was not found.",
        )
    supported = {item.value for item in TournamentPhaseFormat}
    if section.phase.format.value not in supported:
        raise PairingGenerationError(
            "The section has an unsupported pairing format.",
        )
    return section


async def load_participants(
    section_id: int,
    session: AsyncSession,
) -> tuple[SectionParticipant, ...]:
    result = await session.scalars(
        select(SectionParticipant)
        .where(SectionParticipant.section_id == section_id)
        .order_by(SectionParticipant.id)
        .execution_options(populate_existing=True),
    )
    return tuple(result.all())


async def load_rounds(
    section_id: int,
    session: AsyncSession,
) -> tuple[TournamentRound, ...]:
    result = await session.scalars(
        select(TournamentRound)
        .where(TournamentRound.section_id == section_id)
        .order_by(TournamentRound.number)
        .execution_options(populate_existing=True),
    )
    return tuple(result.all())


async def load_games(
    round_ids: list[int],
    session: AsyncSession,
) -> tuple[Game, ...]:
    if not round_ids:
        return ()
    result = await session.scalars(
        select(Game)
        .where(Game.round_id.in_(round_ids))
        .order_by(Game.id)
        .execution_options(populate_existing=True),
    )
    return tuple(result.all())


async def load_records(
    round_ids: list[int],
    session: AsyncSession,
) -> tuple[RoundParticipant, ...]:
    if not round_ids:
        return ()
    result = await session.scalars(
        select(RoundParticipant)
        .where(RoundParticipant.round_id.in_(round_ids))
        .order_by(RoundParticipant.id)
        .execution_options(populate_existing=True),
    )
    return tuple(result.all())


async def load_tiebreaks(
    section_id: int,
    session: AsyncSession,
) -> tuple[SectionTiebreak, ...]:
    result = await session.scalars(
        select(SectionTiebreak)
        .where(
            SectionTiebreak.section_id == section_id,
            SectionTiebreak.is_active.is_(True),
        )
        .order_by(SectionTiebreak.sequence)
        .execution_options(populate_existing=True),
    )
    return tuple(result.all())


def pairing_participants(
    state: GenerationState,
    *,
    participants: tuple[SectionParticipant, ...] | None = None,
) -> tuple[PairingParticipant, ...]:
    selected = participants or state.participants
    standings = calculate_standings(
        state.participants,
        state.rounds,
        state.games,
        state.records,
        state.tiebreaks,
    )
    standings_by_id = {item.participant_id: item for item in standings}
    colors = color_history(state)
    byes = bye_counts(state)
    result = []
    for participant in selected:
        if participant.seed_position is None:
            raise PairingGenerationError(
                f"Participant {participant.id} is missing a seed position.",
            )
        standing = standings_by_id[participant.id]
        values = tuple(
            standing.values.get(rule.id, Decimal("0"))
            for rule in state.tiebreaks
        )
        result.append(
            PairingParticipant(
                participant_id=participant.id,
                seed_position=participant.seed_position,
                points=standing.points,
                ranking_values=values,
                color_history=tuple(colors[participant.id]),
                bye_count=byes[participant.id],
            ),
        )
    return tuple(result)


def color_history(state: GenerationState) -> dict[int, list[Color]]:
    result: dict[int, list[Color]] = defaultdict(list)
    round_numbers = {round_.id: round_.number for round_ in state.rounds}
    ordered_games = sorted(
        state.games,
        key=lambda item: round_numbers[item.round_id],
    )
    for game in ordered_games:
        result[game.white_participant_id].append(Color.WHITE)
        result[game.black_participant_id].append(Color.BLACK)
    return result


def bye_counts(state: GenerationState) -> dict[int, int]:
    result: dict[int, int] = defaultdict(int)
    for record in state.records:
        if record.participation_type is ParticipationType.BYE:
            result[record.participant_id] += 1
    return result
