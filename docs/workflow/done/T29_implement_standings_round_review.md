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
# T29 Implement Standings and Round Review Frontend

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Operators can enter section results, but the application does not recompute or
display standings after those writes and has no focused round review. They
currently have to use the API directly to inspect named rankings, tie-break
values, snapshot times, and incomplete versus recorded games.

## Objective
Deliver the standings and round-review vertical slice with an operator-visible
named standings table, configured tie-break columns, snapshot time, automatic
recomputation after result changes, and focused navigation between rounds.

## Scope
- Extend the section operation contract with active ordered tie-break metadata.
- Recompute standings through a selected round after standings-affecting writes.
- Show ranks, player names, points, wins/draws/losses, tie-break values, and
  snapshot time.
- Navigate round-by-round and distinguish incomplete games from recorded
  results.
- Add focused backend and static frontend tests.
- Update operator documentation and the frontend implementation marker.

## Non-Goals
- Section or tournament closeout controls.
- Pairing automation or automatic phase advancement.
- New standings or tie-break policy.

## Target Files
- `app/section_operation_schemas.py`
- `app/routes/section_operation.py`
- `app/static/operations.js`
- `app/static/styles.css`
- `tests/test_section_operation.py`
- `tests/test_app.py`
- `docs/DESIGN.md`
- `README.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `node --check` passed for `app\static\app.js`,
  `app\static\operations.js`, and `app\static\standings.js`.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_section_operation.py"` passed (4 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (89 tests).

## Rollback
Remove standings review and automatic recomputation from the operation view and
restore the prior section-operation contract, focused tests, and documentation.

## Completion Artifact
An operator can review one round at a time, distinguish incomplete games, and
see refreshed named standings with points, record, tie-break values, and snapshot
time after recording standings-affecting data. Active tie-break metadata is
included in the section operation contract, result writes recompute the selected
round snapshot, and round navigation is preserved in stable URL state.
