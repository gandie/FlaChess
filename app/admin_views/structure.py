from sqladmin import ModelView

from app.models import (
    Player,
    Tournament,
    TournamentParticipant,
    TournamentPhase,
    TournamentSection,
)


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
