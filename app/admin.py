from sqladmin import ModelView

from app.models import Player


class PlayerAdmin(ModelView, model=Player):
    name = "Player"
    name_plural = "Players"
    icon = "fa-solid fa-user"
    column_list = [Player.id, Player.name]
    column_sortable_list = [Player.id, Player.name]
    column_searchable_list = [Player.name]
    form_columns = [Player.name]
