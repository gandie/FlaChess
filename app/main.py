import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqladmin import Admin

from app.admin import PlayerAdmin, TournamentAdmin, TournamentParticipantAdmin
from app.api import router as api_router
from app.config import load_environment
from app.web import STATIC_DIR, router as web_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    load_environment()
    database_url = os.getenv("DATABASE_URL")
    engine: AsyncEngine | None = None
    app.state.session_factory = None

    if not database_url:
        logger.warning("DATABASE_URL is not set; starting without a database connection")
    else:
        engine = create_async_engine(database_url)
        app.state.session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        if not getattr(app.state, "admin_mounted", False):
            admin = Admin(app, engine=engine)
            admin.add_view(PlayerAdmin)
            admin.add_view(TournamentAdmin)
            admin.add_view(TournamentParticipantAdmin)
            app.mount("/admin", admin.app, name="admin")
            app.state.admin_mounted = True
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            logger.warning(
                "PostgreSQL connection check failed; startup will continue (%s)",
                type(error).__name__,
            )

    try:
        yield
    finally:
        if engine is not None:
            await engine.dispose()


app = FastAPI(title="Fla Chess", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
app.include_router(web_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
