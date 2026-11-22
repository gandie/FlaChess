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
# T17 Implement Structure and Membership Slice

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
The tournament foundation exists, but phases, sections, and section membership
are required before rounds, pairings, and standings can be implemented.

## Objective
Implement the tournament structure and membership hierarchy with persistence,
API contracts, administration selectors, integrity rules, and tests.

## Scope
- Add Tournament Phase, Tournament Section, and Section Participant models and
  an Alembic migration.
- Add Pydantic schemas, FastCRUD routes, and SQLAdmin relationship selectors.
- Enforce documented uniqueness, positive values, phase formats, and
  cross-tournament membership validity.

## Non-Goals
- Implement rounds, pairings, participation outcomes, tie-break configuration,
  or standings.
- Add tournament advancement or section assignment policy.

## Target Files
- `app/models.py`
- `app/schemas.py`
- `app/api.py`
- `app/admin.py`
- `app/main.py`
- `app/tournament_structure.py`
- `migrations/versions/`
- `tests/test_tournament_structure.py`
- `tests/test_tournament_structure_routes.py`
- `tests/test_tournament_admin_forms.py`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_structure.py"` passed (5 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_structure_routes.py"` passed (6 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_tournament_admin_forms.py"` passed (1 test).
- The admin-form test command now also verifies the participant label and
  detached-relationship safety (2 tests).
- `.\\venv\\Scripts\\alembic.exe upgrade --sql head` generated the phase, section,
  and membership tables with BIGSERIAL IDs, foreign keys, positive-value checks,
  uniqueness, and the fixed-format check.
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed after
  the admin-form and participant-label fixes (38 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"` passed (1 test).

## Rollback
Downgrade the new migration and remove the T17 implementation and workflow
records.

## Completion Artifact
Tournament phases, sections, and section memberships are persisted, exposed
through FastCRUD/FastAPI and SQLAdmin, and protected by database and application
validation. Cross-tournament membership is rejected consistently from API and
admin writes. Focused and full unittest suites passed, and offline Alembic SQL
generated the complete structure/membership schema. The follow-up admin-form
fix made phase labels depend only on loaded phase columns, preventing
`MissingGreenlet` errors while SQLAdmin builds the section creation form. A
subsequent participant-label fix renders `<player> @ <tournament>` and eagerly
loads both relationships so detached admin option formatting remains safe.
