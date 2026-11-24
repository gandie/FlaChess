import unittest
from itertools import combinations

from app.pairing import (
    Color,
    PairingParticipant,
    PairingValidationError,
    PlannedOutcomeType,
    RoundCountError,
    RoundRobinPairingError,
    plan_round_robin_round,
)


class RoundRobinPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.even = tuple(
            PairingParticipant(participant_id=seed * 10, seed_position=seed)
            for seed in range(1, 5)
        )
        self.odd = self.even[:3]

    def test_even_field_covers_every_unordered_pair_once(self) -> None:
        self.assert_complete_schedule(self.even, 3)

    def test_minimum_even_field_is_pairable(self) -> None:
        self.assert_complete_schedule(self.even[:2], 1)

    def test_odd_field_has_one_scoreless_bye_per_round(self) -> None:
        self.assert_complete_schedule(self.odd, 3)

        bye_recipients = []
        for round_number in range(1, 4):
            with self.subTest(round_number=round_number):
                plan = plan_round_robin_round(self.odd, round_number)
                bye_recipients.append(plan.outcomes[0].participant_id)
                self.assertEqual(len(plan.games), 1)
                self.assertEqual(len(plan.outcomes), 1)
                self.assertIs(plan.outcomes[0].outcome_type, PlannedOutcomeType.BYE)
                self.assertIsNone(plan.outcomes[0].score_awarded)
        self.assertCountEqual(
            bye_recipients,
            [participant.participant_id for participant in self.odd],
        )

    def test_larger_odd_field_covers_every_unordered_pair_once(self) -> None:
        participants = (
            *self.even,
            PairingParticipant(participant_id=50, seed_position=5),
        )

        self.assert_complete_schedule(participants, 5)

    def test_seed_order_controls_pairings_independent_of_input_order(self) -> None:
        reversed_field = tuple(reversed(self.even))

        expected = plan_round_robin_round(self.even, 1)
        self.assertEqual(
            plan_round_robin_round(reversed_field, 1),
            expected,
        )
        self.assertEqual(
            {
                (game.white_participant_id, game.black_participant_id)
                for game in expected.games
            },
            {(10, 40), (20, 30)},
        )

    def test_existing_color_history_is_applied_after_scheduling(self) -> None:
        participants = (
            PairingParticipant(10, 1, color_history=(Color.WHITE, Color.WHITE)),
            self.even[1],
            PairingParticipant(30, 3, color_history=(Color.BLACK, Color.BLACK)),
            self.even[3],
        )

        plan = plan_round_robin_round(participants, 1)

        self.assertIn(
            (30, 20),
            {
                (game.white_participant_id, game.black_participant_id)
                for game in plan.games
            },
        )

    def test_identical_inputs_are_deterministic(self) -> None:
        self.assertEqual(
            tuple(
                plan_round_robin_round(self.even, round_number)
                for round_number in range(1, 4)
            ),
            tuple(
                plan_round_robin_round(self.even, round_number)
                for round_number in range(1, 4)
            ),
        )

    def test_invalid_field_and_round_numbers_fail(self) -> None:
        for round_number in (0, 4, True):
            with self.subTest(round_number=round_number):
                with self.assertRaises(RoundRobinPairingError):
                    plan_round_robin_round(self.even, round_number)
        with self.assertRaises(RoundCountError):
            plan_round_robin_round((self.even[0],), 1)
        with self.assertRaises(PairingValidationError):
            plan_round_robin_round(
                (PairingParticipant(10, 1), PairingParticipant(10, 2)),
                1,
            )

    def assert_complete_schedule(
        self,
        participants: tuple[PairingParticipant, ...],
        round_count: int,
    ) -> None:
        expected_pairs = {
            frozenset((first.participant_id, second.participant_id))
            for first, second in combinations(participants, 2)
        }
        actual_pairs: list[frozenset[int]] = []
        for round_number in range(1, round_count + 1):
            plan = plan_round_robin_round(participants, round_number)
            actual_pairs.extend(
                frozenset((game.white_participant_id, game.black_participant_id))
                for game in plan.games
            )
            appearances = [
                participant_id
                for game in plan.games
                for participant_id in (
                    game.white_participant_id,
                    game.black_participant_id,
                )
            ]
            appearances.extend(
                outcome.participant_id for outcome in plan.outcomes
            )
            self.assertCountEqual(
                appearances,
                [participant.participant_id for participant in participants],
            )
            self.assertEqual(
                len(plan.games),
                len(participants) // 2,
            )
        self.assertEqual(set(actual_pairs), expected_pairs)
        self.assertEqual(len(actual_pairs), len(expected_pairs))


if __name__ == "__main__":
    unittest.main()
