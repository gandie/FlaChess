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
# T38 Implement Swiss Pairing

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation step 5 requires a pure Swiss engine before transactional
generation can consume complete round plans. The planner must apply the approved
seed, standings, repeat, float, bye, and color policies without database or API
side effects.

## Objective
Implement deterministic in-memory FIDE/Dutch-style Swiss round planning with
bounded backtracking and explicit impossible-plan failures.

## Scope
- Pair round one from authoritative seed order and later rounds from standings.
- Preserve score groups, avoid repeats, and use controlled deterministic floats.
- Select at most one eligible Swiss bye recipient and award one point.
- Apply the shared color allocator and validate every returned plan.

## Non-Goals
- Reading or writing persisted tournament state.
- Adding preview, confirm, API, transaction, or UI behavior.
- Implementing knockout pairing.

## Target Files
- `app/pairing/`
- `tests/test_pairing_swiss.py`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_swiss` passed (11
  tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (141
  tests).

## Rollback
Remove the Swiss planner, exports, focused tests, and task completion record; no
persisted schema or runtime entry points are changed.

## Completion Artifact
The pure pairing package returns validated Swiss plans for requested rounds,
including deterministic seed/standings ordering, score-group matching, bounded
repeat fallback, controlled floats, one-point bye selection, shared colors, and
explicit failures for impossible inputs.
