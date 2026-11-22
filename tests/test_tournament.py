from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from typing import AsyncIterator

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, DateTime, String, Text

from app.database import Base, get_session
from app.main import app
from app.models import (
    Tournament,
    TournamentLifecycle,
    TournamentParticipant,
)
from app.schemas import (
    TournamentCreate,
    TournamentParticipantCreate,
    TournamentUpdate,
)


class FakeSession:
    def __init__(
        self,
        tournament: Tournament | None,
        participant_count: int = 0,
    ) -> None:
        self.tournament = tournament
        self.participant_count = participant_count
        self.scalar_calls = 0
        self.committed = False

    async def scalar(self, statement: object) -> object:
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return self.tournament
        return self.participant_count

    async def commit(self) -> None:
        self.committed = True


class TournamentDatabaseTests(unittest.TestCase):
    def test_tournament_table_constraints_and_types(self) -> None:
        table = Base.metadata.tables[Tournament.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertTrue(table.c.id.primary_key)
        self.assertTrue(table.c.id.autoincrement)
        self.assertIsInstance(table.c.name.type, String)
        self.assertEqual(table.c.name.type.length, 255)
        self.assertFalse(table.c.name.nullable)
        self.assertIsInstance(table.c.description.type, Text)
        self.assertIsInstance(table.c.starts_at.type, DateTime)
        self.assertTrue(table.c.starts_at.type.timezone)
        self.assertIn(
            "ck_tournament_dates",
            {constraint.name for constraint in table.constraints},
        )
        self.assertIn(
            "tournamentlifecycle",
            {constraint.name for constraint in table.constraints},
        )

    def test_participant_table_has_unique_pair_and_foreign_keys(self) -> None:
        table = Base.metadata.tables[TournamentParticipant.__tablename__]

        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertEqual(len(table.foreign_keys), 2)
        constraint_names = {constraint.name for constraint in table.constraints}
        self.assertIn("uq_tournament_participant", constraint_names)


class TournamentSchemaTests(unittest.TestCase):
    def test_create_defaults_to_draft_without_accepting_lifecycle(self) -> None:
        tournament = TournamentCreate(name="Club Championship")

        self.assertEqual(tournament.name, "Club Championship")
        self.assertNotIn("lifecycle", tournament.model_fields_set)
        with self.assertRaises(ValueError):
            TournamentCreate(name="")
        with self.assertRaises(ValueError):
            TournamentCreate(name="x" * 256)
        with self.assertRaises(ValueError):
            TournamentCreate(name="Event", time_control="x" * 256)

    def test_date_order_is_validated(self) -> None:
        starts_at = datetime(2026, 11, 22, tzinfo=UTC)

        TournamentCreate(
            name="Valid dates",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
        )
        with self.assertRaises(ValueError):
            TournamentCreate(
                name="Invalid dates",
                starts_at=starts_at,
                ends_at=starts_at,
            )
        with self.assertRaises(ValueError):
            TournamentUpdate(starts_at=starts_at, ends_at=starts_at)

    def test_participant_schema_requires_positive_ids(self) -> None:
        registration = TournamentParticipantCreate(
            tournament_id=1,
            player_id=2,
        )

        self.assertEqual(registration.tournament_id, 1)
        with self.assertRaises(ValueError):
            TournamentParticipantCreate(tournament_id=0, player_id=2)


class TournamentRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def use_session(self, session: FakeSession) -> None:
        async def override_session() -> AsyncIterator[FakeSession]:
            yield session

        app.dependency_overrides[get_session] = override_session

    def test_crud_and_lifecycle_routes_are_registered(self) -> None:
        paths = app.openapi()["paths"]

        for path in (
            "/api/tournaments",
            "/api/tournaments/{id}",
            "/api/tournament-participants",
            "/api/tournament-participants/{id}",
            "/api/tournaments/{id}/activate",
            "/api/tournaments/{id}/finish",
        ):
            self.assertIn(path, paths)

        self.assertIn("post", paths["/api/tournaments"])
        self.assertIn("patch", paths["/api/tournaments/{id}"])
        self.assertIn("post", paths["/api/tournaments/{id}/activate"])
        self.assertIn("post", paths["/api/tournaments/{id}/finish"])

    def test_activation_requires_two_participants(self) -> None:
        tournament = Tournament(id=1, name="Small field")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        session = FakeSession(tournament, participant_count=1)
        self.use_session(session)

        response = self.client.post("/api/tournaments/1/activate")

        self.assertEqual(response.status_code, 409)
        self.assertIn("at least two registered players", response.json()["detail"])
        self.assertEqual(tournament.lifecycle, TournamentLifecycle.DRAFT)
        self.assertFalse(session.committed)

    def test_activation_and_finish_follow_strict_transitions(self) -> None:
        tournament = Tournament(id=1, name="Club Championship")
        tournament.lifecycle = TournamentLifecycle.DRAFT
        activation_session = FakeSession(tournament, participant_count=2)
        self.use_session(activation_session)

        activation = self.client.post("/api/tournaments/1/activate")

        self.assertEqual(activation.status_code, 200)
        self.assertEqual(activation.json()["lifecycle"], "active")
        self.assertTrue(activation_session.committed)

        app.dependency_overrides.clear()
        finish_session = FakeSession(tournament)
        self.use_session(finish_session)
        finish = self.client.post("/api/tournaments/1/finish")

        self.assertEqual(finish.status_code, 200)
        self.assertEqual(finish.json()["lifecycle"], "finished")
        self.assertTrue(finish_session.committed)

    def test_invalid_transition_and_missing_tournament_are_conflicts(self) -> None:
        tournament = Tournament(id=1, name="Finished event")
        tournament.lifecycle = TournamentLifecycle.FINISHED
        self.use_session(FakeSession(tournament))

        invalid = self.client.post("/api/tournaments/1/activate")

        self.assertEqual(invalid.status_code, 409)

        app.dependency_overrides.clear()
        self.use_session(FakeSession(None))
        missing = self.client.post("/api/tournaments/999/finish")

        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
