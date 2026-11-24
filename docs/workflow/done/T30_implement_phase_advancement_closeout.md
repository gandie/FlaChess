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
# T30 Implement Phase Advancement and Closeout Frontend

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
The operator can activate tournaments and sections and review standings, but
the frontend cannot finish either lifecycle, manually place participants into
later draft sections with source provenance, or present a finished tournament
as a focused historical workspace.

## Objective
Complete the phase-advancement and closeout frontend slice using the existing
authoritative lifecycle routes and manual membership model, including final
standings review and read-only tournament history.

## Scope
- Finish active sections and active tournaments through confirmed explicit
  transitions.
- Edit membership in draft sections while a tournament is active, including
  optional prior-section and rank provenance.
- Expose membership provenance in the workspace contract and historical view.
- Hide mutation controls for finished tournaments and show final section
  standings through the existing section operation view.
- Add focused backend/static frontend tests and update operator documentation.

## Non-Goals
- Automatic phase advancement or placement.
- New lifecycle eligibility policy or pairing automation.
- Shared cross-section tournament ranking.

## Target Files
- `app/tournament_workspace_schemas.py`
- `app/routes/tournament_workspace.py`
- `app/section_operation_schemas.py`
- `app/routes/section_operation.py`
- `app/static/structure.js`
- `app/static/operations.js`
- `app/static/tournaments.js`
- `app/static/standings.js`
- `tests/test_tournament_workspace.py`
- `tests/test_section_operation.py`
- `tests/test_app.py`
- `docs/DESIGN.md`
- `README.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `node --check` passed for `app\static\structure.js`,
  `app\static\operations.js`, `app\static\standings.js`, and
  `app\static\tournaments.js`.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_tournament_workspace.py"` passed (5 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_section_operation.py"` passed (4 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\`
  passed (89 tests).

## Rollback
Revert the closeout and manual-advancement UI and workspace-contract additions,
then restore the previous task and documentation state.

## Completion Artifact
An operator can finish active sections and tournaments, manually assign
participants into later draft sections with source section/rank provenance, and
review final standings and historical structure without seeing mutation
controls. The section-operation contract includes tournament lifecycle so a
finished tournament remains read-only even if a section was left draft or active.
