from sqladmin import ModelView

from app.models import Player, Tournament, TournamentParticipant


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
