from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import GameResultType, ParticipationType, SectionLifecycle


class OperationResult:
    def __init__(
        self,
        values: list[object] | None = None,
        row: object | None = None,
    ) -> None:
        self.values = values or []
        self.row = row

    def all(self) -> list[object]:
        return self.values

    def scalars(self) -> "OperationResult":
        return self

    def one_or_none(self) -> object | None:
        return self.row


class OperationSession:
    def __init__(self, results: list[OperationResult]) -> None:
        self.results = iter(results)

    async def execute(self, statement: object) -> OperationResult:
        return next(self.results)


def named_operation_session() -> OperationSession:
    section = SimpleNamespace(
        id=9,
        name="Open",
        sequence=1,
        lifecycle=SectionLifecycle.ACTIVE,
        tie_break_locked_at=None,
        planned_round_count=5,
    )
    participant = SimpleNamespace(id=20, player_name="Nora", rating=1800)
    round_ = SimpleNamespace(id=30, number=1)
    tiebreak = SimpleNamespace(
        id=25,
        code="buchholz_cut_1",
        sequence=1,
        parameter=None,
    )
    game = SimpleNamespace(
        id=40,
        round_id=30,
        white_participant_id=20,
        white_player_name="Nora",
        black_participant_id=21,
        black_player_name="Jules",
        white_score=Decimal("1"),
        black_score=Decimal("0"),
        result_type=GameResultType.NORMAL,
        recorded_at=None,
        comment="Decisive game",
    )
    record = SimpleNamespace(
        id=50,
        round_id=30,
        participant_id=22,
        player_name="Mika",
        participation_type=ParticipationType.BYE,
        score_awarded=Decimal("1"),
        comment="Full-point bye",
    )
    return OperationSession(
        [
            OperationResult(row=(section, 7, "Club Open")),
            OperationResult(values=[participant]),
            OperationResult(values=[round_]),
            OperationResult(values=[tiebreak]),
            OperationResult(values=[game]),
            OperationResult(values=[record]),
        ],
    )


class SectionOperationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: OperationSession) -> None:
        async def override_session() -> AsyncIterator[OperationSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_operation_contract_is_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn(
            "/api/tournament-sections/{section_id}/operation",
            paths,
        )
        schema = paths[
            "/api/tournament-sections/{section_id}/operation"
        ]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertIn("SectionOperationResponse", schema["$ref"])

    def test_operation_returns_named_members_and_round_structure(self) -> None:
        self.use_session(named_operation_session())

        response = self.client.get(
            "/api/tournament-sections/9/operation",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tournament_id"], 7)
        self.assertEqual(payload["tournament_name"], "Club Open")
        self.assertEqual(payload["participants"][0]["player_name"], "Nora")
        self.assertEqual(payload["tiebreaks"][0]["code"], "buchholz_cut_1")
        self.assertEqual(payload["rounds"][0]["number"], 1)
        self.assertEqual(payload["rounds"][0]["games"][0]["black_player_name"], "Jules")
        self.assertEqual(payload["rounds"][0]["records"][0]["participation_type"], "bye")

    def test_operation_returns_404_for_missing_section(self) -> None:
        self.use_session(OperationSession([OperationResult()]))

        response = self.client.get(
            "/api/tournament-sections/404/operation",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "Tournament section not found",
        )


class SectionOperationFrontendTests(unittest.TestCase):
    def test_static_operation_controls_are_served(self) -> None:
        client = TestClient(app)

        operations = client.get("/static/operations.js").text
        standings = client.get("/static/standings.js").text
        structure = client.get("/static/structure.js").text
        tournaments = client.get("/static/tournaments.js").text

        self.assertIn("/operation", operations)
        self.assertIn("/api/tournament-rounds", operations)
        self.assertIn("/api/games", operations)
        self.assertIn("/api/round-participants", operations)
        self.assertIn("/standings/recompute", standings)
        self.assertIn("through_round_id", standings)
        self.assertIn("standingsReview", operations)
        self.assertIn('"Incomplete"', operations)
        self.assertIn("White and black must be different", operations)
        self.assertIn("whiteScore + blackScore !== 1", operations)
        self.assertIn("Open section operation", structure)
        self.assertIn("/activate", tournaments)


if __name__ == "__main__":
    unittest.main()
