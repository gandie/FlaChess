import unittest
from decimal import Decimal
from unittest.mock import patch

from app.pairing import (
    Color,
    PairingParticipant,
    PlannedOutcomeType,
    SwissPairingError,
    plan_swiss_round,
)


class SwissPairingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.field = (
            PairingParticipant(10, 1),
            PairingParticipant(20, 2),
            PairingParticipant(30, 3),
            PairingParticipant(40, 4),
        )

    def test_round_one_pairs_seeded_top_against_bottom(self) -> None:
        plan = plan_swiss_round(tuple(reversed(self.field)), 1)

        self.assertEqual(
            pair_ids(plan),
            ((10, 40), (30, 20)),
        )

    def test_later_round_pairs_within_score_groups(self) -> None:
        participants = (
            PairingParticipant(10, 1, Decimal("2"), (Decimal("8"),)),
            PairingParticipant(20, 2, Decimal("2"), (Decimal("7"),)),
            PairingParticipant(30, 3, Decimal("1"), (Decimal("6"),)),
            PairingParticipant(40, 4, Decimal("1"), (Decimal("5"),)),
        )

        plan = plan_swiss_round(participants, 2)

        self.assertCountEqual(
            unordered_pair_ids(plan),
            ((10, 20), (30, 40)),
        )

    def test_pairing_backtracks_to_avoid_repeats(self) -> None:
        plan = plan_swiss_round(
            self.field,
            2,
            previous_pairs=((10, 20), (30, 40)),
        )

        self.assertCountEqual(
            unordered_pair_ids(plan),
            ((10, 30), (20, 40)),
        )

    def test_minimum_repeat_is_used_when_repeat_free_plan_is_impossible(self) -> None:
        plan = plan_swiss_round(
            self.field[:2],
            2,
            previous_pairs=((10, 20),),
        )

        self.assertEqual(unordered_pair_ids(plan), ((10, 20),))

    def test_odd_score_group_floats_highest_seed_down(self) -> None:
        participants = (
            PairingParticipant(10, 3, Decimal("2"), (Decimal("9"),)),
            PairingParticipant(20, 2, Decimal("2")),
            PairingParticipant(30, 1, Decimal("2"), (Decimal("7"),)),
            PairingParticipant(40, 4, Decimal("1")),
        )

        plan = plan_swiss_round(participants, 2)

        self.assertCountEqual(
            unordered_pair_ids(plan),
            ((20, 30), (10, 40)),
        )

    def test_odd_field_awards_one_point_to_lowest_eligible_rank(self) -> None:
        participants = (
            PairingParticipant(10, 1, Decimal("2")),
            PairingParticipant(20, 2, Decimal("1")),
            PairingParticipant(30, 3, Decimal("0")),
            PairingParticipant(40, 4, Decimal("-1"), bye_count=1),
            PairingParticipant(50, 5, Decimal("-2")),
        )

        plan = plan_swiss_round(participants, 3)

        self.assertEqual(len(plan.outcomes), 1)
        self.assertEqual(plan.outcomes[0].participant_id, 50)
        self.assertIs(plan.outcomes[0].outcome_type, PlannedOutcomeType.BYE)
        self.assertEqual(plan.outcomes[0].score_awarded, Decimal("1"))

    def test_later_round_uses_existing_color_histories(self) -> None:
        participants = (
            PairingParticipant(
                10,
                1,
                Decimal("2"),
                color_history=(Color.WHITE, Color.WHITE),
            ),
            PairingParticipant(
                20,
                2,
                Decimal("2"),
                color_history=(Color.BLACK, Color.BLACK),
            ),
        )

        plan = plan_swiss_round(participants, 3)

        self.assertEqual(pair_ids(plan), ((20, 10),))

    def test_identical_inputs_are_deterministic(self) -> None:
        previous = ((10, 20), (30, 40))

        self.assertEqual(
            plan_swiss_round(self.field, 2, previous),
            plan_swiss_round(self.field, 2, previous),
        )

    def test_all_previous_bye_recipients_make_odd_plan_impossible(self) -> None:
        participants = tuple(
            PairingParticipant(
                participant.participant_id,
                participant.seed_position,
                bye_count=1,
            )
            for participant in self.field[:3]
        )

        with self.assertRaises(SwissPairingError):
            plan_swiss_round(participants, 2)

    def test_bounded_search_failure_is_explicit(self) -> None:
        with patch("app.pairing.swiss.MAX_SEARCH_STEPS", 0):
            with self.assertRaisesRegex(SwissPairingError, "0-step limit"):
                plan_swiss_round(self.field, 2)

    def test_invalid_round_and_previous_pairs_fail(self) -> None:
        with self.assertRaises(SwissPairingError):
            plan_swiss_round(self.field, True)
        with self.assertRaises(SwissPairingError):
            plan_swiss_round(self.field, 2, ((10, 99),))
        with self.assertRaises(SwissPairingError):
            plan_swiss_round(self.field, 2, ((10, 10),))


def pair_ids(plan: object) -> tuple[tuple[int, int], ...]:
    return tuple(
        (game.white_participant_id, game.black_participant_id)
        for game in plan.games  # type: ignore[attr-defined]
    )


def unordered_pair_ids(plan: object) -> tuple[tuple[int, int], ...]:
    return tuple(
        tuple(sorted(pair))
        for pair in pair_ids(plan)
    )


if __name__ == "__main__":
    unittest.main()
