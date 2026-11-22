from __future__ import annotations

import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.admin import TournamentSectionAdmin
from app.database import Base
from app.models import (
    Player,
    RoundParticipant,
    ParticipationType,
    SectionParticipant,
    Tournament,
    TournamentParticipant,
    TournamentPhase,
    TournamentPhaseFormat,
    TournamentRound,
    TournamentSection,
)


class PhaseScalars:
    def __init__(self, phase: TournamentPhase) -> None:
        self.phase = phase

    def unique(self) -> "PhaseScalars":
        return self

    def all(self) -> list[TournamentPhase]:
        return [self.phase]


class PhaseResult:
    def __init__(self, phase: TournamentPhase) -> None:
        self.phase = phase

    def scalars(self) -> PhaseScalars:
        return PhaseScalars(self.phase)


class PhaseSession:
    async def __aenter__(self) -> "PhaseSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def execute(self, statement: object) -> PhaseResult:
        phase = TournamentPhase(
            id=4,
            tournament_id=2,
            sequence=1,
            format=TournamentPhaseFormat.SWISS,
        )
        return PhaseResult(phase)


class PhaseSessionMaker:
    class_ = AsyncSession

    def __call__(self) -> PhaseSession:
        return PhaseSession()


class TournamentAdminFormTests(unittest.IsolatedAsyncioTestCase):
    async def test_section_create_form_loads_phase_options_without_relationships(
        self,
    ) -> None:
        admin = TournamentSectionAdmin()
        admin.session_maker = PhaseSessionMaker()

        form_class = await admin.scaffold_form(admin._form_create_rules)
        options = form_class.phase.kwargs["data"]

        self.assertIn("phase", form_class.__dict__)
        self.assertEqual(
            options,
            [("4", "Tournament 2 - Phase 1 (swiss)")],
        )


class TournamentParticipantLabelTests(unittest.TestCase):
    def test_label_survives_detachment_after_query(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            player = Player(id=1, name="Nora")
            tournament = Tournament(id=2, name="Club Championship")
            participant = TournamentParticipant(
                id=3,
                player=player,
                tournament=tournament,
            )
            session.add(participant)
            session.commit()

            participant_id = participant.id

        with Session(engine) as session:
            participant = session.scalar(
                select(TournamentParticipant).where(
                    TournamentParticipant.id == participant_id,
                ),
            )
            self.assertIsNotNone(participant)

        self.assertEqual(
            str(participant),
            "Nora @ Club Championship",
        )


def build_round_participant_fixture() -> RoundParticipant:
    tournament = Tournament(id=2, name="Club Championship")
    tournament_participant = TournamentParticipant(
        id=3,
        player=Player(id=1, name="Nora"),
        tournament=tournament,
    )
    phase = TournamentPhase(
        id=4,
        tournament=tournament,
        sequence=1,
        format=TournamentPhaseFormat.SWISS,
    )
    section = TournamentSection(
        id=5,
        phase=phase,
        name="Open",
        sequence=1,
    )
    section_participant = SectionParticipant(
        id=6,
        participant=tournament_participant,
        section=section,
    )
    tournament_round = TournamentRound(
        id=7,
        section=section,
        number=1,
    )
    return RoundParticipant(
        id=8,
        round=tournament_round,
        participant=section_participant,
        participation_type=ParticipationType.PAIRED,
    )


class RoundParticipantLabelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as session:
            session.add(build_round_participant_fixture())
            session.commit()

    def test_section_participant_label_survives_detachment(self) -> None:
        with Session(self.engine) as session:
            participant = session.scalar(
                select(SectionParticipant).where(SectionParticipant.id == 6),
            )
            self.assertIsNotNone(participant)

        self.assertEqual(
            str(participant),
            "Nora @ Open @ Club Championship",
        )

    def test_round_participant_label_survives_detachment(self) -> None:
        with Session(self.engine) as session:
            participant = session.scalar(
                select(RoundParticipant).where(RoundParticipant.id == 8),
            )
            self.assertIsNotNone(participant)

        self.assertEqual(
            str(participant),
            "Nora @ Open @ Round 1 @ Club Championship",
        )


if __name__ == "__main__":
    unittest.main()
