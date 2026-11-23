from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Game
from app.routes.round_records import commit_round_record
from app.schemas import GameCreate, GameResponse, GameUpdate
from app.tournament_rounds import game_section_ids

router = APIRouter()


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
