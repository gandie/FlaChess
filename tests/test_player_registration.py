from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import (
    Player,
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
)


class RowsResult:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self.rows


class RegistrationSession:
    def __init__(
        self,
        *,
        tournament: Tournament | None = None,
        player: Player | None = None,
        registration: TournamentParticipant | None = None,
        rows: list[SimpleNamespace] | None = None,
    ) -> None:
        self.tournament = tournament
        self.player = player
        self.registration = registration
        self.rows = rows or []
        self.added: TournamentParticipant | None = None
        self.deleted: TournamentParticipant | None = None
        self.committed = False

    async def get(self, model: type, id: int) -> object | None:
        if model is Tournament:
            return self.tournament
        if model is Player:
            return self.player
        if model is TournamentParticipant:
            return self.registration
        return None

    async def execute(self, statement: object) -> RowsResult:
        return RowsResult(self.rows)

    def add(self, registration: TournamentParticipant) -> None:
        registration.id = 11
        self.added = registration

    async def refresh(self, registration: TournamentParticipant) -> None:
        registration.id = 11

    async def delete(self, registration: TournamentParticipant) -> None:
        self.deleted = registration

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False


class PlayerRegistrationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: RegistrationSession) -> None:
        async def override_session() -> AsyncIterator[RegistrationSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_player_and_registration_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/api/player-summaries", paths)
        self.assertIn("/api/tournaments/{tournament_id}/participants", paths)
        self.assertIn(
            "/api/tournaments/{tournament_id}/participants/{registration_id}",
            paths,
        )

    def test_player_summaries_return_a_direct_named_contract(self) -> None:
        session = RegistrationSession(
            rows=[
                SimpleNamespace(
                    id=4,
                    name="Nora",
                    avatar="data:image/png;base64,AAAA",
                ),
            ],
        )
        self.use_session(session)

        response = self.client.get("/api/player-summaries")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 4,
                    "name": "Nora",
                    "avatar": "data:image/png;base64,AAAA",
                },
            ],
        )

    def test_tournament_participants_include_player_names(self) -> None:
        tournament = Tournament(id=7, name="Winter Open")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        session = RegistrationSession(
            tournament=tournament,
            rows=[
                SimpleNamespace(
                    registration_id=12,
                    player_id=4,
                    player_name="Nora",
                    player_avatar="data:image/png;base64,AAAA",
                ),
            ],
        )
        self.use_session(session)

        response = self.client.get("/api/tournaments/7/participants")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "registration_id": 12,
                    "player_id": 4,
                    "player_name": "Nora",
                    "player_avatar": "data:image/png;base64,AAAA",
                },
            ],
        )

    def test_draft_registration_returns_the_named_player(self) -> None:
        tournament = Tournament(id=7, name="Winter Open")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        player = Player(id=4, name="Nora")
        player.avatar = "data:image/png;base64,AAAA"
        session = RegistrationSession(tournament=tournament, player=player)
        self.use_session(session)

        response = self.client.post(
            "/api/tournaments/7/participants",
            json={"player_id": 4},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "registration_id": 11,
                "player_id": 4,
                "player_name": "Nora",
                "player_avatar": "data:image/png;base64,AAAA",
            },
        )
        self.assertTrue(session.committed)
        self.assertEqual(session.added.tournament_id, 7)

    def test_active_tournament_rejects_registration(self) -> None:
        tournament = Tournament(id=7, name="Winter Open")
        tournament.lifecycle = TournamentLifecycle.ACTIVE
        session = RegistrationSession(tournament=tournament)
        self.use_session(session)

        response = self.client.post(
            "/api/tournaments/7/participants",
            json={"player_id": 4},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("draft tournaments", response.json()["detail"])
        self.assertIsNone(session.added)

    def test_draft_unregistration_deletes_scoped_registration(self) -> None:
        tournament = Tournament(id=7, name="Winter Open")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        registration = TournamentParticipant(tournament_id=7, player_id=4)
        registration.id = 12
        session = RegistrationSession(
            tournament=tournament,
            registration=registration,
        )
        self.use_session(session)

        response = self.client.delete(
            "/api/tournaments/7/participants/12",
        )

        self.assertEqual(response.status_code, 204)
        self.assertIs(session.deleted, registration)
        self.assertTrue(session.committed)


if __name__ == "__main__":
    unittest.main()
