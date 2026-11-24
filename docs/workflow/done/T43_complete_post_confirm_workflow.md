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
# T43 Complete Post-Confirm Workflow

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Confirmed pairing plans are committed successfully, but the operator remains on
the preview screen, and result completion does not explicitly control the
transition to recomputed standings and the next pairing preview. The section
operation workflow must carry the operator from generation through result entry
without leaving stale round or standings data on screen.

## Objective
After pairing confirmation, open the committed round, focus its result-entry
controls, recompute standings when that round is complete, and make the next
pairing preview available while preserving display visibility through the
existing section operation contract.

## Scope
- Navigate to and refresh the committed generated round after confirmation.
- Focus result-entry controls for the generated round.
- Recompute standings when the latest round becomes complete.
- Gate automated preview availability on completion of the latest round.
- Add focused frontend contract coverage and update the automation step.

## Non-Goals
- Pairing policy, planner, persistence, or API contract changes.
- End-to-end browser automation for all pairing formats.
- Changes to the manual round and pairing workflow.

## Target Files
- `app/static/operations.js`
- `tests/test_tournament_usability.py`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `node --check .\app\static\operations.js` passed.
- `.\venv\Scripts\python.exe -m unittest tests.test_tournament_usability`
  passed (5 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (170 tests).
- `git --no-pager diff --check` passed.

## Rollback
Restore the previous confirmation and result-refresh behavior, remove the
focused post-confirm assertions, and retain the existing pairing APIs and manual
operation controls.

## Completion Artifact
Frontend assets and focused tests demonstrate navigation to the generated
round, focused result entry, automatic standings recomputation after result
writes, and completion-gated next-preview availability through the unchanged
operation/display contract.
