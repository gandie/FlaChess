from __future__ import annotations

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import Tournament, TournamentLifecycle


class SummaryResult:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self.rows


class SummarySession:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.statement: object | None = None

    async def execute(self, statement: object) -> SummaryResult:
        self.statement = statement
        return SummaryResult(self.rows)


class CreateSession:
    def __init__(self) -> None:
        self.tournament: Tournament | None = None
        self.committed = False

    def add(self, tournament: Tournament) -> None:
        self.tournament = tournament

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, tournament: Tournament) -> None:
        tournament.id = 8
        tournament.lifecycle = TournamentLifecycle.DRAFT


class TournamentCatalogRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_tournament_crud_has_typed_read_response(self) -> None:
        paths = app.openapi()["paths"]

        read_schema = paths["/api/tournaments/{id}"]["get"]["responses"]["200"][
            "content"
        ]["application/json"]["schema"]

        self.assertIn("TournamentResponse", read_schema["$ref"])

    def test_create_returns_the_new_tournament_id_for_navigation(self) -> None:
        session = CreateSession()

        async def override_session() -> AsyncIterator[CreateSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

        response = self.client.post(
            "/api/tournaments",
            json={"name": "Winter Open", "time_control": "25+5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 8)
        self.assertEqual(response.json()["lifecycle"], "draft")
        self.assertTrue(session.committed)

    def test_catalog_returns_summary_contract_without_generic_pagination(self) -> None:
        starts_at = datetime(2026, 12, 5, 10, 0, tzinfo=UTC)
        session = SummarySession(
            [
                SimpleNamespace(
                    id=7,
                    name="Club Championship",
                    description="Annual event",
                    lifecycle=TournamentLifecycle.DRAFT,
                    time_control="60+30",
                    starts_at=starts_at,
                    ends_at=None,
                    participant_count=12,
                    phase_count=2,
                    section_count=3,
                ),
            ],
        )

        async def override_session() -> AsyncIterator[SummarySession]:
            yield session

        app.dependency_overrides[get_session] = override_session

        response = self.client.get("/api/tournament-summaries")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 7,
                    "name": "Club Championship",
                    "description": "Annual event",
                    "lifecycle": "draft",
                    "time_control": "60+30",
                    "starts_at": "2026-12-05T10:00:00Z",
                    "ends_at": None,
                    "participant_count": 12,
                    "phase_count": 2,
                    "section_count": 3,
                },
            ],
        )
        self.assertIsNotNone(session.statement)


if __name__ == "__main__":
    unittest.main()
