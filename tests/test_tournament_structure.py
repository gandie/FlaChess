import unittest

from sqlalchemy import BigInteger, DateTime, Integer, String

from app.database import Base
from app.models import (
    SectionParticipant,
    TournamentPhase,
    TournamentPhaseFormat,
    TournamentSection,
)
from app.schemas import (
    SectionParticipantCreate,
    SectionParticipantUpdate,
    TournamentPhaseCreate,
    TournamentSectionCreate,
)


class TournamentStructureModelTests(unittest.TestCase):
    def test_phase_table_has_bigint_foreign_key_enum_and_constraints(self) -> None:
        table = Base.metadata.tables[TournamentPhase.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertTrue(table.c.id.primary_key)
        self.assertTrue(table.c.id.autoincrement)
        self.assertIsInstance(table.c.sequence.type, Integer)
        self.assertFalse(table.c.sequence.nullable)
        self.assertEqual(
            set(table.c.format.type.enums),
            {"knockout", "round_robin", "swiss"},
        )
        constraint_names = {constraint.name for constraint in table.constraints}
        self.assertIn("uq_tournament_phase_sequence", constraint_names)
        self.assertIn(
            "ck_tournament_phase_sequence_positive",
            constraint_names,
        )
        self.assertEqual(len(table.foreign_keys), 1)

    def test_section_table_has_planned_fields_and_constraints(self) -> None:
        table = Base.metadata.tables[TournamentSection.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertIsInstance(table.c.name.type, String)
        self.assertEqual(table.c.name.type.length, 255)
        self.assertIsInstance(table.c.tie_break_locked_at.type, DateTime)
        self.assertTrue(table.c.tie_break_locked_at.type.timezone)
        constraint_names = {constraint.name for constraint in table.constraints}
        self.assertIn("uq_tournament_section_sequence", constraint_names)
        self.assertIn(
            "ck_tournament_section_sequence_positive",
            constraint_names,
        )
        self.assertIn(
            "ck_tournament_section_round_count_positive",
            constraint_names,
        )

    def test_section_participant_has_membership_and_source_constraints(self) -> None:
        table = Base.metadata.tables[SectionParticipant.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertIsInstance(table.c.rating.type, Integer)
        self.assertIsInstance(table.c.rating_source.type, String)
        self.assertEqual(table.c.rating_source.type.length, 64)
        self.assertEqual(len(table.foreign_keys), 3)
        constraint_names = {constraint.name for constraint in table.constraints}
        self.assertIn("uq_section_participant_membership", constraint_names)
        self.assertIn(
            "ck_section_participant_rating_positive",
            constraint_names,
        )
        self.assertIn(
            "ck_section_participant_source_rank_positive",
            constraint_names,
        )


class TournamentStructureSchemaTests(unittest.TestCase):
    def test_phase_format_and_positive_values_are_validated(self) -> None:
        phase = TournamentPhaseCreate(
            tournament_id=1,
            sequence=1,
            format=TournamentPhaseFormat.SWISS,
        )

        self.assertEqual(phase.format, TournamentPhaseFormat.SWISS)
        with self.assertRaises(ValueError):
            TournamentPhaseCreate(
                tournament_id=1,
                sequence=0,
                format=TournamentPhaseFormat.SWISS,
            )
        with self.assertRaises(ValueError):
            TournamentPhaseCreate(
                tournament_id=1,
                sequence=1,
                format="double_swiss",
            )

    def test_section_and_membership_positive_values_are_validated(self) -> None:
        section = TournamentSectionCreate(
            phase_id=1,
            name="Open",
            sequence=1,
            planned_round_count=7,
        )
        membership = SectionParticipantCreate(
            participant_id=2,
            section_id=3,
            rating=1800,
            rating_source="fide",
            source_section_id=4,
            source_rank=1,
        )

        self.assertEqual(section.planned_round_count, 7)
        self.assertEqual(membership.source_rank, 1)
        for update in ({"planned_round_count": 0}, {"sequence": 0}):
            values = {
                "phase_id": 1,
                "name": "Open",
                "sequence": 1,
                **update,
            }
            with self.assertRaises(ValueError):
                TournamentSectionCreate(**values)
        with self.assertRaises(ValueError):
            SectionParticipantCreate(participant_id=2, section_id=3, rating=0)
        with self.assertRaises(ValueError):
            SectionParticipantUpdate(section_id=None)


if __name__ == "__main__":
    unittest.main()
