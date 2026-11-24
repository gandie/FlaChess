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
# T28 Implement Activation and Section Operation Frontend

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Operators can configure draft tournaments but cannot activate them, activate
sections, create rounds, record manual pairings, or enter round outcomes from the
operator application. These actions currently require direct API use even though
their backend contracts already exist.

## Objective
Deliver the activation and section-operation vertical slice with an
operator-ready section read contract, lifecycle controls and conflict messages,
round creation, manual game pairing, result entry, and participation records for
byes, unplayed rounds, absences, comments, and awarded scores.

## Scope
- Add a narrow aggregate API contract for one section's operation workspace.
- Add tournament and section activation controls with authoritative backend
  errors.
- Add section navigation, round creation, manual pairing, game result editing,
  and non-game round participation records.
- Refuse unsupported score shapes in the UI before submitting valid combinations.
- Cover API contracts and static frontend behavior with focused tests.
- Update operator documentation and the frontend implementation marker.

## Non-Goals
- Pairing automation, color allocation, repeat-pairing policy, or phase placement.
- Standings display and round review.
- Section or tournament closeout controls.
- New lifecycle, score, or participation policy beyond existing backend rules.

## Target Files
- `app/section_operation_schemas.py`
- `app/routes/section_operation.py`
- `app/api.py`
- `app/static/`
- `tests/test_section_operation.py`
- `tests/test_app.py`
- `docs/DESIGN.md`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T28_implement_activation_section_operation.md`

## Verification
- `node --check` passed for `app\static\operations.js`,
  `app\static\tournaments.js`, `app\static\structure.js`, and
  `app\static\app.js`.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_section_operation.py"` passed (4 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_tournament_workspace.py"` passed (5 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_tournament_round_routes.py"` passed (7 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_done_task_evaluation_boundaries.py"` passed (1 test).
- .\venv\Scripts\python.exe -m unittest discover .\tests\
  passed (89 tests).

## Rollback
Restore the draft-only tournament overview, remove the section operation route
and frontend module, and remove the T28 tests, documentation, and bookkeeping
entries.

## Completion Artifact
An operator can activate a valid draft tournament, activate configured sections,
open a named section-operation workspace, create rounds and manual pairings,
enter valid game or forfeiture results with comments, and record byes, unplayed
rounds, absences, and awarded scores. Invalid local score combinations are
blocked while backend conflicts remain authoritative. Focused and full
validation pass and the completed work is recorded in the task and changelog.
