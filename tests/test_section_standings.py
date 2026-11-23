import unittest
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import AsyncIterator
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, DateTime, Integer, Numeric

from app.database import Base, get_session
from app.main import app
from app.models import (
    Game,
    GameResultType,
    ParticipationType,
    RoundParticipant,
    SectionParticipant,
    SectionStanding,
    SectionStandingValue,
    SectionTiebreak,
    TournamentRound,
)
from app.tournament_standings import (
    UnsupportedTiebreakError,
    calculate_standings,
)

class SectionStandingModelTests(unittest.TestCase):
    def test_standing_tables_define_snapshot_identity(self) -> None:
        standing_table = Base.metadata.tables[SectionStanding.__tablename__]
        value_table = Base.metadata.tables[SectionStandingValue.__tablename__]

        self.assertIsInstance(standing_table.c.id.type, BigInteger)
        self.assertTrue(standing_table.c.id.primary_key)
        self.assertIsInstance(standing_table.c.rank.type, Integer)
        self.assertIsInstance(standing_table.c.points.type, Numeric)
        self.assertIsInstance(standing_table.c.computed_at.type, DateTime)
        self.assertTrue(standing_table.c.computed_at.type.timezone)
        self.assertIn(
            "uq_section_standing_snapshot",
            {index.name for index in standing_table.indexes},
        )
        self.assertIn(
            "uq_section_standing_tiebreak",
            {constraint.name for constraint in value_table.constraints},
        )
        self.assertIn(
            "uq_section_standing_value_sequence",
            {constraint.name for constraint in value_table.constraints},
        )

class SectionStandingCalculationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.participants = [
            SectionParticipant(id=participant_id, participant_id=participant_id, section_id=9)
            for participant_id in range(1, 5)
        ]
        self.rounds = [
            TournamentRound(id=number, section_id=9, number=number)
            for number in range(1, 6)
        ]
        self.games = [
            self.game(1, 1, 2, "1", "0"),
            self.game(2, 1, 3, "0.5", "0.5"),
            self.game(3, 2, 3, "1", "0"),
            self.game(4, 2, 4, "0.5", "0.5"),
            self.game(5, 3, 4, "1", "0"),
        ]

    @staticmethod
    def game(
        round_id: int,
        white_id: int,
        black_id: int,
        white_score: str,
        black_score: str,
    ) -> Game:
        return Game(
            round_id=round_id,
            white_participant_id=white_id,
            black_participant_id=black_id,
            white_score=Decimal(white_score),
            black_score=Decimal(black_score),
            result_type=GameResultType.NORMAL,
        )

    @staticmethod
    def rule(id_: int, code: str, sequence: int) -> SectionTiebreak:
        return SectionTiebreak(
            id=id_,
            section_id=9,
            code=code,
            sequence=sequence,
            is_active=True,
        )

    def test_ranking_uses_direct_encounter_within_point_tie(self) -> None:
        standings = calculate_standings(
            self.participants,
            self.rounds,
            self.games,
            [],
            [self.rule(10, "direct_encounter", 1)],
        )

        by_id = {standing.participant_id: standing for standing in standings}
        self.assertEqual(
            [by_id[participant_id].rank for participant_id in range(1, 5)],
            [1, 2, 3, 4],
        )
        self.assertEqual(by_id[1].points, Decimal("1.5"))
        self.assertEqual((by_id[1].wins, by_id[1].draws, by_id[1].losses), (1, 1, 0))
        self.assertEqual(by_id[1].values[10], Decimal("1.5000"))
        self.assertEqual(by_id[2].values[10], Decimal("1.0000"))
        self.assertEqual(by_id[3].values[10], Decimal("0.5000"))

    def test_calculates_progressive_buchholz_and_sonneborn_values(self) -> None:
        rules = [
            self.rule(1, "progressive_score", 1),
            self.rule(2, "buchholz_cut_1", 2),
            self.rule(3, "sonneborn_berger", 3),
        ]

        standings = calculate_standings(
            self.participants,
            self.rounds,
            self.games,
            [],
            rules,
        )

        first = next(item for item in standings if item.participant_id == 1)
        self.assertEqual(first.values[1], Decimal("7.0000"))
        self.assertEqual(first.values[2], Decimal("1.5000"))
        self.assertEqual(first.values[3], Decimal("2.2500"))

    def test_rejects_policy_dependent_tiebreak_code(self) -> None:
        with self.assertRaises(UnsupportedTiebreakError):
            calculate_standings(
                self.participants,
                self.rounds,
                self.games,
                [],
                [self.rule(10, "koya", 1)],
            )

    def test_non_paired_award_adds_points_without_a_win(self) -> None:
        record = RoundParticipant(
            round_id=1,
            participant_id=4,
            participation_type=ParticipationType.BYE,
            score_awarded=Decimal("1"),
        )

        standings = calculate_standings(
            self.participants,
            self.rounds,
            self.games,
            [record],
            [self.rule(1, "number_of_wins", 1)],
        )

        fourth = next(item for item in standings if item.participant_id == 4)
        self.assertEqual(fourth.points, Decimal("1.5"))
        self.assertEqual(fourth.wins, 0)
        self.assertEqual(fourth.values[1], Decimal("0.0000"))


class SectionStandingRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_standing_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        self.assertIn("/api/tournament-sections/{section_id}/standings", paths)
        self.assertIn(
            "/api/tournament-sections/{section_id}/standings/recompute",
            paths,
        )

    def test_recompute_route_commits_persisted_snapshot(self) -> None:
        session = SimpleNamespace(
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )
        standing = SectionStanding(
            id=12,
            section_id=9,
            participant_id=4,
            rank=1,
            points=Decimal("1.5"),
            wins=1,
            draws=1,
            losses=0,
            game_points=None,
            computed_at=datetime.now(UTC),
            values=[],
        )

        async def override_session() -> AsyncIterator[object]:
            yield session

        app.dependency_overrides[get_session] = override_session
        with patch(
            "app.api.recompute_section_standings",
            new=AsyncMock(return_value=[standing]),
        ):
            response = self.client.post(
                "/api/tournament-sections/9/standings/recompute",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], 12)
        session.commit.assert_awaited_once()
