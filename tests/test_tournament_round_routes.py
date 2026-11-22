from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.admin import GameAdmin, RoundParticipantAdmin
from app.database import get_session
from app.main import app
from app.models import Game, ParticipationType, RoundParticipant


class RoundSession:
    def __init__(
        self,
        section_ids: list[int | None],
        record: RoundParticipant | Game | None = None,
    ) -> None:
        self.section_ids = iter(section_ids)
        self.record = record
        self.added: RoundParticipant | Game | None = None
        self.committed = False

    async def scalar(self, statement: object) -> int | None:
        return next(self.section_ids)

    async def get(
        self,
        model: type[RoundParticipant] | type[Game],
        id: int,
    ) -> RoundParticipant | Game | None:
        return self.record

    def add(self, record: RoundParticipant | Game) -> None:
        record.id = 11
        self.added = record

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None

    async def __aenter__(self) -> "RoundSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class TournamentRoundRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: RoundSession) -> None:
        async def override_session() -> AsyncIterator[RoundSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_round_game_and_participation_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        for path in (
            "/api/tournament-rounds",
            "/api/tournament-rounds/{id}",
            "/api/round-participants",
            "/api/round-participants/{id}",
            "/api/games",
            "/api/games/{id}",
        ):
            self.assertIn(path, paths)

        self.assertIn("post", paths["/api/tournament-rounds"])
        self.assertIn("post", paths["/api/round-participants"])
        self.assertIn("patch", paths["/api/games/{id}"])

    def test_round_participation_accepts_round_section_member(self) -> None:
        session = RoundSession([4, 4])
        self.use_session(session)

        response = self.client.post(
            "/api/round-participants",
            json={
                "round_id": 8,
                "participant_id": 9,
                "participation_type": "bye",
                "score_awarded": 1,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 11)
        self.assertTrue(session.committed)

    def test_round_participation_rejects_other_section_member(self) -> None:
        session = RoundSession([4, 5])
        self.use_session(session)

        response = self.client.post(
            "/api/round-participants",
            json={
                "round_id": 8,
                "participant_id": 9,
                "participation_type": "paired",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("round's section", response.json()["detail"])
        self.assertIsNone(session.added)

    def test_game_create_rejects_member_from_other_section(self) -> None:
        session = RoundSession([4, 4, 5])
        self.use_session(session)

        response = self.client.post(
            "/api/games",
            json={
                "round_id": 8,
                "white_participant_id": 9,
                "black_participant_id": 10,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("round's section", response.json()["detail"])
        self.assertIsNone(session.added)

    def test_game_update_revalidates_merged_scores(self) -> None:
        game = Game(
            round_id=8,
            white_participant_id=9,
            black_participant_id=10,
            white_score=Decimal("1"),
            black_score=Decimal("0"),
        )
        game.id = 11
        session = RoundSession([4, 4, 4], game)
        self.use_session(session)

        response = self.client.patch(
            "/api/games/11",
            json={"black_score": 0.5},
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("sum to 1", response.json()["detail"])
        self.assertFalse(session.committed)


class TournamentRoundAdminValidationTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_rejects_game_from_another_section(self) -> None:
        session = RoundSession([4, 4, 5])
        view = SimpleNamespace(session_maker=lambda: session)

        with self.assertRaisesRegex(ValueError, "round's section"):
            await GameAdmin.on_model_change(
                view,
                {"round": 8, "white_participant": 9, "black_participant": 10},
                Game(),
                True,
                Request({"type": "http"}),
            )

    async def test_admin_rejects_paired_awarded_score(self) -> None:
        session = RoundSession([])
        view = SimpleNamespace(session_maker=lambda: session)

        with self.assertRaisesRegex(ValueError, "awarded score"):
            await RoundParticipantAdmin.on_model_change(
                view,
                {
                    "round": 8,
                    "participant": 9,
                    "participation_type": ParticipationType.PAIRED,
                    "score_awarded": 1,
                },
                RoundParticipant(),
                True,
                Request({"type": "http"}),
            )


if __name__ == "__main__":
    unittest.main()
