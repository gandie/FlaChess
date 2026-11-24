import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from app.pairing import (
    Color,
    ColorAllocationContext,
    ColorAllocationError,
    PairingFormat,
    PairingParticipant,
    RoundCountError,
    allocate_colors,
    calculate_knockout_round_count,
    calculate_round_robin_round_count,
    calculate_swiss_round_count,
    order_by_seed,
    order_by_standings,
    order_for_downward_float,
    validate_planned_round_count,
)


class PairingTypeTests(unittest.TestCase):
    def test_pairing_inputs_are_immutable(self) -> None:
        participant = PairingParticipant(participant_id=4, seed_position=2)

        with self.assertRaises(FrozenInstanceError):
            participant.seed_position = 3  # type: ignore[misc]


class RoundCountTests(unittest.TestCase):
    def test_swiss_uses_the_operator_plan(self) -> None:
        self.assertEqual(calculate_swiss_round_count(8, 5), 5)
        self.assertEqual(
            validate_planned_round_count(
                PairingFormat.SWISS,
                8,
                5,
            ),
            5,
        )

    def test_round_robin_counts_even_and_odd_fields(self) -> None:
        self.assertEqual(calculate_round_robin_round_count(8), 7)
        self.assertEqual(calculate_round_robin_round_count(7), 7)

    def test_knockout_counts_padded_bracket_rounds(self) -> None:
        self.assertEqual(calculate_knockout_round_count(2), 1)
        self.assertEqual(calculate_knockout_round_count(5), 3)
        self.assertEqual(calculate_knockout_round_count(8), 3)
        self.assertEqual(calculate_knockout_round_count(9), 4)

    def test_calculated_formats_reject_a_different_plan(self) -> None:
        with self.assertRaises(RoundCountError):
            validate_planned_round_count(
                PairingFormat.ROUND_ROBIN,
                8,
                8,
            )
        with self.assertRaises(RoundCountError):
            validate_planned_round_count(
                PairingFormat.KNOCKOUT,
                5,
                4,
            )

    def test_all_formats_reject_unpairable_or_invalid_fields(self) -> None:
        calculators = (
            lambda: calculate_swiss_round_count(1, 4),
            lambda: calculate_round_robin_round_count(1),
            lambda: calculate_knockout_round_count(0),
            lambda: calculate_swiss_round_count(4, 0),
            lambda: calculate_round_robin_round_count(True),
        )
        for calculator in calculators:
            with self.subTest(calculator=calculator):
                with self.assertRaises(RoundCountError):
                    calculator()


class PairingOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.participants = (
            PairingParticipant(30, 3, Decimal("2"), (Decimal("4"),)),
            PairingParticipant(20, 2, Decimal("2"), (Decimal("5"),)),
            PairingParticipant(10, 1, Decimal("3"), (Decimal("1"),)),
            PairingParticipant(40, 4, Decimal("2"), (Decimal("5"),)),
        )

    def test_seed_order_uses_stable_participant_id_as_final_tie_break(self) -> None:
        self.assertEqual(
            [participant.participant_id for participant in order_by_seed(self.participants)],
            [10, 20, 30, 40],
        )

    def test_standings_order_applies_configured_values_then_seed_and_id(self) -> None:
        self.assertEqual(
            [
                participant.participant_id
                for participant in order_by_standings(self.participants)
            ],
            [10, 20, 40, 30],
        )

    def test_downward_float_prefers_highest_seed_number_first(self) -> None:
        self.assertEqual(
            [
                participant.participant_id
                for participant in order_for_downward_float(self.participants)
            ],
            [40, 30, 20, 10],
        )


class ColorAllocationTests(unittest.TestCase):
    def test_first_swiss_round_alternates_the_higher_seeds_color(self) -> None:
        participants = (
            PairingParticipant(10, 1, color_history=(Color.BLACK,)),
            PairingParticipant(20, 2),
        )
        first = allocate_colors(
            participants[0],
            participants[1],
            ColorAllocationContext(PairingFormat.SWISS, 1, 1),
        )
        second = allocate_colors(
            participants[0],
            participants[1],
            ColorAllocationContext(PairingFormat.SWISS, 1, 2),
        )

        self.assertEqual(
            (first.white_participant_id, first.black_participant_id),
            (10, 20),
        )
        self.assertEqual(
            (second.white_participant_id, second.black_participant_id),
            (20, 10),
        )

    def test_streak_avoidance_precedes_balance_and_seed_fallback(self) -> None:
        white_streak = PairingParticipant(
            10,
            1,
            color_history=(Color.WHITE, Color.WHITE),
        )
        black_streak = PairingParticipant(
            20,
            2,
            color_history=(Color.BLACK, Color.BLACK),
        )

        assignment = allocate_colors(
            white_streak,
            black_streak,
            ColorAllocationContext(PairingFormat.ROUND_ROBIN, 2, 1),
        )

        self.assertEqual(assignment.white_participant_id, 20)

    def test_balanced_color_histories_precede_seed_fallback(self) -> None:
        first = PairingParticipant(
            10,
            1,
            color_history=(Color.WHITE, Color.BLACK, Color.BLACK),
        )
        second = PairingParticipant(20, 2, color_history=(Color.WHITE,))

        assignment = allocate_colors(
            first,
            second,
            ColorAllocationContext(PairingFormat.KNOCKOUT, 1, 1),
        )

        self.assertEqual(assignment.white_participant_id, 10)

    def test_unresolved_color_tie_uses_seed_then_id(self) -> None:
        assignment = allocate_colors(
            PairingParticipant(20, 2),
            PairingParticipant(10, 1),
            ColorAllocationContext(PairingFormat.ROUND_ROBIN, 1, 1),
        )

        self.assertEqual(assignment.white_participant_id, 10)

    def test_color_allocator_rejects_self_pairing_and_bad_context(self) -> None:
        participant = PairingParticipant(10, 1)
        with self.assertRaises(ColorAllocationError):
            allocate_colors(
                participant,
                participant,
                ColorAllocationContext(PairingFormat.SWISS, 2, 1),
            )
        with self.assertRaises(ColorAllocationError):
            allocate_colors(
                participant,
                PairingParticipant(20, 2),
                ColorAllocationContext(PairingFormat.SWISS, 0, 1),
            )


if __name__ == "__main__":
    unittest.main()
