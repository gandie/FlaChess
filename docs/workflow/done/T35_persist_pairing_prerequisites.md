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
# T35 Persist Pairing Prerequisites

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation requires stable operator-assigned seed positions and an
explicit section-membership withdrawal state before any pairing engine can run.
The current membership model cannot preserve either invariant, so section
activation cannot reject incomplete or invalid pairable fields and operators
cannot safely withdraw or re-enter a member without changing history.

## Objective
Persist, validate, expose, and edit pairing seed and withdrawal prerequisites
without changing historical games or scores.

## Scope
- Add seed and withdrawal persistence plus an Alembic migration.
- Validate positive, section-unique seeds in schemas and membership services.
- Reject draft section activation with missing, duplicate, or invalid seeds for
  pairable fields.
- Add explicit withdraw and re-entry API and operator controls.
- Expose the state through workspace responses, admin, and membership CRUD.

## Non-Goals
- Pairing plans or pairing engines.
- Reopening the approved seed, bye, color, or withdrawal policies.
- Creating automatic scores or modifying historical round records.

## Target Files
- `migrations/versions/`
- `app/model_definitions/sections.py`
- `app/schemas.py`
- `app/routes/memberships.py`
- `app/lifecycle.py`
- `app/tournament_workspace_schemas.py`
- `app/routes/tournament_workspace.py`
- `app/admin_views/sections.py`
- `app/static/structure.js`
- `tests/`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_tournament_structure
  tests.test_tournament_structure_routes tests.test_tournament_workspace
  tests.test_section_tiebreaks` passed (27 tests).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (98 tests).

## Rollback
Revert the migration, pairing-prerequisite columns, routes, validation, workspace
fields, and operator controls; retain only pre-existing membership behavior.

## Completion Artifact
Memberships persist positive section-unique seed positions and explicit
withdrawal state; draft activation blocks invalid pairable fields; dedicated
actions support withdrawal/re-entry without touching historical round records;
the full unittest suite passes.

The migration and constraints are in
`migrations/versions/b4e7c9a1d2f3_add_pairing_prerequisites.py`, seed and
withdrawal state are exposed through workspace/admin/operator surfaces, and
generic membership updates reject attempts to bypass the explicit action
endpoints.
