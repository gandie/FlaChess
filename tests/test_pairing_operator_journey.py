from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.database import get_session
from app.main import app
from app.models import (
    Game,
    SectionLifecycle,
    TournamentPhaseFormat,
)


FORMATS = (
    (
        TournamentPhaseFormat.SWISS,
        "swiss",
        "repeat_opponent_avoidance",
    ),
    (
        TournamentPhaseFormat.ROUND_ROBIN,
        "round_robin",
        "fixed_member_schedule",
    ),
    (
        TournamentPhaseFormat.KNOCKOUT,
        "knockout",
        "standard_seeded_bracket",
    ),
)


class ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return list(self.values)


class JourneySession:
    def __init__(
        self,
        pairing_format: TournamentPhaseFormat,
        *,
        fail_commit: bool = False,
    ) -> None:
        planned_round_count = {
            TournamentPhaseFormat.SWISS: 3,
            TournamentPhaseFormat.ROUND_ROBIN: 3,
            TournamentPhaseFormat.KNOCKOUT: 2,
        }[pairing_format]
        self.section = SimpleNamespace(
            id=9,
            lifecycle=SectionLifecycle.ACTIVE,
            planned_round_count=planned_round_count,
            phase=SimpleNamespace(format=pairing_format),
        )
        self.participants = [
            SimpleNamespace(
                id=index,
                section_id=9,
                seed_position=index,
                is_withdrawn=False,
            )
            for index in range(1, 5)
        ]
        self.batches = iter(
            [
                values
                for _ in range(3)
                for values in (self.participants, [], [])
            ],
        )
        self.added: list[object] = []
        self.games: dict[int, Game] = {}
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_commit = fail_commit

    async def scalar(self, statement: object) -> object:
        return self.section

    async def scalars(self, statement: object) -> ScalarResult:
        return ScalarResult(next(self.batches))

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: tuple[object, ...]) -> None:
        for index, value in enumerate(values, start=200 + len(self.games)):
            value.id = index
            if isinstance(value, Game):
                self.games[value.id] = value
        self.added.extend(values)

    async def flush(self) -> None:
        self.added[0].id = 100

    async def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("insert", {}, Exception("duplicate"))
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def get(self, model: object, record_id: int) -> object | None:
        if model is Game:
            return self.games.get(record_id)
        return None


class PairingOperatorJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: JourneySession) -> None:
        async def override_session() -> AsyncIterator[JourneySession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def preview_and_confirm(
        self,
        response_format: str,
        policy_label: str,
    ) -> None:
        preview = self.client.get(
            "/api/tournament-sections/9/pairing/preview",
        )
        confirmed = self.client.post(
            "/api/tournament-sections/9/pairing/confirm",
            json={"expected_round_number": 1},
        )

        self.assertEqual(preview.status_code, 200)
        self.assertIsNone(preview.json()["round_id"])
        self.assertEqual(preview.json()["format"], response_format)
        self.assertIn(policy_label, preview.json()["policy_labels"])
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.json()["round_id"], 100)
        self.assertEqual(confirmed.json()["target_round"], 1)
        self.assertEqual(len(confirmed.json()["games"]), 2)

    def record_result_and_recompute_standings(self) -> None:
        with patch(
            "app.routes.games.validate_game_members",
            new=AsyncMock(),
        ):
            result = self.client.patch(
                "/api/games/200",
                json={
                    "white_score": 1,
                    "black_score": 0,
                    "result_type": "normal",
                    "recorded_at": "2026-11-24T18:00:00Z",
                },
            )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["white_score"], "1")

        standing = SimpleNamespace(
            id=300,
            section_id=9,
            participant_id=1,
            through_round_id=100,
            rank=1,
            points=Decimal("1"),
            wins=1,
            draws=0,
            losses=0,
            game_points=Decimal("1"),
            computed_at=datetime.now(UTC),
            values=[],
        )
        with patch(
            "app.api.recompute_section_standings",
            new=AsyncMock(return_value=[standing]),
        ):
            standings = self.client.post(
                "/api/tournament-sections/9/standings/recompute"
                "?through_round_id=100",
            )
        self.assertEqual(standings.status_code, 200)
        self.assertEqual(standings.json()[0]["through_round_id"], 100)

    def test_each_format_completes_the_route_journey(self) -> None:
        for pairing_format, response_format, policy_label in FORMATS:
            with self.subTest(format=response_format):
                session = JourneySession(pairing_format)
                self.use_session(session)
                self.preview_and_confirm(response_format, policy_label)
                self.record_result_and_recompute_standings()
                self.assertEqual(session.rollback_count, 0)

    def test_stale_and_persistence_conflicts_are_visible(self) -> None:
        for pairing_format, response_format, _ in FORMATS:
            with self.subTest(format=response_format, failure="stale"):
                stale_session = JourneySession(pairing_format)
                self.use_session(stale_session)
                stale = self.client.post(
                    "/api/tournament-sections/9/pairing/confirm",
                    json={"expected_round_number": 2},
                )
                self.assertEqual(stale.status_code, 409)
                self.assertIn("stale or invalid", stale.json()["detail"])
                self.assertEqual(stale_session.added, [])

            with self.subTest(format=response_format, failure="rollback"):
                failed_session = JourneySession(
                    pairing_format,
                    fail_commit=True,
                )
                self.use_session(failed_session)
                conflict = self.client.post(
                    "/api/tournament-sections/9/pairing/confirm",
                    json={"expected_round_number": 1},
                )
                self.assertEqual(conflict.status_code, 409)
                self.assertIn("persistent data", conflict.json()["detail"])
                self.assertEqual(failed_session.commit_count, 0)
                self.assertEqual(failed_session.rollback_count, 1)


class PairingOperatorUIContractTests(unittest.TestCase):
    def test_ui_carries_results_to_standings_and_next_preview(self) -> None:
        client = TestClient(app)
        operations = client.get("/static/operations.js").text
        standings = client.get("/static/standings.js").text
        display = client.get("/static/display.js").text
        confirmation = operations.split(
            "function pairingConfirmAction",
            1,
        )[1].split("function pairingAutomation", 1)[0]

        self.assertNotIn("previewResult", confirmation)
        self.assertIn("errorSummary(error)", confirmation)
        self.assertIn("generated.round_id", operations)
        self.assertIn("focusResultEntry(activeRound)", operations)
        self.assertIn("/api/games/${game.id}", operations)
        self.assertIn("refreshAfterResult(round.id, game.id)", operations)
        self.assertIn("recomputeStandings({", operations)
        self.assertIn("roundIsComplete(latestRound)", operations)
        self.assertIn("previewButton.disabled = !previewReady", operations)
        self.assertIn("/standings?through_round_id=", standings)
        self.assertIn("latestRound(operation)", display)
        self.assertIn("/operation", display)

    def test_manual_round_and_pairing_fallbacks_remain_available(self) -> None:
        operations = TestClient(app).get("/static/operations.js").text

        self.assertIn("/api/tournament-rounds", operations)
        self.assertIn("/api/games", operations)
        self.assertIn("New round", operations)
        self.assertIn("New manual pairing", operations)
        self.assertIn("Add a manual pairing", operations)
        self.assertIn("New participation record", operations)


if __name__ == "__main__":
    unittest.main()
