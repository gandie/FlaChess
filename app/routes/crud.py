from fastapi import APIRouter
from fastcrud import crud_router

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
from app.schemas import (
    GameCreate,
    GameUpdate,
    PlayerCreate,
    PlayerUpdate,
    RoundParticipantCreate,
    RoundParticipantUpdate,
    SectionParticipantCreate,
    SectionParticipantUpdate,
    SectionTiebreakCreate,
    SectionTiebreakUpdate,
    TournamentCreate,
    TournamentParticipantCreate,
    TournamentParticipantUpdate,
    TournamentResponse,
    TournamentPhaseCreate,
    TournamentPhaseUpdate,
    TournamentRoundCreate,
    TournamentRoundUpdate,
    TournamentSectionCreate,
    TournamentSectionUpdate,
    TournamentUpdate,
)

router = APIRouter()


def _include_crud(
    *,
    model: type,
    create_schema: type,
    update_schema: type,
    path: str,
    tags: list[str],
    deleted_methods: list[str] | None = None,
    select_schema: type | None = None,
) -> None:
    router.include_router(
        crud_router(
            session=get_session,
            model=model,
            create_schema=create_schema,
            update_schema=update_schema,
            path=path,
            tags=tags,
            deleted_methods=deleted_methods,
            select_schema=select_schema,
        ),
    )


_include_crud(
    model=Player,
    create_schema=PlayerCreate,
    update_schema=PlayerUpdate,
    path="/players",
    tags=["Players"],
)
_include_crud(
    model=Tournament,
    create_schema=TournamentCreate,
    update_schema=TournamentUpdate,
    select_schema=TournamentResponse,
    path="/tournaments",
    tags=["Tournaments"],
)
_include_crud(
    model=TournamentParticipant,
    create_schema=TournamentParticipantCreate,
    update_schema=TournamentParticipantUpdate,
    path="/tournament-participants",
    tags=["Tournament Participants"],
)
_include_crud(
    model=TournamentPhase,
    create_schema=TournamentPhaseCreate,
    update_schema=TournamentPhaseUpdate,
    path="/tournament-phases",
    tags=["Tournament Phases"],
)
_include_crud(
    model=TournamentSection,
    create_schema=TournamentSectionCreate,
    update_schema=TournamentSectionUpdate,
    path="/tournament-sections",
    tags=["Tournament Sections"],
)
_include_crud(
    model=SectionTiebreak,
    create_schema=SectionTiebreakCreate,
    update_schema=SectionTiebreakUpdate,
    path="/section-tiebreaks",
    tags=["Section Tie-Breaks"],
    deleted_methods=["create", "update", "delete"],
)
_include_crud(
    model=SectionParticipant,
    create_schema=SectionParticipantCreate,
    update_schema=SectionParticipantUpdate,
    path="/section-participants",
    tags=["Section Participants"],
    deleted_methods=["create", "update"],
)
_include_crud(
    model=TournamentRound,
    create_schema=TournamentRoundCreate,
    update_schema=TournamentRoundUpdate,
    path="/tournament-rounds",
    tags=["Tournament Rounds"],
)
_include_crud(
    model=RoundParticipant,
    create_schema=RoundParticipantCreate,
    update_schema=RoundParticipantUpdate,
    path="/round-participants",
    tags=["Round Participants"],
    deleted_methods=["create", "update"],
)
_include_crud(
    model=Game,
    create_schema=GameCreate,
    update_schema=GameUpdate,
    path="/games",
    tags=["Games"],
    deleted_methods=["create", "update"],
)
