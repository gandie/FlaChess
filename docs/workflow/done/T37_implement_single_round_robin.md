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
# T37 Implement Single Round-Robin

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation step 4 requires a pure single round-robin engine before
transactional generation or operator routes can consume round plans. The engine
must prove that circle scheduling produces every unordered pairing exactly once
while handling odd fields with scoreless structural byes.

## Objective
Implement deterministic in-memory single round-robin planning for any pairable
eligible field, with independently verified even/odd circle schedules and the
existing color policy applied to each planned game.

## Scope
- Add a side-effect-free round-robin planner for one requested round.
- Generate schedules from authoritative seed order for even and odd fields.
- Verify calculated round counts, round shape, exact pair coverage, and no
  repeated unordered pairs.
- Add focused tests for determinism, byes, colors, coverage, and failures.

## Non-Goals
- Implementing database reads or writes, routes, preview/confirm workflows, or
  transactional generation.
- Implementing Swiss, knockout, or double round-robin behavior.

## Target Files
- `app/pairing/`
- `tests/test_pairing_round_robin.py`
- `docs/workflow/changelog/`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest tests.test_pairing_round_robin`
  passed (8 tests).
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed (130
  tests).

## Rollback
Remove the round-robin planner, exports, focused tests, and task completion
record; no persisted schema or runtime entry points are changed.

## Completion Artifact
The pure pairing package returns validated `PairingPlan` values for requested
single round-robin rounds. Even and odd schedules cover every unordered
participant pair exactly once, odd rounds include one scoreless structural bye,
and all plans use the shared deterministic color allocator. Focused and full
unittest evidence is recorded above.
