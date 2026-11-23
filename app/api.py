from fastapi import APIRouter, Depends, HTTPException, status
from fastcrud import crud_router
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.lifecycle import (
    LifecycleTransitionError,
    transition_section,
    transition_tournament,
)
from app.models import (
    Game,
    ParticipationType,
    Player,
    RoundParticipant,
    SectionLifecycle,
    SectionParticipant,
    SectionTiebreak,
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
    TournamentPhase,
    TournamentRound,
    TournamentSection,
)
from app.schemas import (
    GameCreate,
    GameResponse,
    GameUpdate,
    PlayerCreate,
    PlayerUpdate,
    RoundParticipantCreate,
    RoundParticipantResponse,
    RoundParticipantUpdate,
    SectionParticipantCreate,
    SectionParticipantResponse,
    SectionParticipantUpdate,
    SectionTiebreakCreate,
    SectionTiebreakResponse,
    SectionTiebreakUpdate,
    SectionTransitionResponse,
    TournamentCreate,
    TournamentParticipantCreate,
    TournamentParticipantUpdate,
    TournamentPhaseCreate,
    TournamentPhaseUpdate,
    TournamentRoundCreate,
    TournamentRoundUpdate,
    TournamentSectionCreate,
    TournamentSectionUpdate,
    TournamentTransitionResponse,
    TournamentUpdate,
)
from app.tournament_rounds import (
    game_section_ids,
    participant_section_id,
    round_section_id,
)
from app.tournament_structure import membership_tournament_ids

router = APIRouter()

player_router = crud_router(
    session=get_session,
    model=Player,
    create_schema=PlayerCreate,
    update_schema=PlayerUpdate,
    path="/players",
    tags=["Players"],
)
router.include_router(player_router)

tournament_router = crud_router(
    session=get_session,
    model=Tournament,
    create_schema=TournamentCreate,
    update_schema=TournamentUpdate,
    path="/tournaments",
    tags=["Tournaments"],
)
router.include_router(tournament_router)

tournament_participant_router = crud_router(
    session=get_session,
    model=TournamentParticipant,
    create_schema=TournamentParticipantCreate,
    update_schema=TournamentParticipantUpdate,
    path="/tournament-participants",
    tags=["Tournament Participants"],
)
router.include_router(tournament_participant_router)

tournament_phase_router = crud_router(
    session=get_session,
    model=TournamentPhase,
    create_schema=TournamentPhaseCreate,
    update_schema=TournamentPhaseUpdate,
    path="/tournament-phases",
    tags=["Tournament Phases"],
)
router.include_router(tournament_phase_router)

tournament_section_router = crud_router(
    session=get_session,
    model=TournamentSection,
    create_schema=TournamentSectionCreate,
    update_schema=TournamentSectionUpdate,
    path="/tournament-sections",
    tags=["Tournament Sections"],
)
router.include_router(tournament_section_router)

section_tiebreak_router = crud_router(
    session=get_session,
    model=SectionTiebreak,
    create_schema=SectionTiebreakCreate,
    update_schema=SectionTiebreakUpdate,
    path="/section-tiebreaks",
    tags=["Section Tie-Breaks"],
    deleted_methods=["create", "update", "delete"],
)
router.include_router(section_tiebreak_router)

section_participant_router = crud_router(
    session=get_session,
    model=SectionParticipant,
    create_schema=SectionParticipantCreate,
    update_schema=SectionParticipantUpdate,
    path="/section-participants",
    tags=["Section Participants"],
    deleted_methods=["create", "update"],
)
router.include_router(section_participant_router)

tournament_round_router = crud_router(
    session=get_session,
    model=TournamentRound,
    create_schema=TournamentRoundCreate,
    update_schema=TournamentRoundUpdate,
    path="/tournament-rounds",
    tags=["Tournament Rounds"],
)
router.include_router(tournament_round_router)

round_participant_router = crud_router(
    session=get_session,
    model=RoundParticipant,
    create_schema=RoundParticipantCreate,
    update_schema=RoundParticipantUpdate,
    path="/round-participants",
    tags=["Round Participants"],
    deleted_methods=["create", "update"],
)
router.include_router(round_participant_router)

game_router = crud_router(
    session=get_session,
    model=Game,
    create_schema=GameCreate,
    update_schema=GameUpdate,
    path="/games",
    tags=["Games"],
    deleted_methods=["create", "update"],
)
router.include_router(game_router)


async def validate_section_is_draft(
    section_id: int,
    session: AsyncSession,
) -> None:
    lifecycle = await session.scalar(
        select(TournamentSection.lifecycle).where(
            TournamentSection.id == section_id,
        ),
    )
    if lifecycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    if lifecycle is not SectionLifecycle.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section tie-break configuration is locked",
        )


async def commit_tiebreak(
    tiebreak: SectionTiebreak,
    session: AsyncSession,
) -> SectionTiebreak:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section tie-break configuration violates a constraint",
        ) from error
    return tiebreak


@router.post(
    "/section-tiebreaks",
    response_model=SectionTiebreakResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_section_tiebreak(
    payload: SectionTiebreakCreate,
    session: AsyncSession = Depends(get_session),
) -> SectionTiebreak:
    await validate_section_is_draft(payload.section_id, session)
    tiebreak = SectionTiebreak(**payload.model_dump())
    session.add(tiebreak)
    return await commit_tiebreak(tiebreak, session)


@router.patch(
    "/section-tiebreaks/{id}",
    response_model=SectionTiebreakResponse,
)
async def update_section_tiebreak(
    id: int,
    payload: SectionTiebreakUpdate,
    session: AsyncSession = Depends(get_session),
) -> SectionTiebreak:
    tiebreak = await session.get(SectionTiebreak, id)
    if tiebreak is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section tie-break not found",
        )

    await validate_section_is_draft(tiebreak.section_id, session)
    values = payload.model_dump(exclude_unset=True)
    target_section_id = values.get("section_id", tiebreak.section_id)
    if target_section_id != tiebreak.section_id:
        await validate_section_is_draft(target_section_id, session)
    for field, value in values.items():
        setattr(tiebreak, field, value)
    return await commit_tiebreak(tiebreak, session)


@router.delete(
    "/section-tiebreaks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_section_tiebreak(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    tiebreak = await session.get(SectionTiebreak, id)
    if tiebreak is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section tie-break not found",
        )
    await validate_section_is_draft(tiebreak.section_id, session)
    await session.delete(tiebreak)
    await session.commit()


async def validate_section_membership(
    participant_id: int,
    section_id: int,
    session: AsyncSession,
) -> None:
    (
        participant_tournament_id,
        section_tournament_id,
    ) = await membership_tournament_ids(participant_id, section_id, session)
    if participant_tournament_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament participant not found",
        )

    if section_tournament_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )
    if participant_tournament_id != section_tournament_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant and section belong to different tournaments",
        )


async def commit_section_membership(
    membership: SectionParticipant,
    session: AsyncSession,
) -> SectionParticipant:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section participant membership violates a database constraint",
        ) from error
    return membership


@router.post(
    "/section-participants",
    response_model=SectionParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_section_participant(
    payload: SectionParticipantCreate,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    await validate_section_membership(
        payload.participant_id,
        payload.section_id,
        session,
    )
    membership = SectionParticipant(**payload.model_dump())
    session.add(membership)
    return await commit_section_membership(membership, session)


@router.patch(
    "/section-participants/{id}",
    response_model=SectionParticipantResponse,
)
async def update_section_participant(
    id: int,
    payload: SectionParticipantUpdate,
    session: AsyncSession = Depends(get_session),
) -> SectionParticipant:
    membership = await session.get(SectionParticipant, id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )

    values = payload.model_dump(exclude_unset=True)
    participant_id = values.get("participant_id", membership.participant_id)
    section_id = values.get("section_id", membership.section_id)
    await validate_section_membership(participant_id, section_id, session)
    for field, value in values.items():
        setattr(membership, field, value)
    return await commit_section_membership(membership, session)


async def validate_round_member(
    round_id: int,
    participant_id: int,
    session: AsyncSession,
) -> None:
    actual_round_section_id = await round_section_id(round_id, session)
    actual_participant_section_id = await participant_section_id(
        participant_id,
        session,
    )
    if actual_round_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament round not found",
        )
    if actual_participant_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )
    if actual_round_section_id != actual_participant_section_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant does not belong to the round's section",
        )


async def commit_round_record(
    record: RoundParticipant | Game,
    session: AsyncSession,
) -> RoundParticipant | Game:
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Round record violates a database constraint",
        ) from error
    return record


@router.post(
    "/round-participants",
    response_model=RoundParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_round_participant(
    payload: RoundParticipantCreate,
    session: AsyncSession = Depends(get_session),
) -> RoundParticipant:
    await validate_round_member(
        payload.round_id,
        payload.participant_id,
        session,
    )
    record = RoundParticipant(**payload.model_dump())
    session.add(record)
    await commit_round_record(record, session)
    return record


@router.patch(
    "/round-participants/{id}",
    response_model=RoundParticipantResponse,
)
async def update_round_participant(
    id: int,
    payload: RoundParticipantUpdate,
    session: AsyncSession = Depends(get_session),
) -> RoundParticipant:
    record = await session.get(RoundParticipant, id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Round participant not found",
        )

    values = payload.model_dump(exclude_unset=True)
    round_id = values.get("round_id", record.round_id)
    participant_id = values.get("participant_id", record.participant_id)
    await validate_round_member(round_id, participant_id, session)
    participation_type = values.get(
        "participation_type",
        record.participation_type,
    )
    score_awarded = values.get("score_awarded", record.score_awarded)
    if participation_type == ParticipationType.PAIRED and score_awarded is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="paired participation cannot have score_awarded",
        )
    for field, value in values.items():
        setattr(record, field, value)
    await commit_round_record(record, session)
    return record


async def validate_game_members(
    round_id: int,
    white_participant_id: int,
    black_participant_id: int,
    session: AsyncSession,
) -> None:
    if white_participant_id == black_participant_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Game participants must be different",
        )
    (
        actual_round_section_id,
        white_section_id,
        black_section_id,
    ) = await game_section_ids(
        round_id,
        white_participant_id,
        black_participant_id,
        session,
    )
    if actual_round_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament round not found",
        )
    if white_section_id is None or black_section_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section participant not found",
        )
    if (
        white_section_id != actual_round_section_id
        or black_section_id != actual_round_section_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game participants do not belong to the round's section",
        )


@router.post(
    "/games",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_game(
    payload: GameCreate,
    session: AsyncSession = Depends(get_session),
) -> Game:
    await validate_game_members(
        payload.round_id,
        payload.white_participant_id,
        payload.black_participant_id,
        session,
    )
    game = Game(**payload.model_dump())
    session.add(game)
    await commit_round_record(game, session)
    return game


@router.patch(
    "/games/{id}",
    response_model=GameResponse,
)
async def update_game(
    id: int,
    payload: GameUpdate,
    session: AsyncSession = Depends(get_session),
) -> Game:
    game = await session.get(Game, id)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    values = payload.model_dump(exclude_unset=True)
    round_id = values.get("round_id", game.round_id)
    white_id = values.get("white_participant_id", game.white_participant_id)
    black_id = values.get("black_participant_id", game.black_participant_id)
    await validate_game_members(round_id, white_id, black_id, session)
    white_score = values.get("white_score", game.white_score)
    black_score = values.get("black_score", game.black_score)
    try:
        GameCreate.validate_scores(white_score, black_score)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    for field, value in values.items():
        setattr(game, field, value)
    await commit_round_record(game, session)
    return game


async def apply_tournament_transition(
    id: int,
    target: TournamentLifecycle,
    session: AsyncSession,
) -> Tournament:
    tournament = await session.scalar(select(Tournament).where(Tournament.id == id))
    if tournament is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament not found",
        )

    try:
        await transition_tournament(tournament, target, session)
    except LifecycleTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    await session.commit()
    return tournament


@router.post(
    "/tournaments/{id}/activate",
    response_model=TournamentTransitionResponse,
)
async def activate_tournament(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> Tournament:
    return await apply_tournament_transition(
        id,
        TournamentLifecycle.ACTIVE,
        session,
    )


@router.post(
    "/tournaments/{id}/finish",
    response_model=TournamentTransitionResponse,
)
async def finish_tournament(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> Tournament:
    return await apply_tournament_transition(
        id,
        TournamentLifecycle.FINISHED,
        session,
    )


async def apply_section_transition(
    id: int,
    target: SectionLifecycle,
    session: AsyncSession,
) -> TournamentSection:
    section = await session.scalar(
        select(TournamentSection).where(TournamentSection.id == id),
    )
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tournament section not found",
        )

    try:
        await transition_section(section, target, session)
    except LifecycleTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    await session.commit()
    return section


@router.post(
    "/tournament-sections/{id}/activate",
    response_model=SectionTransitionResponse,
)
async def activate_section(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> TournamentSection:
    return await apply_section_transition(
        id,
        SectionLifecycle.ACTIVE,
        session,
    )


@router.post(
    "/tournament-sections/{id}/finish",
    response_model=SectionTransitionResponse,
)
async def finish_section(
    id: int,
    session: AsyncSession = Depends(get_session),
) -> TournamentSection:
    return await apply_section_transition(
        id,
        SectionLifecycle.FINISHED,
        session,
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
