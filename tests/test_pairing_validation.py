import unittest
from decimal import Decimal

from app.pairing import (
    PairingFormat,
    PairingParticipant,
    PairingPlan,
    PairingValidationError,
    PlannedGame,
    PlannedOutcome,
    PlannedOutcomeType,
    validate_complete_plan,
)


class PairingPlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.even = (
            PairingParticipant(10, 1),
            PairingParticipant(20, 2),
            PairingParticipant(30, 3),
            PairingParticipant(40, 4),
        )
        self.odd = self.even[:3]

    def test_complete_even_plan_is_valid(self) -> None:
        plan = PairingPlan(
            1,
            (PlannedGame(10, 40), PlannedGame(30, 20)),
        )

        self.assertIs(
            validate_complete_plan(
                plan,
                self.even,
                PairingFormat.ROUND_ROBIN,
            ),
            plan,
        )

    def test_complete_swiss_plan_has_one_point_bye_for_new_recipient(self) -> None:
        plan = PairingPlan(
            1,
            (PlannedGame(10, 30),),
            (PlannedOutcome(20, PlannedOutcomeType.BYE, Decimal("1")),),
        )

        validate_complete_plan(plan, self.odd, PairingFormat.SWISS)

    def test_plan_rejects_incomplete_duplicate_self_and_unknown_pairs(
        self,
    ) -> None:
        bad_plans = (
            PairingPlan(1, (PlannedGame(10, 40),)),
            PairingPlan(
                1,
                (PlannedGame(10, 40), PlannedGame(10, 30)),
            ),
            PairingPlan(
                1,
                (PlannedGame(10, 10), PlannedGame(30, 40)),
            ),
            PairingPlan(
                1,
                (PlannedGame(10, 99), PlannedGame(30, 40)),
            ),
        )
        for plan in bad_plans:
            with self.subTest(plan=plan):
                with self.assertRaises(PairingValidationError):
                    validate_complete_plan(
                        plan,
                        self.even,
                        PairingFormat.ROUND_ROBIN,
                    )

    def test_plan_rejects_repeats_unless_explicitly_budgeted(self) -> None:
        plan = PairingPlan(
            2,
            (PlannedGame(10, 40), PlannedGame(20, 30)),
        )
        with self.assertRaises(PairingValidationError):
            validate_complete_plan(
                plan,
                self.even,
                PairingFormat.SWISS,
                previous_pairs=((40, 10),),
            )

        validate_complete_plan(
            plan,
            self.even,
            PairingFormat.SWISS,
            previous_pairs=((40, 10),),
            max_repeat_pairs=1,
        )

    def test_swiss_bye_policy_rejects_wrong_field_shape_and_score(self) -> None:
        bad_plans = (
            PairingPlan(1, (PlannedGame(10, 30),)),
            PairingPlan(
                1,
                (PlannedGame(10, 30),),
                (
                    PlannedOutcome(
                        20,
                        PlannedOutcomeType.BYE,
                        Decimal("0.5"),
                    ),
                ),
            ),
            PairingPlan(
                1,
                (PlannedGame(10, 40),),
                (
                    PlannedOutcome(
                        30,
                        PlannedOutcomeType.BYE,
                        Decimal("1"),
                    ),
                    PlannedOutcome(
                        20,
                        PlannedOutcomeType.BYE,
                        Decimal("1"),
                    ),
                ),
            ),
        )
        participants = (self.odd, self.odd, self.even)
        for plan, field in zip(bad_plans, participants):
            with self.subTest(plan=plan):
                with self.assertRaises(PairingValidationError):
                    validate_complete_plan(
                        plan,
                        field,
                        PairingFormat.SWISS,
                    )

    def test_swiss_bye_rejects_a_second_bye(self) -> None:
        participants = (
            PairingParticipant(10, 1),
            PairingParticipant(20, 2),
            PairingParticipant(30, 3, bye_count=1),
        )
        plan = PairingPlan(
            2,
            (PlannedGame(10, 20),),
            (
                PlannedOutcome(
                    30,
                    PlannedOutcomeType.BYE,
                    Decimal("1"),
                ),
            ),
        )

        with self.assertRaises(PairingValidationError):
            validate_complete_plan(
                plan,
                participants,
                PairingFormat.SWISS,
            )

    def test_structural_bye_rejects_an_awarded_score(self) -> None:
        plan = PairingPlan(
            1,
            (PlannedGame(10, 20),),
            (PlannedOutcome(30, PlannedOutcomeType.BYE, Decimal("1")),),
        )

        with self.assertRaises(PairingValidationError):
            validate_complete_plan(
                plan,
                self.odd,
                PairingFormat.ROUND_ROBIN,
            )

    def test_plan_rejects_invalid_control_values(self) -> None:
        plan = PairingPlan(
            1,
            (PlannedGame(10, 40), PlannedGame(20, 30)),
        )
        for repeat_limit in (-1, True):
            with self.subTest(repeat_limit=repeat_limit):
                with self.assertRaises(PairingValidationError):
                    validate_complete_plan(
                        plan,
                        self.even,
                        PairingFormat.ROUND_ROBIN,
                        max_repeat_pairs=repeat_limit,
                    )

        with self.assertRaises(PairingValidationError):
            validate_complete_plan(
                PairingPlan(True, plan.games),
                self.even,
                PairingFormat.ROUND_ROBIN,
            )

    def test_plan_rejects_an_unknown_outcome_type(self) -> None:
        plan = PairingPlan(
            1,
            (PlannedGame(10, 20),),
            (PlannedOutcome(30, "other"),),  # type: ignore[arg-type]
        )

        with self.assertRaises(PairingValidationError):
            validate_complete_plan(
                plan,
                self.odd,
                PairingFormat.ROUND_ROBIN,
            )

    def test_participant_seeds_and_ids_must_be_unique_and_positive(self) -> None:
        invalid_sets = (
            (PairingParticipant(10, 1), PairingParticipant(10, 2)),
            (PairingParticipant(10, 1), PairingParticipant(20, 1)),
            (PairingParticipant(0, 1),),
            (PairingParticipant(10, 0),),
        )
        for participants in invalid_sets:
            with self.subTest(participants=participants):
                with self.assertRaises(PairingValidationError):
                    validate_complete_plan(
                        PairingPlan(1),
                        participants,
                        PairingFormat.ROUND_ROBIN,
                    )


if __name__ == "__main__":
    unittest.main()
