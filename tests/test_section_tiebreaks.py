import unittest
from datetime import UTC

from sqlalchemy import BigInteger, Boolean, Integer, String

from app.database import Base
from app.lifecycle import (
    LifecycleTransitionError,
    transition_section,
)
from app.models import SectionLifecycle, SectionTiebreak, TournamentSection
from app.schemas import SectionTiebreakCreate, SectionTiebreakUpdate


class SectionTiebreakModelTests(unittest.TestCase):
    def test_table_has_ordered_unique_configuration(self) -> None:
        table = Base.metadata.tables[SectionTiebreak.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertTrue(table.c.id.primary_key)
        self.assertIsInstance(table.c.code.type, String)
        self.assertEqual(table.c.code.type.length, 64)
        self.assertIsInstance(table.c.sequence.type, Integer)
        self.assertIsInstance(table.c.is_active.type, Boolean)
        self.assertIn(
            "uq_section_tiebreak_sequence",
            {constraint.name for constraint in table.constraints},
        )
        self.assertIn(
            "ck_section_tiebreak_sequence_positive",
            {constraint.name for constraint in table.constraints},
        )
        self.assertIn(
            "uq_section_tiebreak_configuration",
            {index.name for index in table.indexes},
        )

    def test_section_has_locked_section_lifecycle(self) -> None:
        table = Base.metadata.tables[TournamentSection.__tablename__]

        self.assertEqual(
            set(table.c.lifecycle.type.enums),
            {"draft", "active", "finished"},
        )
        self.assertFalse(table.c.lifecycle.nullable)


class SectionTiebreakSchemaTests(unittest.TestCase):
    def test_configuration_validates_required_values(self) -> None:
        tiebreak = SectionTiebreakCreate(
            section_id=1,
            code="buchholz_cut_1",
            sequence=1,
        )

        self.assertEqual(tiebreak.code, "buchholz_cut_1")
        self.assertTrue(tiebreak.is_active)
        with self.assertRaises(ValueError):
            SectionTiebreakCreate(section_id=1, code="", sequence=1)
        with self.assertRaises(ValueError):
            SectionTiebreakCreate(section_id=1, code="buchholz", sequence=0)
        with self.assertRaises(ValueError):
            SectionTiebreakUpdate(sequence=None)
        with self.assertRaises(ValueError):
            SectionTiebreakUpdate(is_active=None)


class SectionLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_activation_locks_configuration(self) -> None:
        section = TournamentSection(
            phase_id=1,
            name="Open",
            sequence=1,
            lifecycle=SectionLifecycle.DRAFT,
        )

        await transition_section(section, SectionLifecycle.ACTIVE, object())

        self.assertEqual(section.lifecycle, SectionLifecycle.ACTIVE)
        self.assertIsNotNone(section.tie_break_locked_at)
        self.assertIs(section.tie_break_locked_at.tzinfo, UTC)

    async def test_section_transitions_are_strict(self) -> None:
        section = TournamentSection(
            phase_id=1,
            name="Open",
            sequence=1,
            lifecycle=SectionLifecycle.DRAFT,
        )

        with self.assertRaises(LifecycleTransitionError):
            await transition_section(
                section,
                SectionLifecycle.FINISHED,
                object(),
            )

        await transition_section(section, SectionLifecycle.ACTIVE, object())
        await transition_section(section, SectionLifecycle.FINISHED, object())
        self.assertEqual(section.lifecycle, SectionLifecycle.FINISHED)
        with self.assertRaises(LifecycleTransitionError):
            await transition_section(section, SectionLifecycle.ACTIVE, object())


if __name__ == "__main__":
    unittest.main()
