---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-11-26
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

# T60 Add Tie-Break Manual

## Metadata
- Owner: unassigned
- Created: 2026-11-26
- Updated: 2026-11-26

## Why Needed
Operators need a player-facing explanation of the tie-breaks supported by the
standings engine. The existing configuration screen names rules but does not
show what each value includes or how a reader can reproduce a calculation.

## Objective
Add a flat Manual page that explains every supported tie-break with a practical,
worked example and expose it as a primary navigation item.

## Scope
- Add a Manual route and primary navigation item.
- Explain all supported tie-break formulas, ordering behavior, and inputs.
- Include one reproducible calculation example for each supported tie-break.
- Add focused frontend contract coverage and responsive styling.

## Non-Goals
- Add unsupported tie-break algorithms or configuration controls.
- Change standings calculation behavior or persistence.
- Add a multi-level documentation navigation system.

## Target Files
- `app/static/index.html`
- `app/static/app.js`
- `app/static/manual.js`
- `app/static/styles.css`
- `app/static/styles/manual.css`
- `tests/test_tournament_usability.py`
- Workflow records

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_tournament_usability.py"
  - Passed: 16 tests.
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
  - Passed: 1 test.
- .\venv\Scripts\python.exe -m unittest discover .\tests\
  - Passed: 193 tests.
- `node --check app\static\manual.js` passed.
- `git diff --check` passed.

## Rollback
Remove the Manual navigation item, route, module, styles, and associated tests
while leaving tie-break configuration and standings calculation unchanged.

## Completion Artifact
The Manual page is available from primary navigation, explains how a
section's configured order is applied, and lists every supported tie-break
with examples that can be reproduced from recorded scores and opponent points.
