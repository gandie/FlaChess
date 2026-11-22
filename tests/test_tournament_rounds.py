import unittest
from decimal import Decimal

from sqlalchemy import BigInteger, Integer, Numeric

from app.database import Base
from app.models import (
    Game,
    GameResultType,
    ParticipationType,
    RoundParticipant,
    TournamentRound,
)
from app.schemas import (
    GameCreate,
    GameUpdate,
    RoundParticipantCreate,
    RoundParticipantUpdate,
    TournamentRoundCreate,
)


class TournamentRoundModelTests(unittest.TestCase):
    def test_round_and_participation_constraints_are_defined(self) -> None:
        round_table = Base.metadata.tables[TournamentRound.__tablename__]
        participant_table = Base.metadata.tables[RoundParticipant.__tablename__]

        self.assertIsInstance(round_table.c.id.type, BigInteger)
        self.assertIsInstance(round_table.c.number.type, Integer)
        self.assertEqual(
            set(participant_table.c.participation_type.type.enums),
            {"paired", "bye", "unplayed", "absent"},
        )
        self.assertIsInstance(participant_table.c.score_awarded.type, Numeric)
        constraint_names = {
            constraint.name
            for table in (round_table, participant_table)
            for constraint in table.constraints
        }
        self.assertIn("uq_tournament_round_number", constraint_names)
        self.assertIn("uq_round_participant", constraint_names)
        self.assertIn(
            "ck_round_participant_paired_score_null",
            constraint_names,
        )

    def test_game_has_score_and_participant_constraints(self) -> None:
        table = Base.metadata.tables[Game.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertIsInstance(table.c.white_score.type, Numeric)
        self.assertIsInstance(table.c.black_score.type, Numeric)
        self.assertEqual(
            set(table.c.result_type.type.enums),
            {
                "normal",
                "white_forfeit",
                "black_forfeit",
                "double_forfeit",
                "adjusted",
            },
        )
        constraint_names = {constraint.name for constraint in table.constraints}
        self.assertTrue(
            {
                "ck_game_distinct_participants",
                "ck_game_scores_together",
                "ck_game_white_score",
                "ck_game_black_score",
                "ck_game_scores_total",
            }.issubset(constraint_names),
        )


class TournamentRoundSchemaTests(unittest.TestCase):
    def test_positive_round_number_is_required(self) -> None:
        round_payload = TournamentRoundCreate(section_id=1, number=3)

        self.assertEqual(round_payload.number, 3)
        with self.assertRaises(ValueError):
            TournamentRoundCreate(section_id=1, number=0)

    def test_participation_scores_are_limited(self) -> None:
        record = RoundParticipantCreate(
            round_id=1,
            participant_id=2,
            participation_type=ParticipationType.BYE,
            score_awarded=Decimal("0.5"),
        )

        self.assertEqual(record.score_awarded, Decimal("0.5"))
        with self.assertRaises(ValueError):
            RoundParticipantCreate(
                round_id=1,
                participant_id=2,
                participation_type=ParticipationType.BYE,
                score_awarded=Decimal("0.25"),
            )
        with self.assertRaises(ValueError):
            RoundParticipantCreate(
                round_id=1,
                participant_id=2,
                participation_type=ParticipationType.PAIRED,
                score_awarded=Decimal("1"),
            )
        with self.assertRaises(ValueError):
            RoundParticipantUpdate(participant_id=None)

    def test_game_scores_and_participants_are_validated(self) -> None:
        game = GameCreate(
            round_id=1,
            white_participant_id=2,
            black_participant_id=3,
            white_score=Decimal("1"),
            black_score=Decimal("0"),
            result_type=GameResultType.NORMAL,
        )

        self.assertEqual(game.white_score, Decimal("1"))
        with self.assertRaises(ValueError):
            GameCreate(
                round_id=1,
                white_participant_id=2,
                black_participant_id=2,
            )
        with self.assertRaises(ValueError):
            GameCreate(
                round_id=1,
                white_participant_id=2,
                black_participant_id=3,
                white_score=Decimal("1"),
            )
        with self.assertRaises(ValueError):
            GameCreate(
                round_id=1,
                white_participant_id=2,
                black_participant_id=3,
                white_score=Decimal("1"),
                black_score=Decimal("0.5"),
            )
        with self.assertRaises(ValueError):
            GameUpdate(black_participant_id=None)


if __name__ == "__main__":
    unittest.main()
