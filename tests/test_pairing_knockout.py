import unittest
from decimal import Decimal

from app.pairing import (
    KnockoutPairingError,
    KnockoutPredecessor,
    PairingParticipant,
    PlannedOutcomeType,
    plan_knockout_round,
)


class KnockoutPairingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.eight = tuple(
            PairingParticipant(seed * 10, seed)
            for seed in range(1, 9)
        )

    def test_first_round_uses_standard_seeded_bracket_order(self) -> None:
        plan = plan_knockout_round(tuple(reversed(self.eight)), 1)

        self.assertEqual(
            unordered_pair_ids(plan),
            ((10, 80), (40, 50), (20, 70), (30, 60)),
        )

    def test_non_power_of_two_bracket_gives_structural_byes_to_top_seeds(
        self,
    ) -> None:
        participants = self.eight[:5]

        plan = plan_knockout_round(participants, 1)

        self.assertEqual(unordered_pair_ids(plan), ((40, 50),))
        self.assertEqual(
            [outcome.participant_id for outcome in plan.outcomes],
            [10, 20, 30],
        )
        for outcome in plan.outcomes:
            self.assertIs(outcome.outcome_type, PlannedOutcomeType.BYE)
            self.assertIsNone(outcome.score_awarded)

    def test_round_two_advances_decisive_winners_in_bracket_order(self) -> None:
        participants = self.eight[:5]
        predecessors = (
            KnockoutPredecessor(10),
            KnockoutPredecessor(40, 50, Decimal("0"), Decimal("1")),
            KnockoutPredecessor(20),
            KnockoutPredecessor(30),
        )

        plan = plan_knockout_round(participants, 2, predecessors)

        self.assertEqual(
            unordered_pair_ids(plan),
            ((10, 50), (20, 30)),
        )
        self.assertEqual(plan.outcomes, ())

    def test_drawn_predecessor_blocks_advancement(self) -> None:
        predecessors = (
            KnockoutPredecessor(10, 80, Decimal("0.5"), Decimal("0.5")),
            KnockoutPredecessor(40, 50, Decimal("1"), Decimal("0")),
            KnockoutPredecessor(20, 70, Decimal("1"), Decimal("0")),
            KnockoutPredecessor(30, 60, Decimal("1"), Decimal("0")),
        )

        with self.assertRaisesRegex(KnockoutPairingError, "drawn"):
            plan_knockout_round(self.eight, 2, predecessors)

    def test_unresolved_predecessor_blocks_advancement(self) -> None:
        predecessors = (
            KnockoutPredecessor(10, 80),
            KnockoutPredecessor(40, 50, Decimal("1"), Decimal("0")),
            KnockoutPredecessor(20, 70, Decimal("1"), Decimal("0")),
            KnockoutPredecessor(30, 60, Decimal("1"), Decimal("0")),
        )

        with self.assertRaisesRegex(KnockoutPairingError, "complete"):
            plan_knockout_round(self.eight, 2, predecessors)

    def test_final_round_completes_bracket_and_rejects_later_rounds(self) -> None:
        plan = plan_knockout_round(
            self.eight,
            3,
            (
                KnockoutPredecessor(10, 40, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(20, 30, Decimal("0"), Decimal("1")),
            ),
        )

        self.assertEqual(unordered_pair_ids(plan), ((10, 30),))
        with self.assertRaises(KnockoutPairingError):
            plan_knockout_round(self.eight, 4, ())

    def test_predecessors_must_match_expected_bracket_slots(self) -> None:
        cases = (
            (),
            (
                KnockoutPredecessor(10, 80, Decimal("1"), Decimal("0")),
            ),
            (
                KnockoutPredecessor(10, 80, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(10, 50, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(20, 70, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(30, 60, Decimal("1"), Decimal("0")),
            ),
            (
                KnockoutPredecessor(10, 99, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(40, 50, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(20, 70, Decimal("1"), Decimal("0")),
                KnockoutPredecessor(30, 60, Decimal("1"), Decimal("0")),
            ),
        )

        for predecessors in cases:
            with self.subTest(predecessors=predecessors):
                with self.assertRaises(KnockoutPairingError):
                    plan_knockout_round(self.eight, 2, predecessors)

    def test_structural_byes_are_rejected_after_round_two_predecessors(
        self,
    ) -> None:
        with self.assertRaisesRegex(KnockoutPairingError, "Structural byes"):
            plan_knockout_round(
                self.eight,
                3,
                (KnockoutPredecessor(10), KnockoutPredecessor(20)),
            )

    def test_identical_inputs_are_deterministic(self) -> None:
        expected = plan_knockout_round(self.eight, 1)

        self.assertEqual(
            expected,
            plan_knockout_round(tuple(reversed(self.eight)), 1),
        )


def unordered_pair_ids(plan: object) -> tuple[tuple[int, int], ...]:
    return tuple(
        tuple(sorted((game.white_participant_id, game.black_participant_id)))
        for game in plan.games  # type: ignore[attr-defined]
    )


if __name__ == "__main__":
    unittest.main()
