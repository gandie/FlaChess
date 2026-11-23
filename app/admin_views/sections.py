from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from app.admin_views.support import ensure_section_is_draft
from app.models import SectionParticipant, SectionTiebreak
from app.tournament_structure import membership_tournament_ids


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

        if participant_tournament_id is None or section_tournament_id is None:
            raise ValueError("Participant or section no longer exists")
        if participant_tournament_id != section_tournament_id:
            raise ValueError(
                "Participant and section belong to different tournaments",
            )
