from typing import Any

from sqladmin import ModelView
from sqlalchemy import select
from starlette.requests import Request

from app.models import (
    Game,
    Player,
    RoundParticipant,
    SectionLifecycle,
    SectionParticipant,
    SectionStanding,
    SectionStandingValue,
    SectionTiebreak,
    Tournament,
    TournamentParticipant,
    TournamentPhase,
    TournamentRound,
    TournamentSection,
)
from app.tournament_rounds import (
    game_section_ids,
    participant_section_id,
    round_section_id,
)
from app.tournament_structure import membership_tournament_ids


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


class PlayerAdmin(ModelView, model=Player):
    name = "Player"
    name_plural = "Players"
    icon = "fa-solid fa-user"
    column_list = [Player.id, Player.name]
    column_sortable_list = [Player.id, Player.name]
    column_searchable_list = [Player.name]
    form_columns = [Player.name]


class TournamentAdmin(ModelView, model=Tournament):
    name = "Tournament"
    name_plural = "Tournaments"
    icon = "fa-solid fa-chess"
    column_list = [
        Tournament.id,
        Tournament.name,
        Tournament.lifecycle,
        Tournament.time_control,
        Tournament.starts_at,
        Tournament.ends_at,
    ]
    column_sortable_list = [
        Tournament.id,
        Tournament.name,
        Tournament.lifecycle,
        Tournament.starts_at,
    ]
    column_searchable_list = [Tournament.name, Tournament.description]
    form_columns = [
        Tournament.name,
        Tournament.description,
        Tournament.time_control,
        Tournament.starts_at,
        Tournament.ends_at,
    ]


class TournamentParticipantAdmin(ModelView, model=TournamentParticipant):
    name = "Tournament Participant"
    name_plural = "Tournament Participants"
    icon = "fa-solid fa-users"
    column_list = [
        TournamentParticipant.id,
        TournamentParticipant.tournament,
        TournamentParticipant.player,
    ]
    form_columns = [
        TournamentParticipant.tournament,
        TournamentParticipant.player,
    ]


class TournamentPhaseAdmin(ModelView, model=TournamentPhase):
    name = "Tournament Phase"
    name_plural = "Tournament Phases"
    icon = "fa-solid fa-layer-group"
    column_list = [
        TournamentPhase.id,
        TournamentPhase.tournament,
        TournamentPhase.sequence,
        TournamentPhase.format,
    ]
    column_sortable_list = [
        TournamentPhase.id,
        TournamentPhase.tournament_id,
        TournamentPhase.sequence,
        TournamentPhase.format,
    ]
    form_columns = [
        TournamentPhase.tournament,
        TournamentPhase.sequence,
        TournamentPhase.format,
    ]


class TournamentSectionAdmin(ModelView, model=TournamentSection):
    name = "Tournament Section"
    name_plural = "Tournament Sections"
    icon = "fa-solid fa-table-list"
    column_list = [
        TournamentSection.id,
        TournamentSection.phase,
        TournamentSection.name,
        TournamentSection.sequence,
        TournamentSection.lifecycle,
        TournamentSection.planned_round_count,
        TournamentSection.tie_break_locked_at,
    ]
    column_sortable_list = [
        TournamentSection.id,
        TournamentSection.phase_id,
        TournamentSection.name,
        TournamentSection.sequence,
    ]
    column_searchable_list = [TournamentSection.name]
    form_columns = [
        TournamentSection.phase,
        TournamentSection.name,
        TournamentSection.sequence,
        TournamentSection.planned_round_count,
    ]


class SectionTiebreakAdmin(ModelView, model=SectionTiebreak):
    name = "Section Tie-Break"
    name_plural = "Section Tie-Breaks"
    icon = "fa-solid fa-arrow-down-1-9"
    column_list = [
        SectionTiebreak.id,
        SectionTiebreak.section,
        SectionTiebreak.sequence,
        SectionTiebreak.code,
        SectionTiebreak.parameter,
        SectionTiebreak.is_active,
    ]
    column_sortable_list = [
        SectionTiebreak.id,
        SectionTiebreak.section_id,
        SectionTiebreak.sequence,
        SectionTiebreak.code,
    ]
    form_columns = [
        SectionTiebreak.section,
        SectionTiebreak.code,
        SectionTiebreak.sequence,
        SectionTiebreak.parameter,
        SectionTiebreak.is_active,
    ]

    async def on_model_change(
        self,
        data: dict,
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        current_section_id = getattr(model, "section_id", None)
        if current_section_id is not None:
            await ensure_section_is_draft(
                self.session_maker,
                int(current_section_id),
            )

        section_value = data.get("section", current_section_id)
        if section_value is None:
            raise ValueError("Section is required")
        target_section_id = int(section_value)
        if target_section_id != current_section_id:
            await ensure_section_is_draft(
                self.session_maker,
                target_section_id,
            )

    async def on_model_delete(
        self,
        model: Any,
        request: Request,
    ) -> None:
        section_id = getattr(model, "section_id", None)
        if section_id is None:
            raise ValueError("Section is required")
        await ensure_section_is_draft(self.session_maker, int(section_id))


class SectionParticipantAdmin(ModelView, model=SectionParticipant):
    name = "Section Participant"
    name_plural = "Section Participants"
    icon = "fa-solid fa-user-group"
    column_list = [
        SectionParticipant.id,
        SectionParticipant.participant,
        SectionParticipant.section,
        SectionParticipant.rating,
        SectionParticipant.rating_source,
        SectionParticipant.source_section,
        SectionParticipant.source_rank,
    ]
    form_columns = [
        SectionParticipant.participant,
        SectionParticipant.section,
        SectionParticipant.rating,
        SectionParticipant.rating_source,
        SectionParticipant.source_section,
        SectionParticipant.source_rank,
    ]

    async def on_model_change(
        self,
        data: dict,
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        participant_value = data.get(
            "participant",
            getattr(model, "participant_id", None),
        )
        section_value = data.get(
            "section",
            getattr(model, "section_id", None),
        )
        if participant_value is None or section_value is None:
            raise ValueError("Participant and section are required")

        participant_id = int(participant_value)
        section_id = int(section_value)
        async with self.session_maker() as session:
            (
                participant_tournament_id,
                section_tournament_id,
            ) = await membership_tournament_ids(participant_id, section_id, session)

        if (
            participant_tournament_id is None
            or section_tournament_id is None
        ):
            raise ValueError("Participant or section no longer exists")
        if participant_tournament_id != section_tournament_id:
            raise ValueError(
                "Participant and section belong to different tournaments",
            )


class TournamentRoundAdmin(ModelView, model=TournamentRound):
    name = "Tournament Round"
    name_plural = "Tournament Rounds"
    icon = "fa-solid fa-chess-board"
    column_list = [
        TournamentRound.id,
        TournamentRound.section,
        TournamentRound.number,
    ]
    form_columns = [TournamentRound.section, TournamentRound.number]


class RoundParticipantAdmin(ModelView, model=RoundParticipant):
    name = "Round Participant"
    name_plural = "Round Participants"
    icon = "fa-solid fa-user-clock"
    column_list = [
        RoundParticipant.id,
        RoundParticipant.round,
        RoundParticipant.participant,
        RoundParticipant.participation_type,
        RoundParticipant.score_awarded,
    ]
    form_columns = [
        RoundParticipant.round,
        RoundParticipant.participant,
        RoundParticipant.participation_type,
        RoundParticipant.score_awarded,
        RoundParticipant.comment,
    ]

    async def on_model_change(
        self,
        data: dict,
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        round_value = data.get("round", getattr(model, "round_id", None))
        participant_value = data.get(
            "participant",
            getattr(model, "participant_id", None),
        )
        participation_type = data.get(
            "participation_type",
            getattr(model, "participation_type", None),
        )
        score_awarded = data.get(
            "score_awarded",
            getattr(model, "score_awarded", None),
        )
        if round_value is None or participant_value is None:
            raise ValueError("Round and participant are required")
        if participation_type == "paired" and score_awarded is not None:
            raise ValueError("Paired participation cannot have an awarded score")

        async with self.session_maker() as session:
            section_id = await round_section_id(int(round_value), session)
            member_section_id = await participant_section_id(
                int(participant_value),
                session,
            )
        if section_id is None or member_section_id is None:
            raise ValueError("Round or participant no longer exists")
        if section_id != member_section_id:
            raise ValueError("Participant does not belong to the round's section")


class GameAdmin(ModelView, model=Game):
    name = "Game"
    name_plural = "Games"
    icon = "fa-solid fa-chess"
    column_list = [
        Game.id,
        Game.round,
        Game.white_participant,
        Game.black_participant,
        Game.white_score,
        Game.black_score,
        Game.result_type,
    ]
    form_columns = [
        Game.round,
        Game.white_participant,
        Game.black_participant,
        Game.white_score,
        Game.black_score,
        Game.result_type,
        Game.recorded_at,
        Game.comment,
    ]

    async def on_model_change(
        self,
        data: dict,
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        round_value = data.get("round", getattr(model, "round_id", None))
        white_value = data.get(
            "white_participant",
            getattr(model, "white_participant_id", None),
        )
        black_value = data.get(
            "black_participant",
            getattr(model, "black_participant_id", None),
        )
        if round_value is None or white_value is None or black_value is None:
            raise ValueError("Round and both game participants are required")
        if int(white_value) == int(black_value):
            raise ValueError("Game participants must be different")

        async with self.session_maker() as session:
            section_id, white_section_id, black_section_id = await game_section_ids(
                int(round_value),
                int(white_value),
                int(black_value),
                session,
            )
        if section_id is None:
            raise ValueError("Round no longer exists")
        if white_section_id is None or black_section_id is None:
            raise ValueError("Game participant no longer exists")
        if white_section_id != section_id or black_section_id != section_id:
            raise ValueError("Game participants do not belong to the round's section")


class SectionStandingAdmin(ModelView, model=SectionStanding):
    name = "Section Standing"
    name_plural = "Section Standings"
    icon = "fa-solid fa-ranking-star"
    column_list = [
        SectionStanding.id,
        SectionStanding.section,
        SectionStanding.participant,
        SectionStanding.through_round,
        SectionStanding.rank,
        SectionStanding.points,
        SectionStanding.wins,
        SectionStanding.draws,
        SectionStanding.losses,
        SectionStanding.computed_at,
    ]
    column_sortable_list = [
        SectionStanding.id,
        SectionStanding.section_id,
        SectionStanding.rank,
        SectionStanding.points,
        SectionStanding.computed_at,
    ]
    can_create = False
    can_edit = False
    can_delete = False


class SectionStandingValueAdmin(ModelView, model=SectionStandingValue):
    name = "Section Standing Value"
    name_plural = "Section Standing Values"
    icon = "fa-solid fa-list-ol"
    column_list = [
        SectionStandingValue.id,
        SectionStandingValue.standing,
        SectionStandingValue.tiebreak,
        SectionStandingValue.sequence,
        SectionStandingValue.value,
    ]
    column_sortable_list = [
        SectionStandingValue.id,
        SectionStandingValue.standing_id,
        SectionStandingValue.sequence,
    ]
    can_create = False
    can_edit = False
    can_delete = False
