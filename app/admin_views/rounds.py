from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from app.models import Game, RoundParticipant, TournamentRound
from app.tournament_rounds import (
    game_section_ids,
    participant_section_id,
    round_section_id,
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
