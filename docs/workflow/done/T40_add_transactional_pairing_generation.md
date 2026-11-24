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
# T40 Add Transactional Pairing Generation

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing plans are now pure and validated, but no domain command can load
authoritative section state and persist a complete next round atomically. The
automation chain needs a transaction boundary that prevents partial rounds and
blocks invalid lifecycle, numbering, eligibility, completeness, and conflict
states before any write.

## Objective
Add one domain command that plans and persists the next round for an active
section in one commit, rolling back every domain or persistence failure.

## Scope
- Reload section, phase, members, rounds, games, records, and standings state.
- Validate lifecycle, planned/calculated counts, seeds, eligibility, numbering,
  prior-round completeness, and existing-round conflicts.
- Dispatch to the existing pure Swiss, round-robin, and knockout planners.
- Freeze round-robin membership after round one and reject membership changes.
- Persist the round, games, and round-participant records atomically.
- Add focused transaction and domain-validation tests.

## Non-Goals
- Preview or confirm HTTP endpoints.
- Pydantic API contracts or frontend controls.
- Changes to pairing policy or pure pairing algorithms.

## Target Files
- `app/pairing/`
- `tests/`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_generation`
  passed (11 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_round_robin
  tests.test_pairing_swiss tests.test_pairing_knockout` passed (28 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (161
  tests).

## Rollback
Remove the generation command, focused tests, exports, and task completion
record; no schema changes are introduced.

## Completion Artifact
An active section's next pairing round is persisted completely or not at all,
with authoritative state validation and rollback evidence from focused and full
tests. The exported `generate_next_round` command reloads and locks section
state, supports all three pure planners, freezes round-robin membership after
round one, and commits generated round rows as one transaction.
