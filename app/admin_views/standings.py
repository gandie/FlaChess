from sqladmin import ModelView

from app.models import SectionStanding, SectionStandingValue


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
