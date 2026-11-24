from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class TournamentUsabilityFrontendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def static_asset(self, name: str) -> str:
        response = self.client.get(f"/static/{name}")
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_player_display_uses_only_existing_read_contracts(self) -> None:
        display = self.static_asset("display.js")
        app_module = self.static_asset("app.js")

        self.assertIn("/api/tournaments/${tournamentId}/workspace", display)
        self.assertIn("/api/tournament-sections/${section.id}/operation", display)
        self.assertIn(
            "/api/tournament-sections/${operation.id}/standings?through_round_id=",
            display,
        )
        self.assertIn("Upcoming games", display)
        self.assertIn("Current phase", display)
        self.assertNotIn("api.post", display)
        self.assertNotIn("api.patch", display)
        self.assertNotIn("api.delete", display)
        self.assertIn("/display/tournaments/:id", app_module)

    def test_operator_result_entry_has_shortcuts_before_standings(self) -> None:
        operations = self.static_asset("operations.js")
        active_round_block = operations.split("if (activeRound)", 1)[1]

        self.assertIn("result-queue", operations)
        self.assertIn("jumpToGame", operations)
        self.assertIn('"data-result-state":', operations)
        self.assertLess(
            active_round_block.index("roundPanel(context, activeRound)"),
            active_round_block.index("standingsReview({"),
        )
        self.assertIn("operation-disclosure", operations)
        self.assertIn("Activate this section?", operations)

    def test_operator_can_preview_and_confirm_generated_pairings(self) -> None:
        operations = self.static_asset("operations.js")

        self.assertIn("Preview next round", operations)
        self.assertIn("Confirm generation", operations)
        self.assertIn("/pairing/preview", operations)
        self.assertIn("/pairing/confirm", operations)
        self.assertIn("expected_round_number: preview.target_round", operations)
        self.assertIn("generated.round_id", operations)
        self.assertIn("window.location.hash =", operations)
        self.assertIn("/rounds/${generatedRoundId}", operations)
        self.assertIn("focusResultEntry(activeRound)", operations)
        self.assertIn('label: "White"', operations)
        self.assertIn('label: "Black"', operations)
        self.assertIn("Byes and non-paired outcomes", operations)
        self.assertIn("pairing-preview-warnings", operations)
        self.assertIn("Preview the next round before committing", operations)
        self.assertIn("previewResult.replaceChildren(review)", operations)
        self.assertIn("/api/tournament-rounds", operations)
        self.assertIn("New manual pairing", operations)

    def test_operator_advances_only_after_generated_round_is_complete(self) -> None:
        operations = self.static_asset("operations.js")
        display = self.static_asset("display.js")

        self.assertIn("roundIsComplete(latestRound)", operations)
        self.assertIn("if (changedRound) {", operations)
        self.assertIn("recomputeStandings({", operations)
        self.assertIn("previewButton.disabled = !previewReady", operations)
        self.assertIn("Record every result in round", operations)
        self.assertIn("function latestRound(operation)", display)
        self.assertIn(
            "/api/tournament-sections/${section.id}/operation",
            display,
        )
        self.assertIn("latestRound(operation)", display)

    def test_dense_views_keep_navigation_and_tables_keyboard_friendly(self) -> None:
        styles = self.static_asset("styles.css")
        tournaments = self.static_asset("tournaments.js")

        self.assertIn("position: sticky", styles)
        self.assertIn(".result-jump", styles)
        self.assertIn(".display-games-grid", styles)
        self.assertIn("@media (max-width: 42rem)", styles)
        self.assertIn("Open player display", tournaments)
        self.assertIn("Activate this tournament?", tournaments)


if __name__ == "__main__":
    unittest.main()
