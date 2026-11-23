import unittest
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.admin import SectionTiebreakAdmin
from app.database import get_session
from app.main import app
from app.models import SectionLifecycle, SectionTiebreak, TournamentSection


class TiebreakSession:
    def __init__(
        self,
        scalar_values: list[object] | None = None,
        record: SectionTiebreak | None = None,
    ) -> None:
        self.scalar_values = iter(scalar_values or [])
        self.record = record
        self.added: SectionTiebreak | None = None
        self.committed = False
        self.deleted = False

    async def scalar(self, statement: object) -> object:
        return next(self.scalar_values)

    async def get(
        self,
        model: type[SectionTiebreak],
        id: int,
    ) -> SectionTiebreak | None:
        return self.record

    def add(self, tiebreak: SectionTiebreak) -> None:
        tiebreak.id = 9
        self.added = tiebreak

    async def delete(self, tiebreak: SectionTiebreak) -> None:
        self.deleted = True

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None

    async def __aenter__(self) -> "TiebreakSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class SectionTiebreakRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: TiebreakSession) -> None:
        async def override_session() -> AsyncIterator[TiebreakSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_tiebreak_and_section_action_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        for path in (
            "/api/section-tiebreaks",
            "/api/section-tiebreaks/{id}",
            "/api/tournament-sections/{id}/activate",
            "/api/tournament-sections/{id}/finish",
        ):
            self.assertIn(path, paths)
        self.assertIn("delete", paths["/api/section-tiebreaks/{id}"])
        self.assertIn("post", paths["/api/tournament-sections/{id}/activate"])

    def test_draft_section_accepts_configuration(self) -> None:
        session = TiebreakSession([SectionLifecycle.DRAFT])
        self.use_session(session)

        response = self.client.post(
            "/api/section-tiebreaks",
            json={"section_id": 4, "code": "buchholz", "sequence": 1},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 9)
        self.assertTrue(session.committed)

    def test_active_section_rejects_configuration_create(self) -> None:
        session = TiebreakSession([SectionLifecycle.ACTIVE])
        self.use_session(session)

        response = self.client.post(
            "/api/section-tiebreaks",
            json={"section_id": 4, "code": "buchholz", "sequence": 1},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("locked", response.json()["detail"])
        self.assertIsNone(session.added)

    def test_active_section_rejects_configuration_delete(self) -> None:
        record = SectionTiebreak(
            id=7,
            section_id=4,
            code="buchholz",
            sequence=1,
        )
        session = TiebreakSession([SectionLifecycle.ACTIVE], record)
        self.use_session(session)

        response = self.client.delete("/api/section-tiebreaks/7")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(session.deleted)
        self.assertFalse(session.committed)

    def test_section_activation_locks_tiebreaks(self) -> None:
        section = TournamentSection(
            id=4,
            phase_id=2,
            name="Open",
            sequence=1,
            lifecycle=SectionLifecycle.DRAFT,
        )
        session = TiebreakSession([section])
        self.use_session(session)

        response = self.client.post("/api/tournament-sections/4/activate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["lifecycle"], "active")
        self.assertIsNotNone(response.json()["tie_break_locked_at"])
        self.assertTrue(session.committed)


class SectionTiebreakAdminTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_rejects_changes_to_active_section(self) -> None:
        session = TiebreakSession([SectionLifecycle.ACTIVE])
        view = SimpleNamespace(session_maker=lambda: session)

        with self.assertRaisesRegex(ValueError, "locked"):
            await SectionTiebreakAdmin.on_model_change(
                view,
                {"section": 4},
                SectionTiebreak(),
                True,
                Request({"type": "http"}),
            )


if __name__ == "__main__":
    unittest.main()
