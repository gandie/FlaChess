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
# T18 Implement Rounds, Pairings, and Participation Outcomes

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
Tournament structure and section membership are implemented, but pairing and
round-outcome data cannot be persisted until rounds, games, and per-round
participation records exist.

## Objective
Implement the rounds, pairings, and participation-outcomes slice with
persistence, API contracts, administration controls, integrity rules, and
focused tests.

## Scope
- Add Tournament Round, Round Participant, and Game models with an Alembic
  migration.
- Add Pydantic schemas, FastCRUD routes, and SQLAdmin relationship selectors.
- Enforce documented round, score, participant, result-type, and participation
  constraints.
- Validate that game and round-participation members belong to the round's
  section in API and administration writes.

## Non-Goals
- Implement pairing generation, tournament advancement, tie-break
  configuration, or standings.
- Add format-specific duplicate-pair rules or game lifecycle transitions.

## Target Files
- `app/models.py`
- `app/schemas.py`
- `app/api.py`
- `app/admin.py`
- `app/main.py`
- `app/tournament_rounds.py`
- `migrations/versions/`
- `tests/test_tournament_rounds.py`
- `tests/test_tournament_round_routes.py`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_rounds.py"` passed (5 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_round_routes.py"` passed (7 tests).
- `.\\venv\\Scripts\\alembic.exe upgrade --sql head` generated the round,
  participation, and game tables with BIGSERIAL IDs, foreign keys, score
  checks, participant checks, and enum constraints.
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed (50 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_refactor_boundaries.py"` passed (1 test).
- Admin-label bug fix: `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_admin_forms.py"` passed (4 tests),
  including detached Section Participant and Round Participant labels.
- After the admin-label fix, `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
  passed (52 tests), and the refactor boundary test passed (1 test).

## Rollback
Downgrade the new migration and remove the T18 implementation and workflow
records.

## Completion Artifact
Rounds, games, and participation outcomes are persisted and exposed through
FastAPI and SQLAdmin with database and application integrity validation.
Focused and full unittest suites passed, and offline Alembic SQL generated the
complete round/pairing schema. Cross-section games and participation records
are rejected consistently from API and administration writes. Section
Participant and Round Participant dropdown labels use readable `@`-separated
player, section, round, and tournament context that survives detached ORM
session use.
