from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_session
from app.models import (
    Game,
    Player,
    RoundParticipant,
    SectionParticipant,
    SectionTiebreak,
    Tournament,
    TournamentParticipant,
    TournamentPhase,
    TournamentRound,
    TournamentSection,
)
from app.section_operation_schemas import (
    OperationGame,
    OperationParticipant,
    OperationRound,
    OperationRoundParticipant,
    OperationTiebreak,
    SectionOperationResponse,
)

router = APIRouter()


async def operation_participants(
    section_id: int,
    session: AsyncSession,
) -> list[OperationParticipant]:
    result = await session.execute(
        select(
            SectionParticipant.id,
            Player.name.label("player_name"),
            SectionParticipant.rating,
        )
        .join(
            TournamentParticipant,
            TournamentParticipant.id == SectionParticipant.participant_id,
        )
        .join(Player, Player.id == TournamentParticipant.player_id)
        .where(SectionParticipant.section_id == section_id)
        .order_by(Player.name, SectionParticipant.id),
    )
    return [OperationParticipant.model_validate(row) for row in result.all()]


async def operation_rounds(
    section_id: int,
    session: AsyncSession,
) -> list[TournamentRound]:
    result = await session.execute(
        select(TournamentRound)
        .where(TournamentRound.section_id == section_id)
        .order_by(TournamentRound.number, TournamentRound.id),
    )
    return list(result.scalars().all())


async def operation_tiebreaks(
    section_id: int,
    session: AsyncSession,
) -> list[OperationTiebreak]:
    result = await session.execute(
        select(
            SectionTiebreak.id,
            SectionTiebreak.code,
            SectionTiebreak.sequence,
            SectionTiebreak.parameter,
        )
        .where(
            SectionTiebreak.section_id == section_id,
            SectionTiebreak.is_active.is_(True),
        )
        .order_by(SectionTiebreak.sequence, SectionTiebreak.id),
    )
    return [OperationTiebreak.model_validate(row) for row in result.all()]


async def operation_games(
    round_ids: list[int],
    session: AsyncSession,
) -> list[tuple[int, OperationGame]]:
    if not round_ids:
        return []
    black_member = aliased(SectionParticipant)
    black_registration = aliased(TournamentParticipant)
    white_player = aliased(Player)
    black_player = aliased(Player)
    result = await session.execute(
        select(
            Game.id,
            Game.round_id,
            Game.white_participant_id,
            white_player.name.label("white_player_name"),
            Game.black_participant_id,
            black_player.name.label("black_player_name"),
            Game.white_score,
            Game.black_score,
            Game.result_type,
            Game.recorded_at,
            Game.comment,
        )
        .join(
            SectionParticipant,
            SectionParticipant.id == Game.white_participant_id,
        )
        .join(
            TournamentParticipant,
            TournamentParticipant.id == SectionParticipant.participant_id,
        )
        .join(white_player, white_player.id == TournamentParticipant.player_id)
        .join(black_member, black_member.id == Game.black_participant_id)
        .join(
            black_registration,
            black_registration.id == black_member.participant_id,
        )
        .join(black_player, black_player.id == black_registration.player_id)
        .where(Game.round_id.in_(round_ids))
        .order_by(Game.id),
    )
    return [(row.round_id, OperationGame.model_validate(row)) for row in result.all()]


async def operation_records(
    round_ids: list[int],
    session: AsyncSession,
) -> list[tuple[int, OperationRoundParticipant]]:
    if not round_ids:
        return []
    result = await session.execute(
        select(
            RoundParticipant.id,
            RoundParticipant.round_id,
            RoundParticipant.participant_id,
            Player.name.label("player_name"),
            RoundParticipant.participation_type,
            RoundParticipant.score_awarded,
            RoundParticipant.comment,
        )
        .join(
            SectionParticipant,
            SectionParticipant.id == RoundParticipant.participant_id,
        )
        .join(
            TournamentParticipant,
            TournamentParticipant.id == SectionParticipant.participant_id,
        )
        .join(Player, Player.id == TournamentParticipant.player_id)
        .where(RoundParticipant.round_id.in_(round_ids))
        .order_by(Player.name, RoundParticipant.id),
    )
    return [
        (row.round_id, OperationRoundParticipant.model_validate(row))
        for row in result.all()
    ]


async def operation_round_content(
    rounds: list[TournamentRound],
    session: AsyncSession,
) -> tuple[
    dict[int, list[OperationGame]],
    dict[int, list[OperationRoundParticipant]],
]:
    games_by_round: dict[int, list[OperationGame]] = defaultdict(list)
    records_by_round: dict[int, list[OperationRoundParticipant]] = defaultdict(list)
    round_ids = [round_.id for round_ in rounds]
    for round_id, game in await operation_games(round_ids, session):
        games_by_round[round_id].append(game)
    for round_id, record in await operation_records(round_ids, session):
        records_by_round[round_id].append(record)
    return games_by_round, records_by_round


@router.get(
    "/tournament-sections/{section_id}/operation",
    response_model=SectionOperationResponse,
    tags=["Tournament Sections"],
)
async def get_section_operation(
    section_id: int,
    session: AsyncSession = Depends(get_session),
) -> SectionOperationResponse:
    result = await session.execute(
        select(
            TournamentSection,
            Tournament.id.label("tournament_id"),
            Tournament.name.label("tournament_name"),
        )
        .join(TournamentPhase, TournamentSection.phase_id == TournamentPhase.id)
        .join(Tournament, TournamentPhase.tournament_id == Tournament.id)
        .where(TournamentSection.id == section_id),
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    section, tournament_id, tournament_name = row
    participants = await operation_participants(section_id, session)
    rounds = await operation_rounds(section_id, session)
    tiebreaks = await operation_tiebreaks(section_id, session)
    games_by_round, records_by_round = await operation_round_content(rounds, session)
    return SectionOperationResponse(
        id=section.id,
        tournament_id=tournament_id,
        tournament_name=tournament_name,
        name=section.name,
        sequence=section.sequence,
        lifecycle=section.lifecycle,
        tie_break_locked_at=section.tie_break_locked_at,
        planned_round_count=section.planned_round_count,
        participants=participants,
        tiebreaks=tiebreaks,
        rounds=[
            OperationRound(
                id=round_.id,
                number=round_.number,
                games=games_by_round[round_.id],
                records=records_by_round[round_.id],
            )
            for round_ in rounds
        ],
    )
