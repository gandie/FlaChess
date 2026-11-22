from fastapi import APIRouter
from fastcrud import crud_router

from app.database import get_session
from app.models import Player
from app.schemas import PlayerCreate, PlayerUpdate

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


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
