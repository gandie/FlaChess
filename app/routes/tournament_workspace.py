from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_session
from app.models import (
    Player,
    SectionParticipant,
    SectionTiebreak,
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
    TournamentPhase,
    TournamentSection,
)
from app.standings.ranking import SUPPORTED_TIEBREAK_CODES
from app.tournament_workspace_schemas import (
    TournamentReadiness,
    TournamentWorkspaceResponse,
    WorkspaceParticipant,
    WorkspacePhase,
    WorkspaceSection,
    WorkspaceSectionParticipant,
    WorkspaceTiebreak,
)

router = APIRouter()


async def workspace_participants(
    tournament_id: int,
    session: AsyncSession,
) -> list[WorkspaceParticipant]:
    result = await session.execute(
        select(
            TournamentParticipant.id.label("registration_id"),
            TournamentParticipant.player_id,
            Player.name.label("player_name"),
            Player.avatar.label("player_avatar"),
        )
        .join(Player, Player.id == TournamentParticipant.player_id)
        .where(TournamentParticipant.tournament_id == tournament_id)
        .order_by(Player.name, TournamentParticipant.id),
    )
    return [WorkspaceParticipant.model_validate(row) for row in result.all()]


async def workspace_sections(
    tournament_id: int,
    session: AsyncSession,
) -> tuple[list[TournamentPhase], list[WorkspaceSection]]:
    phase_result = await session.execute(
        select(TournamentPhase)
        .where(TournamentPhase.tournament_id == tournament_id)
        .order_by(TournamentPhase.sequence, TournamentPhase.id),
    )
    phases = list(phase_result.scalars().all())
    section_result = await session.execute(
        select(TournamentSection)
        .join(TournamentPhase, TournamentSection.phase_id == TournamentPhase.id)
        .where(TournamentPhase.tournament_id == tournament_id)
        .order_by(TournamentSection.sequence, TournamentSection.id),
    )
    sections = [
        WorkspaceSection(
            id=section.id,
            phase_id=section.phase_id,
            name=section.name,
            sequence=section.sequence,
            lifecycle=section.lifecycle,
            tie_break_locked_at=section.tie_break_locked_at,
            planned_round_count=section.planned_round_count,
            participants=[],
            tiebreaks=[],
        )
        for section in section_result.scalars().all()
    ]
    return phases, sections


async def section_participants(
    tournament_id: int,
    session: AsyncSession,
) -> list[tuple[int, WorkspaceSectionParticipant]]:
    source_section = aliased(TournamentSection)
    result = await session.execute(
        select(
            SectionParticipant.id,
            SectionParticipant.section_id,
            SectionParticipant.rating,
            SectionParticipant.rating_source,
            SectionParticipant.source_section_id,
            SectionParticipant.source_rank,
            SectionParticipant.seed_position,
            SectionParticipant.is_withdrawn,
            TournamentParticipant.id.label("registration_id"),
            TournamentParticipant.player_id,
            Player.name.label("player_name"),
            Player.avatar.label("player_avatar"),
            source_section.name.label("source_section_name"),
        )
        .join(
            TournamentParticipant,
            TournamentParticipant.id == SectionParticipant.participant_id,
        )
        .join(Player, Player.id == TournamentParticipant.player_id)
        .outerjoin(
            source_section,
            source_section.id == SectionParticipant.source_section_id,
        )
        .where(TournamentParticipant.tournament_id == tournament_id)
        .order_by(Player.name, SectionParticipant.id),
    )
    return [
        (
            row.section_id,
            WorkspaceSectionParticipant.model_validate(row),
        )
        for row in result.all()
    ]


async def section_tiebreaks(
    tournament_id: int,
    session: AsyncSession,
) -> list[tuple[int, WorkspaceTiebreak]]:
    result = await session.execute(
        select(SectionTiebreak)
        .join(
            TournamentSection,
            SectionTiebreak.section_id == TournamentSection.id,
        )
        .join(TournamentPhase, TournamentSection.phase_id == TournamentPhase.id)
        .where(TournamentPhase.tournament_id == tournament_id)
        .order_by(SectionTiebreak.sequence, SectionTiebreak.id),
    )
    return [
        (
            tiebreak.section_id,
            WorkspaceTiebreak(
                id=tiebreak.id,
                code=tiebreak.code,
                sequence=tiebreak.sequence,
                parameter=tiebreak.parameter,
                is_active=tiebreak.is_active,
                supported=tiebreak.code in SUPPORTED_TIEBREAK_CODES,
            ),
        )
        for tiebreak in result.scalars().all()
    ]


def readiness(
    tournament: Tournament,
    participants: list[WorkspaceParticipant],
    sections: list[WorkspaceSection],
) -> TournamentReadiness:
    blockers: list[str] = []
    warnings: list[str] = []
    if tournament.lifecycle is TournamentLifecycle.DRAFT and len(participants) < 2:
        blockers.append("Register at least two players before activation.")
    if not sections:
        warnings.append("Add at least one section before operating rounds.")
    for section in sections:
        eligible_members = [
            member for member in section.participants if not member.is_withdrawn
        ]
        if section.planned_round_count is None:
            warnings.append(f"{section.name}: planned round count is missing.")
        if not section.participants:
            warnings.append(f"{section.name}: no players are assigned.")
        if len(eligible_members) >= 2:
            seeds = [member.seed_position for member in eligible_members]
            if any(seed is None for seed in seeds):
                warnings.append(
                    f"{section.name}: an eligible player is missing a seed.",
                )
            elif len(set(seeds)) != len(seeds):
                warnings.append(f"{section.name}: seed positions are duplicated.")
        if any(not rule.supported for rule in section.tiebreaks):
            warnings.append(
                f"{section.name}: unsupported tie-break codes are configured.",
            )
    return TournamentReadiness(
        can_activate=tournament.lifecycle is TournamentLifecycle.DRAFT
        and not blockers,
        blocking_issues=blockers,
        setup_warnings=warnings,
    )


@router.get(
    "/tournaments/{tournament_id}/workspace",
    response_model=TournamentWorkspaceResponse,
    tags=["Tournaments"],
)
async def get_tournament_workspace(
    tournament_id: int,
    session: AsyncSession = Depends(get_session),
) -> TournamentWorkspaceResponse:
    tournament = await session.get(Tournament, tournament_id)
    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    participants = await workspace_participants(tournament_id, session)
    phases, sections = await workspace_sections(tournament_id, session)
    members_by_section: dict[int, list[WorkspaceSectionParticipant]] = defaultdict(list)
    for section_id, member in await section_participants(tournament_id, session):
        members_by_section[section_id].append(member)
    rules_by_section: dict[int, list[WorkspaceTiebreak]] = defaultdict(list)
    for section_id, rule in await section_tiebreaks(tournament_id, session):
        rules_by_section[section_id].append(rule)

    for section in sections:
        section.participants = members_by_section[section.id]
        section.tiebreaks = rules_by_section[section.id]
    sections_by_phase: dict[int, list[WorkspaceSection]] = defaultdict(list)
    for section in sections:
        sections_by_phase[section.phase_id].append(section)
    workspace_phases = [
        WorkspacePhase(
            id=phase.id,
            sequence=phase.sequence,
            format=phase.format,
            sections=sections_by_phase[phase.id],
        )
        for phase in phases
    ]
    return TournamentWorkspaceResponse(
        id=tournament.id,
        name=tournament.name,
        lifecycle=tournament.lifecycle,
        participants=participants,
        phases=workspace_phases,
        supported_tiebreak_codes=list(SUPPORTED_TIEBREAK_CODES),
        readiness=readiness(tournament, participants, sections),
    )
