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
# T26 Implement Player and Tournament Registration

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Operators need to maintain reusable player records and assign those players to
draft tournaments before activation. The current frontend exposes only
tournament metadata, while generic participant records display foreign-key IDs
instead of an operator-ready registration view.

## Objective
Deliver the player directory and draft-tournament registration vertical slice,
including direct player summaries, participant names, and draft-only
registration and unregistration.

## Scope
- Add direct player and tournament participant read contracts with names.
- Enforce draft-only participant registration and unregistration on dedicated
  tournament routes.
- Add reusable player create and edit controls with loading and error states.
- Add participant registration controls to draft tournament overviews.
- Cover API contracts and static frontend markers with focused tests.

## Non-Goals
- Tournament structure, section membership, ratings, or lifecycle transitions.
- Pairing, standings, authentication, or real-time behavior.
- Player deletion from the operator UI.

## Target Files
- `app/schemas.py`
- `app/player_registration_schemas.py`
- `app/api.py`
- `app/routes/`
- `app/static/`
- `tests/test_player_registration.py`
- `tests/test_app.py`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T26_implement_player_registration.md`

## Verification
- `node --check app\\static\\players.js` passed.
- `node --check app\\static\\app.js` passed.
- `node --check app\\static\\tournaments.js` passed.
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p
  "test_player_registration.py"` passed (6 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed (80
  tests).

## Rollback
Restore the prior frontend catalog, remove the dedicated player and registration
contracts, focused tests, and T26 bookkeeping entries.

## Completion Artifact
The operator can create and edit players, browse a named player directory, and
register or unregister named players from a draft tournament. Active and
finished tournaments expose participants read-only. Focused and full validation
pass with the change recorded in `done/`.
Direct summary routes avoid generic pagination and display player names instead
of foreign-key IDs. Registration writes enforce the draft lifecycle in the
dedicated operator API.
