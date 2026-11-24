---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-11-24
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
# T36 Add Pure Common Pairing Layer

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation needs one side-effect-free contract before format-specific
engines are added. Without shared input/output types, round-count rules, plan
validation, deterministic ordering, and color allocation, later Swiss,
round-robin, and knockout implementations would duplicate policy and drift from
the approved pairing decisions.

## Objective
Implement the pure common pairing layer and exhaustively test its approved
round-count, ordering, plan-integrity, bye, and color rules.

## Scope
- Add framework-free immutable pairing input and output types.
- Add format-specific round-count calculators and validation.
- Add deterministic seed, standings, and float ordering helpers.
- Add complete-plan and previous-opponent/bye validation.
- Add the shared deterministic color allocator.

## Non-Goals
- Implementing round-robin, Swiss, or knockout schedules.
- Reading or writing SQLAlchemy models.
- Adding FastAPI routes, persistence, or UI behavior.

## Target Files
- `app/pairing/`
- `tests/test_pairing_common.py`
- `tests/test_pairing_validation.py`
- `docs/workflow/changelog/`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest tests.test_pairing_common
  tests.test_pairing_validation` passed (24 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed (122
  tests).

## Rollback
Remove the common pairing package, its focused tests, and this task record; no
database or runtime entry points are changed.

## Completion Artifact
The framework-free pairing package exposes the shared types, round counts,
ordering, plan validation, and color allocator, with focused and full unittest
evidence recorded above. Format-specific engines remain isolated to the next
planned implementation steps.
