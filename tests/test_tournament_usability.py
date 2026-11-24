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

    def test_player_display_supports_round_history_and_finished_ceremony(self) -> None:
        display = self.static_asset("display.js")
        styles = self.static_asset("styles.css")

        self.assertIn("display-round-selector", display)
        self.assertIn("selectedSnapshotKey", display)
        self.assertIn("operations.flatMap", display)
        self.assertIn("victoryCeremony", display)
        self.assertIn("Tournament complete", display)
        self.assertIn("section-podium", display)
        self.assertIn("selectedRound = latestRound(operation)", display)
        self.assertIn(".display-tournament-finished", styles)
        self.assertIn(".victory-ceremony", styles)
        self.assertIn(".podium-place-1", styles)
        self.assertIn("prefers-reduced-motion", styles)
        self.assertNotIn("api.post", display)
        self.assertNotIn("api.patch", display)
        self.assertNotIn("api.delete", display)

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

    def test_tournament_desk_surfaces_live_work_and_round_actions(self) -> None:
        app_module = self.static_asset("app.js")
        operations = self.static_asset("operations.js")
        styles = self.static_asset("styles.css")
        index = self.static_asset("index.html")

        self.assertIn("Tournament command desk", app_module)
        self.assertIn("/api/tournament-summaries", app_module)
        self.assertIn("Open tournament", app_module)
        self.assertIn("live-round-rail", operations)
        self.assertIn("Tournament overview", operations)
        active_round_block = operations.split("if (activeRound)", 1)[1]
        self.assertLess(
            active_round_block.index("automation ? [automation]"),
            active_round_block.index("roundPanel(context, activeRound)"),
        )
        self.assertIn("--clock: #ef6246", styles)
        self.assertIn(".command-deck", styles)
        self.assertIn(".live-round-rail", styles)
        self.assertIn('class="brand-mark"', index)
        self.assertIn("prefers-reduced-motion", styles)

    def test_tournament_setup_uses_direct_player_actions_and_compact_sections(self) -> None:
        players = self.static_asset("players.js")
        structure = self.static_asset("structure.js")
        tournaments = self.static_asset("tournaments.js")
        styles = self.static_asset("styles.css")

        self.assertIn("registrationRoster", players)
        self.assertIn("Add ${player.name}", players)
        self.assertIn("Remove ${player.name}", players)
        self.assertNotIn("registration_player", players)
        self.assertIn("membershipAssignmentRow", structure)
        self.assertIn("nextSeedPosition", structure)
        self.assertIn("Next seed ${nextSeed}", structure)
        self.assertIn("Advancement details", structure)
        self.assertIn('seed.control.dataset.generatedSeed = "true"', structure)
        self.assertIn('seed.control.dataset.userEdited = "true"', structure)
        self.assertNotIn('label: "Registered player"', structure)
        self.assertIn("setupDisclosure", structure)
        self.assertIn('context.workspace.lifecycle === "draft"', structure)
        self.assertIn("Section roster and assignments", structure)
        self.assertIn("section.participants.length", structure)
        self.assertIn(": membership,", structure)
        self.assertIn("preserveView: true", tournaments)
        self.assertIn("captureWorkspaceState", tournaments)
        self.assertIn("restoreWorkspaceState", tournaments)
        self.assertIn('focus({ preventScroll: true })', tournaments)
        self.assertIn('control.dataset.generatedSeed === "true"', tournaments)
        self.assertIn("tournament-workspace", tournaments)
        self.assertIn("Edit tournament metadata", tournaments)
        self.assertIn(".tournament-workspace", styles)
        self.assertIn(".player-action-row", styles)
        self.assertIn(".membership-assignment-row", styles)
        self.assertIn(".setup-disclosure", styles)
        self.assertIn("@media (max-width: 52rem)", styles)
        self.assertIn(".workspace-sidebar .form-grid", styles)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", styles)
        self.assertIn("min-width: 0;", styles)


if __name__ == "__main__":
    unittest.main()
