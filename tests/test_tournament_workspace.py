from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import (
    SectionLifecycle,
    SectionTiebreak,
    Tournament,
    TournamentLifecycle,
    TournamentPhase,
    TournamentPhaseFormat,
    TournamentSection,
)
from app.standings.ranking import SUPPORTED_TIEBREAK_CODES


class WorkspaceResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values

    def scalars(self) -> "WorkspaceResult":
        return self


class WorkspaceSession:
    def __init__(
        self,
        tournament: Tournament | None,
        results: list[list[object]],
    ) -> None:
        self.tournament = tournament
        self.results = iter(results)

    async def get(self, model: type, id: int) -> Tournament | None:
        return self.tournament

    async def execute(self, statement: object) -> WorkspaceResult:
        return WorkspaceResult(next(self.results))


def phase() -> TournamentPhase:
    return TournamentPhase(
        id=2,
        tournament_id=7,
        sequence=1,
        format=TournamentPhaseFormat.SWISS,
    )


def section() -> TournamentSection:
    return TournamentSection(
        id=3,
        phase_id=2,
        name="Open",
        sequence=1,
        lifecycle=SectionLifecycle.DRAFT,
        planned_round_count=5,
    )


def workspace_member() -> SimpleNamespace:
    return SimpleNamespace(
        id=20,
        section_id=3,
        registration_id=10,
        player_id=4,
        player_name="Nora",
        rating=1800,
        rating_source="fide",
        source_section_id=1,
        source_section_name="Preliminary",
        source_rank=2,
        seed_position=4,
        is_withdrawn=False,
    )


class TournamentWorkspaceRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: WorkspaceSession) -> None:
        async def override_session() -> AsyncIterator[WorkspaceSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_workspace_contract_is_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/api/tournaments/{tournament_id}/workspace", paths)
        schema = paths["/api/tournaments/{tournament_id}/workspace"]["get"][
            "responses"
        ]["200"]["content"]["application/json"]["schema"]
        self.assertIn("TournamentWorkspaceResponse", schema["$ref"])

    def test_workspace_returns_named_structure_membership_and_rules(self) -> None:
        tournament = Tournament(id=7, name="Club Open")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        participant = SimpleNamespace(
            registration_id=10,
            player_id=4,
            player_name="Nora",
        )
        rule = SectionTiebreak(
            id=30,
            section_id=3,
            code="buchholz_cut_1",
            sequence=1,
            is_active=True,
        )
        self.use_session(
            WorkspaceSession(
                tournament,
                [[participant], [phase()], [section()], [workspace_member()], [rule]],
            ),
        )

        response = self.client.get("/api/tournaments/7/workspace")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "Club Open")
        self.assertEqual(payload["participants"][0]["player_name"], "Nora")
        open_section = payload["phases"][0]["sections"][0]
        self.assertEqual(open_section["participants"][0]["rating"], 1800)
        self.assertEqual(
            open_section["participants"][0]["source_section_name"],
            "Preliminary",
        )
        self.assertEqual(open_section["participants"][0]["source_rank"], 2)
        self.assertEqual(open_section["participants"][0]["seed_position"], 4)
        self.assertFalse(open_section["participants"][0]["is_withdrawn"])
        self.assertTrue(open_section["tiebreaks"][0]["supported"])
        self.assertEqual(
            payload["supported_tiebreak_codes"],
            list(SUPPORTED_TIEBREAK_CODES),
        )
        self.assertFalse(payload["readiness"]["can_activate"])
        self.assertIn("at least two", payload["readiness"]["blocking_issues"][0])

    def test_workspace_marks_unsupported_rule_without_new_activation_block(self) -> None:
        tournament = Tournament(id=7, name="Club Open")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        participants = [
            SimpleNamespace(
                registration_id=index,
                player_id=index,
                player_name=f"Player {index}",
            )
            for index in (1, 2)
        ]
        rule = SectionTiebreak(
            id=30,
            section_id=3,
            code="future_policy",
            sequence=1,
            is_active=True,
        )
        self.use_session(
            WorkspaceSession(
                tournament,
                [participants, [phase()], [section()], [], [rule]],
            ),
        )

        response = self.client.get("/api/tournaments/7/workspace")

        payload = response.json()
        self.assertTrue(payload["readiness"]["can_activate"])
        self.assertEqual(payload["readiness"]["blocking_issues"], [])
        configured = payload["phases"][0]["sections"][0]["tiebreaks"][0]
        self.assertFalse(configured["supported"])
        self.assertIn(
            "unsupported",
            " ".join(payload["readiness"]["setup_warnings"]).lower(),
        )

    def test_workspace_returns_404_for_missing_tournament(self) -> None:
        self.use_session(WorkspaceSession(None, []))

        response = self.client.get("/api/tournaments/404/workspace")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Tournament not found")


class TournamentWorkspaceFrontendTests(unittest.TestCase):
    def test_static_structure_controls_are_served(self) -> None:
        client = TestClient(app)

        structure = client.get("/static/structure.js").text
        overview = client.get("/static/tournaments.js").text

        self.assertIn("/api/tournament-phases", structure)
        self.assertIn("/api/tournament-sections", structure)
        self.assertIn("/api/section-participants", structure)
        self.assertIn("/api/section-tiebreaks", structure)
        self.assertIn("Only standings-supported codes", structure)
        self.assertIn("source_section_id", structure)
        self.assertIn("source_rank", structure)
        self.assertIn("seed_position", structure)
        self.assertIn("is_withdrawn", structure)
        self.assertIn("re-enter", structure)
        self.assertIn("withdraw", structure)
        self.assertIn("Review final standings", structure)
        self.assertIn("/workspace", overview)


if __name__ == "__main__":
    unittest.main()
