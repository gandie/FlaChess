from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.admin import (
    SectionParticipantAdmin,
    TournamentPhaseAdmin,
    TournamentSectionAdmin,
)
from app.database import get_session
from app.main import app
from app.models import SectionParticipant


class StructureSession:
    def __init__(
        self,
        tournament_ids: list[int | None],
        membership: SectionParticipant | None = None,
    ) -> None:
        self.tournament_ids = iter(tournament_ids)
        self.membership = membership
        self.added: SectionParticipant | None = None
        self.committed = False

    async def scalar(self, statement: object) -> int | None:
        return next(self.tournament_ids)

    async def get(
        self,
        model: type[SectionParticipant],
        id: int,
    ) -> SectionParticipant | None:
        return self.membership

    def add(self, membership: SectionParticipant) -> None:
        membership.id = 7
        self.added = membership

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None

    async def __aenter__(self) -> "StructureSession":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None


class TournamentStructureRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: StructureSession) -> None:
        async def override_session() -> AsyncIterator[StructureSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_structure_crud_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        for path in (
            "/api/tournament-phases",
            "/api/tournament-phases/{id}",
            "/api/tournament-sections",
            "/api/tournament-sections/{id}",
            "/api/section-participants",
            "/api/section-participants/{id}",
        ):
            self.assertIn(path, paths)

        self.assertIn("post", paths["/api/tournament-phases"])
        self.assertIn("patch", paths["/api/tournament-sections/{id}"])
        self.assertIn("post", paths["/api/section-participants"])
        self.assertIn("patch", paths["/api/section-participants/{id}"])

    def test_membership_create_accepts_matching_tournament(self) -> None:
        session = StructureSession([1, 1])
        self.use_session(session)

        response = self.client.post(
            "/api/section-participants",
            json={
                "participant_id": 2,
                "section_id": 3,
                "rating": 1800,
                "rating_source": "fide",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 7)
        self.assertTrue(session.committed)
        self.assertEqual(session.added.participant_id, 2)

    def test_membership_create_rejects_another_tournament(self) -> None:
        session = StructureSession([1, 2])
        self.use_session(session)

        response = self.client.post(
            "/api/section-participants",
            json={"participant_id": 2, "section_id": 3},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("different tournaments", response.json()["detail"])
        self.assertIsNone(session.added)
        self.assertFalse(session.committed)

    def test_membership_update_revalidates_parent_tournaments(self) -> None:
        membership = SectionParticipant(participant_id=2, section_id=3)
        membership.id = 8
        session = StructureSession([2, 1], membership)
        self.use_session(session)

        response = self.client.patch(
            "/api/section-participants/8",
            json={"section_id": 4},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(membership.section_id, 3)
        self.assertFalse(session.committed)


class TournamentStructureAdminTests(unittest.TestCase):
    def test_admin_views_use_relationship_selectors(self) -> None:
        phase_fields = [column.key for column in TournamentPhaseAdmin.form_columns]
        section_fields = [
            column.key for column in TournamentSectionAdmin.form_columns
        ]
        participant_fields = [
            column.key for column in SectionParticipantAdmin.form_columns
        ]

        self.assertIn("tournament", phase_fields)
        self.assertIn("phase", section_fields)
        self.assertIn("participant", participant_fields)
        self.assertIn("section", participant_fields)
        self.assertIn("source_section", participant_fields)
        self.assertNotIn("tournament_id", phase_fields)
        self.assertNotIn("phase_id", section_fields)


class TournamentStructureAdminValidationTests(
    unittest.IsolatedAsyncioTestCase,
):
    async def test_admin_rejects_membership_from_another_tournament(self) -> None:
        session = StructureSession([1, 2])
        view = SimpleNamespace(session_maker=lambda: session)

        with self.assertRaisesRegex(ValueError, "different tournaments"):
            await SectionParticipantAdmin.on_model_change(
                view,
                {"participant": 2, "section": 3},
                SectionParticipant(),
                True,
                Request({"type": "http"}),
            )

        self.assertFalse(session.committed)


if __name__ == "__main__":
    unittest.main()
