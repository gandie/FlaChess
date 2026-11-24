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
# T25 Implement Tournament Catalog and Draft Creation

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Operators need a visible tournament catalog and a focused way to create draft
tournaments, but the SPA currently exposes only the application foundation.
The generic CRUD list is not a sufficient screen contract for lifecycle and
structure counts.

## Objective
Deliver the first database-backed frontend slice with tournament summaries,
draft creation, and a URL-backed tournament overview that permits metadata
editing only while the backend tournament is draft.

## Scope
- Add a narrow tournament summary API contract for catalog rows.
- Add catalog and tournament overview navigation, loading, empty, and error
  states.
- Create draft tournaments from metadata and refresh backend state after writes.
- Add editable metadata controls to draft tournament overviews while presenting
  active and finished tournaments as read-only.
- Cover the API contract and static frontend markers with focused tests.

## Non-Goals
- Player registration, structure management, lifecycle transitions, or
  tournament deletion.
- Add pairing, standings, authentication, or real-time behavior.
- Introduce a frontend framework or build step.

## Target Files
- `app/schemas.py`
- `app/api.py`
- `app/routes/tournament_catalog.py`
- `app/static/`
- `tests/test_tournament_catalog.py`
- `tests/test_app.py`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T25_implement_tournament_catalog.md`

## Verification
- `node --check` passed for `api.js`, `router.js`, `render.js`,
  `tournaments.js`, and `app.js`.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_tournament_catalog.py"` passed (3 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_done_task_evaluation_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (74 tests).
- Operator browser interaction passed: tournament catalog navigation, test
  tournament creation, overview opening, and draft metadata behavior were
  exercised successfully.

## Rollback
Restore the prior frontend foundation and remove the tournament summary route,
focused tests, documentation, and T25 bookkeeping entries.

## Completion Artifact
The operator can browse tournament summaries, create a draft from the catalog,
open a stable tournament URL, and edit metadata only for draft tournaments.
The catalog summary returns lifecycle, dates, and participant/phase/section
counts without a paginated CRUD envelope. Draft creation and update flows
refresh authoritative backend state, and focused tests plus the full suite
pass with the change recorded in `done/`.
The operator completed the live browser smoke flow and created a test
tournament successfully.
