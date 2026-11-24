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
# T27 Implement Draft Tournament Structure Frontend

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Operators can register players but still cannot configure phases, sections,
planned rounds, section membership, ratings, or ordered tie-break rules in the
tournament workspace. The overview also cannot explain which draft setup items
remain incomplete before activation.

## Objective
Deliver the draft tournament structure and rules vertical slice with an
operator-focused workspace contract, editable structure controls, named section
membership and ratings, supported-code-aware tie-break configuration, and
activation readiness that matches the backend lifecycle rule.

## Scope
- Add a narrow tournament workspace read contract with structure, membership,
  tie-breaks, supported codes, and readiness.
- Add draft overview controls for phases, sections, planned rounds, membership,
  ratings, and ordered tie-break configuration.
- Preserve section tie-break locks and backend-authoritative errors.
- Cover API contracts and static frontend behavior with focused tests.
- Update operator documentation and implementation completion markers.

## Non-Goals
- Tournament, section, or tie-break lifecycle transitions.
- Pairing, games, results, standings, or automated advancement.
- New activation policy beyond the existing two-player requirement.
- Browser framework, build step, authentication, or real-time behavior.

## Target Files
- `app/tournament_workspace_schemas.py`
- `app/routes/tournament_workspace.py`
- `app/api.py`
- `app/static/`
- `tests/test_tournament_workspace.py`
- `tests/test_app.py`
- `docs/DESIGN.md`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T27_implement_tournament_structure_frontend.md`

## Verification
- `node --check app\static\tournaments.js` passed.
- `node --check app\static\structure.js` passed.
- `node --check app\static\players.js` passed.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_tournament_workspace.py"` passed (5 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (85 tests).

## Rollback
Restore the previous tournament overview, remove the workspace read contract and
structure module, and remove the T27 tests, documentation, and bookkeeping
entries.

## Completion Artifact
The operator can inspect and edit draft phases, sections, planned rounds,
section membership, ratings, and ordered tie-break configuration from a stable
tournament overview. Existing supported codes are identified, unsupported codes
are visibly flagged, tie-break-locked sections are read-only, and readiness
distinguishes current activation blockers from setup warnings. Focused and full
validation pass and the change is recorded in the done task and changelog.
