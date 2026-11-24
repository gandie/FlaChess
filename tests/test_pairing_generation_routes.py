from __future__ import annotations

import unittest
from decimal import Decimal
from types import SimpleNamespace
from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import SectionLifecycle, TournamentPhaseFormat
from app.pairing.generation import PairingPreview, preview_next_round
from app.pairing.generation_state import (
    PairingGenerationConflict,
    PairingGenerationError,
    PairingGenerationNotFound,
)
from app.pairing.types import (
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PlannedGame,
    PlannedOutcome,
    PlannedOutcomeType,
)


class PreviewResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class PreviewSession:
    def __init__(self) -> None:
        self.section = SimpleNamespace(
            id=7,
            lifecycle=SectionLifecycle.ACTIVE,
            planned_round_count=2,
            phase=SimpleNamespace(format=TournamentPhaseFormat.SWISS),
        )
        self.batches = iter(
            [
                [
                    SimpleNamespace(
                        id=index,
                        section_id=7,
                        seed_position=index,
                        is_withdrawn=False,
                    )
                    for index in range(1, 4)
                ],
                [],
                [],
            ],
        )
        self.added: list[object] = []
        self.commit_count = 0
        self.rollback_count = 0

    async def scalar(self, statement: object) -> object:
        return self.section

    async def scalars(self, statement: object) -> PreviewResult:
        return PreviewResult(next(self.batches))

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: tuple[object, ...]) -> None:
        self.added.extend(values)

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class ExpiringPreviewSession(PreviewSession):
    async def scalars(self, statement: object) -> PreviewResult:
        self.section.phase = PhaseUnavailable()
        return await super().scalars(statement)


class PhaseUnavailable:
    @property
    def format(self) -> object:
        raise AssertionError("Expired phase triggered an async lazy load")


def swiss_preview() -> PairingPreview:
    return PairingPreview(
        section_id=9,
        pairing_format=PairingFormat.SWISS,
        planned_round_count=3,
        calculated_round_count=3,
        plan=PairingPlan(
            round_number=2,
            games=(PlannedGame(10, 11),),
            outcomes=(
                PlannedOutcome(
                    12,
                    PlannedOutcomeType.BYE,
                    Decimal("1"),
                ),
            ),
        ),
        seed_order=(
            PairingParticipant(10, 1),
            PairingParticipant(11, 2),
            PairingParticipant(12, 3),
        ),
    )


class PairingPreviewDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_preview_uses_generation_path_without_writes(self) -> None:
        session = PreviewSession()

        preview = await preview_next_round(7, session)

        self.assertEqual(preview.plan.round_number, 1)
        self.assertEqual(preview.planned_round_count, 2)
        self.assertEqual(preview.calculated_round_count, 2)
        self.assertEqual(
            [participant.seed_position for participant in preview.seed_order],
            [1, 2, 3],
        )
        self.assertEqual(session.added, [])
        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 0)

    async def test_preview_does_not_read_phase_after_other_state_loads(self) -> None:
        preview = await preview_next_round(7, ExpiringPreviewSession())

        self.assertIs(preview.pairing_format, PairingFormat.SWISS)


class PairingGenerationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self) -> None:
        async def override_session() -> AsyncIterator[object]:
            yield object()

        app.dependency_overrides[get_session] = override_session

    def test_pairing_routes_expose_read_and_command_contracts(self) -> None:
        paths = app.openapi()["paths"]

        preview = paths[
            "/api/tournament-sections/{section_id}/pairing/preview"
        ]["get"]
        confirm = paths[
            "/api/tournament-sections/{section_id}/pairing/confirm"
        ]["post"]
        self.assertIn("PairingPlanRead", preview["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"])
        self.assertIn("PairingConfirmationCommand", confirm["requestBody"][
            "content"
        ]["application/json"]["schema"]["$ref"])

    def test_preview_returns_complete_plan_without_generating(self) -> None:
        self.use_session()
        preview = swiss_preview()
        with (
            patch(
                "app.routes.pairing_generation.preview_next_round",
                new=AsyncMock(return_value=preview),
            ),
            patch(
                "app.routes.pairing_generation.generate_next_round",
                new=AsyncMock(),
            ) as generate,
        ):
            response = self.client.get(
                "/api/tournament-sections/9/pairing/preview",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNone(payload["round_id"])
        self.assertEqual(payload["target_round"], 2)
        self.assertEqual(payload["format"], "swiss")
        self.assertEqual(payload["games"][0]["white_participant_id"], 10)
        self.assertEqual(payload["outcomes"][0]["score_awarded"], "1")
        self.assertEqual(
            [item["seed_position"] for item in payload["seed_order"]],
            [1, 2, 3],
        )
        self.assertIn("repeat_opponent_avoidance", payload["policy_labels"])
        self.assertIn("one-point Swiss bye", payload["warnings"][0])
        generate.assert_not_awaited()

    def test_confirm_revalidates_then_uses_transactional_command(self) -> None:
        self.use_session()
        preview = swiss_preview()
        generated = SimpleNamespace(
            round=SimpleNamespace(id=81),
            plan=PairingPlan(
                round_number=2,
                games=(PlannedGame(11, 10),),
            ),
        )
        with (
            patch(
                "app.routes.pairing_generation.preview_next_round",
                new=AsyncMock(return_value=preview),
            ) as preview_mock,
            patch(
                "app.routes.pairing_generation.generate_next_round",
                new=AsyncMock(return_value=generated),
            ) as generate,
        ):
            response = self.client.post(
                "/api/tournament-sections/9/pairing/confirm",
                json={"expected_round_number": 2},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["round_id"], 81)
        self.assertEqual(
            response.json()["games"][0]["white_participant_id"],
            11,
        )
        preview_mock.assert_awaited_once_with(9, unittest.mock.ANY, 2)
        generate.assert_awaited_once_with(9, unittest.mock.ANY, 2)

    def test_confirm_rejects_stale_preview_without_generating(self) -> None:
        self.use_session()
        stale = PairingGenerationConflict(
            "Round 2 is stale or invalid; the next round is 3.",
        )
        with (
            patch(
                "app.routes.pairing_generation.preview_next_round",
                new=AsyncMock(side_effect=stale),
            ),
            patch(
                "app.routes.pairing_generation.generate_next_round",
                new=AsyncMock(),
            ) as generate,
        ):
            response = self.client.post(
                "/api/tournament-sections/9/pairing/confirm",
                json={"expected_round_number": 2},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("next round is 3", response.json()["detail"])
        generate.assert_not_awaited()

    def test_preview_maps_actionable_domain_errors(self) -> None:
        self.use_session()
        cases = (
            (PairingGenerationNotFound("Tournament section 404 was not found."), 404),
            (PairingGenerationError("Participant 10 is missing a seed position."), 422),
        )
        for error, expected_status in cases:
            with self.subTest(status=expected_status), patch(
                "app.routes.pairing_generation.preview_next_round",
                new=AsyncMock(side_effect=error),
            ):
                response = self.client.get(
                    "/api/tournament-sections/9/pairing/preview",
                )
            self.assertEqual(response.status_code, expected_status)
            self.assertEqual(response.json()["detail"], str(error))

    def test_confirm_requires_positive_target_round(self) -> None:
        self.use_session()

        response = self.client.post(
            "/api/tournament-sections/9/pairing/confirm",
            json={"expected_round_number": 0},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
