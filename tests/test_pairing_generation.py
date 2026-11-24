from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.models import (
    ParticipationType,
    SectionLifecycle,
    TournamentPhaseFormat,
)
from app.pairing import (
    PairingGenerationConflict,
    PairingGenerationError,
    generate_next_round,
)
from app.pairing.generation_plan import prepare_pairing_plan
from app.pairing.generation_state import GenerationState
from app.pairing.types import PairingFormat

ROUND_ROBIN = TournamentPhaseFormat.ROUND_ROBIN
SWISS = TournamentPhaseFormat.SWISS
class ScalarResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return list(self.values)
class GenerationSession:
    def __init__(
        self,
        section: object,
        batches: list[list[object]],
        *,
        fail_flush: bool = False,
        fail_commit: bool = False,
    ) -> None:
        self.section = section
        self.batches = iter(batches)
        self.added: list[object] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_flush = fail_flush
        self.fail_commit = fail_commit

    async def scalar(self, statement: object) -> object:
        return self.section

    async def scalars(self, statement: object) -> ScalarResult:
        return ScalarResult(next(self.batches))

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_all(self, values: tuple[object, ...]) -> None:
        self.added.extend(values)

    async def flush(self) -> None:
        if self.fail_flush:
            raise RuntimeError("flush failed")
        self.added[0].id = 90

    async def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("insert", {}, Exception("duplicate"))
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1
class PairingGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_command_persists_complete_round(self) -> None:
        section = make_section(ROUND_ROBIN, 3)
        participants = make_participants(4)
        session = GenerationSession(
            section,
            [participants, [], []],
        )

        generated = await generate_next_round(7, session, 1)

        self.assertEqual(generated.round.number, 1)
        self.assertEqual(len(generated.games), 2)
        self.assertEqual(len(generated.records), 4)
        self.assertEqual(session.commit_count, 1)
        self.assertEqual(session.rollback_count, 0)
        self.assertEqual(
            {
                record.participation_type
                for record in generated.records
            },
            {ParticipationType.PAIRED},
        )

    async def test_odd_swiss_round_persists_awarded_bye(self) -> None:
        section = make_section(TournamentPhaseFormat.SWISS, 1)
        participants = make_participants(3)
        session = GenerationSession(
            section,
            [participants, [], []],
        )

        generated = await generate_next_round(7, session)

        byes = [
            record
            for record in generated.records
            if record.participation_type is ParticipationType.BYE
        ]
        self.assertEqual(len(generated.games), 1)
        self.assertEqual(len(byes), 1)
        self.assertEqual(byes[0].score_awarded, Decimal("1"))

    async def test_stale_round_conflict_rolls_back(self) -> None:
        section = make_section(TournamentPhaseFormat.ROUND_ROBIN, 3)
        session = GenerationSession(
            section,
            [make_participants(4), [], []],
        )

        expected = PairingGenerationConflict
        with self.assertRaisesRegex(expected, "next round is 1"):
            await generate_next_round(7, session, 2)

        self.assertEqual(session.added, [])
        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 1)

    async def test_flush_failure_rolls_back_everything(self) -> None:
        section = make_section(TournamentPhaseFormat.ROUND_ROBIN, 3)
        session = GenerationSession(
            section,
            [make_participants(4), [], []],
            fail_flush=True,
        )

        with self.assertRaisesRegex(RuntimeError, "flush failed"):
            await generate_next_round(7, session)

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 1)

    async def test_commit_failure_is_a_conflict(self) -> None:
        section = make_section(TournamentPhaseFormat.ROUND_ROBIN, 3)
        session = GenerationSession(
            section,
            [make_participants(4), [], []],
            fail_commit=True,
        )

        with self.assertRaises(PairingGenerationConflict):
            await generate_next_round(7, session)

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 1)

    def test_draft_and_missing_plan_are_rejected(self) -> None:
        draft = make_state(TournamentPhaseFormat.SWISS, 1, 2)
        draft.section.lifecycle = SectionLifecycle.DRAFT
        missing = make_state(TournamentPhaseFormat.SWISS, None, 2)

        with self.assertRaisesRegex(PairingGenerationConflict, "active"):
            prepare_pairing_plan(draft, None)
        with self.assertRaisesRegex(PairingGenerationError, "planned"):
            prepare_pairing_plan(missing, None)

    def test_missing_seed_and_skipped_round_rejected(self) -> None:
        missing_seed = make_state(SWISS, 1, 2)
        missing_seed.participants[1].seed_position = None
        skipped = replace(
            make_state(SWISS, 2, 2),
            rounds=(make_round(81, 2),),
        )

        with self.assertRaisesRegex(PairingGenerationError, "seed position"):
            prepare_pairing_plan(missing_seed, None)
        with self.assertRaisesRegex(PairingGenerationConflict, "numbering"):
            prepare_pairing_plan(skipped, None)

    def test_incomplete_previous_round_blocks_next(self) -> None:
        state = completed_round_state(4)
        state.games[0].black_score = None

        with self.assertRaisesRegex(PairingGenerationConflict, "incomplete"):
            prepare_pairing_plan(state, 2)

    def test_round_robin_rejects_mid_cycle_withdrawal(self) -> None:
        state = completed_round_state(4)
        state.participants[3].is_withdrawn = True

        with self.assertRaisesRegex(PairingGenerationConflict, "fixed"):
            prepare_pairing_plan(state, 2)

    def test_round_robin_ignores_prewithdrawn_members(self) -> None:
        state = completed_round_state(4)
        withdrawn = SimpleNamespace(
            id=5,
            section_id=7,
            seed_position=5,
            is_withdrawn=True,
        )
        state = replace(state, participants=(*state.participants, withdrawn))

        plan, field = prepare_pairing_plan(state, 2)

        self.assertEqual(plan.round_number, 2)
        self.assertEqual(len(field), 4)

    def test_knockout_round_two_advances_seeded_bracket(self) -> None:
        state = knockout_state()

        plan, _ = prepare_pairing_plan(state, 2)

        self.assertEqual(len(plan.games), 1)
        self.assertEqual(
            {
                plan.games[0].white_participant_id,
                plan.games[0].black_participant_id,
            },
            {1, 3},
        )


def make_section(
    pairing_format: TournamentPhaseFormat,
    planned_round_count: int | None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=7,
        lifecycle=SectionLifecycle.ACTIVE,
        planned_round_count=planned_round_count,
        phase=SimpleNamespace(format=pairing_format),
    )


def make_participants(count: int) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            id=index,
            section_id=7,
            seed_position=index,
            is_withdrawn=False,
        )
        for index in range(1, count + 1)
    ]


def make_round(round_id: int, number: int) -> SimpleNamespace:
    return SimpleNamespace(id=round_id, section_id=7, number=number)


def make_state(
    pairing_format: TournamentPhaseFormat,
    planned_round_count: int | None,
    participant_count: int,
) -> GenerationState:
    section = make_section(pairing_format, planned_round_count)
    return GenerationState(
        section=section,
        pairing_format=PairingFormat(pairing_format.value),
        participants=tuple(make_participants(participant_count)),
        rounds=(),
        games=(),
        records=(),
        tiebreaks=(),
    )


def completed_round_state(count: int) -> GenerationState:
    state = make_state(TournamentPhaseFormat.ROUND_ROBIN, count - 1, count)
    round_ = make_round(80, 1)
    games = [
        SimpleNamespace(
            id=index,
            round_id=round_.id,
            white_participant_id=2 * index - 1,
            black_participant_id=2 * index,
            white_score=Decimal("1"),
            black_score=Decimal("0"),
        )
        for index in range(1, count // 2 + 1)
    ]
    records = [
        SimpleNamespace(
            id=participant.id,
            round_id=round_.id,
            participant_id=participant.id,
            participation_type=ParticipationType.PAIRED,
            score_awarded=None,
        )
        for participant in state.participants
    ]
    return GenerationState(
        state.section,
        state.pairing_format,
        state.participants,
        (round_,),
        tuple(games),
        tuple(records),
        (),
    )


def knockout_state() -> GenerationState:
    state = make_state(TournamentPhaseFormat.KNOCKOUT, 2, 3)
    round_ = make_round(80, 1)
    game = SimpleNamespace(
        id=1,
        round_id=round_.id,
        white_participant_id=2,
        black_participant_id=3,
        white_score=Decimal("0"),
        black_score=Decimal("1"),
    )
    records = [
        SimpleNamespace(
            id=1,
            round_id=round_.id,
            participant_id=2,
            participation_type=ParticipationType.PAIRED,
            score_awarded=None,
        ),
        SimpleNamespace(
            id=2,
            round_id=round_.id,
            participant_id=3,
            participation_type=ParticipationType.PAIRED,
            score_awarded=None,
        ),
        SimpleNamespace(
            id=3,
            round_id=round_.id,
            participant_id=1,
            participation_type=ParticipationType.BYE,
            score_awarded=None,
        ),
    ]
    return GenerationState(
        state.section,
        state.pairing_format,
        state.participants,
        (round_,),
        (game,),
        tuple(records),
        (),
    )
