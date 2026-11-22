---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: YYYY-MM-DD
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness:
    scope_discipline:
    validation_trust:

  collaboration:
    ambiguity_handling:
    operator_load:
    trust_delta:

  notes: >
    HUMAN NOTES
---
# T15 Implement Tournament Slice

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
The application needs persistent tournament records, registration rows, and explicit lifecycle transitions before tournament phases, sections, rounds, and games can be implemented.

## Objective
Implement the first Tournament slice with a minimal participant registration table so activation can enforce the documented two-player rule.

## Scope
- Add Tournament and TournamentParticipant models and an Alembic migration.
- Add Pydantic create/update schemas and FastCRUD routes.
- Add SQLAdmin views for tournaments and registrations.
- Implement strict draft-to-active-to-finished lifecycle routes.
- Add focused model, schema, route, constraint, and lifecycle tests.

## Non-Goals
- Implement phases, sections, rounds, games, standings, or pairing.
- Add participant registration workflow states.
- Implement reopening finished tournaments.
- Add public tournament frontend screens or admin authentication.

## Target Files
- `app/models.py`
- `app/lifecycle.py`
- `app/schemas.py`
- `app/api.py`
- `app/admin.py`
- `app/main.py`
- `migrations/versions/`
- `tests/test_tournament.py`
- `README.md`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T15_implement_tournament_slice.md`

## Verification
- `.\venv\Scripts\python.exe -m unittest discover .\tests\`
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`
- `.\venv\Scripts\alembic.exe upgrade --sql head`

## Rollback
Revert the Tournament application, migration, tests, and documentation changes and remove the T15 workflow records.

## Completion Artifact
Tournament and registration CRUD/admin surfaces exist. Alembic SQL creates
the BIGINT-keyed constrained tables, including lifecycle and date checks.
Lifecycle tests prove strict transitions and the two-player activation guard.
SQLAdmin regression coverage proves Tournament Participant forms use relationship
selectors for tournament and player rather than suppressed raw foreign-key
columns.
Validation passed: 25 full-suite tests, Markdown and done-task boundary checks,
and offline Alembic SQL generation through head.
