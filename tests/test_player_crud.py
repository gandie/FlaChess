import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import TournamentParticipantAdmin
from app.main import app


class AvailableConnection:
    async def __aenter__(self) -> "AvailableConnection":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        return None


class AvailableEngine:
    def connect(self) -> AvailableConnection:
        return AvailableConnection()

    async def dispose(self) -> None:
        return None


class EmptyScalars:
    def unique(self) -> "EmptyScalars":
        return self

    def all(self) -> list[object]:
        return []


class EmptyResult:
    def scalars(self) -> EmptyScalars:
        return EmptyScalars()


class EmptyAsyncSession:
    async def __aenter__(self) -> "EmptyAsyncSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> EmptyResult:
        return EmptyResult()


class EmptyAsyncSessionMaker:
    class_ = AsyncSession

    def __call__(self) -> EmptyAsyncSession:
        return EmptyAsyncSession()


class PlayerCrudAdminTests(unittest.TestCase):
    def test_player_crud_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/api/players", paths)
        self.assertIn("/api/players/{id}", paths)
        self.assertIn("get", paths["/api/players"])
        self.assertIn("post", paths["/api/players"])
        self.assertIn("get", paths["/api/players/{id}"])
        self.assertIn("patch", paths["/api/players/{id}"])
        self.assertIn("delete", paths["/api/players/{id}"])

    def test_sqladmin_mount_is_added_when_database_is_available(self) -> None:
        engine = AvailableEngine()
        with (
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql+asyncpg://user:password@localhost/db"},
            ),
            patch("app.main.create_async_engine", return_value=engine),
            patch("app.main.async_sessionmaker", return_value=object()),
        ):
            with TestClient(app) as client:
                response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        mount_paths = {getattr(route, "path", None) for route in app.routes}
        self.assertIn("/admin", mount_paths)

    def test_tournament_participant_admin_uses_relationship_fields(self) -> None:
        admin = TournamentParticipantAdmin()
        admin.session_maker = EmptyAsyncSessionMaker()
        form_class = self.run_async(admin.scaffold_form())

        self.assertIn("tournament", form_class.__dict__)
        self.assertIn("player", form_class.__dict__)
        self.assertNotIn("tournament_id", form_class.__dict__)
        self.assertNotIn("player_id", form_class.__dict__)

    @staticmethod
    def run_async(operation: object) -> object:
        import asyncio

        return asyncio.run(operation)
