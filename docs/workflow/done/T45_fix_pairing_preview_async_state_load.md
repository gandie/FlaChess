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
# T45 Fix Pairing Preview Async State Load

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing preview can return 500 in a real PostgreSQL session because later
`populate_existing` state queries refresh the section identity and expire its
phase relationship before the pairing format is read. SQLAlchemy then attempts
async lazy I/O outside a valid greenlet context.

## Objective
Load the pairing format while the section phase relationship is eager and valid,
so preview and confirmation work through the real async state-loading path
without lazy relationship I/O.

## Scope
- Capture the validated pairing format before loading the remaining generation
  state.
- Add a regression test that invalidates the section relationship during later
  state loads.
- Preserve current preview, confirmation, and transaction behavior.

## Non-Goals
- Changes to pairing algorithms, format policy, or response contracts.
- Global SQLAlchemy loader configuration changes.
- Unrelated relationship-loading refactors.

## Target Files
- `app/pairing/generation_state.py`
- `tests/test_pairing_generation_routes.py`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_generation_routes`
  passed (8 tests).
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_operator_journey`
  passed (4 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (175 tests).
- `git --no-pager diff --check` passed.

## Rollback
Restore the previous pairing format read after state loading; no data model or
schema migration is involved.

## Completion Artifact
A regression test reproduces the section identity refresh and proves that
preview remains read-only without accessing an expired async relationship.
The pairing format is now captured before participant and history queries can
refresh the same section identity, preventing the production `MissingGreenlet`
error.
