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
# T39 Implement Knockout Pairing

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation step 6 requires a pure knockout engine before transactional
generation can consume complete round plans. The planner must map operator seeds
into a standard padded bracket, advance only decisive winners, and fail instead
of inventing winners for drawn or unresolved predecessor matches.

## Objective
Implement deterministic in-memory knockout round planning for standard seeded
brackets, structural first-round byes, and bracket-ordered decisive advancement.

## Scope
- Place operator seeds in a standard seeded power-of-two bracket.
- Create scoreless structural byes in the first round.
- Advance only completed decisive predecessor winners in bracket order.
- Reject draws, unresolved matches, malformed predecessors, and out-of-range
  rounds.
- Apply the shared color allocator and validate every returned plan.

## Non-Goals
- Reading or writing persisted tournament state.
- Adding preview, confirm, API, transaction, or UI behavior.
- Automatic rematches, tie-break winners, or multi-game match aggregation.
- Third-place matches.

## Target Files
- `app/pairing/`
- `tests/test_pairing_knockout.py`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_knockout` passed (9
  tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (150
  tests).

## Rollback
Remove the knockout planner, exports, focused tests, and task completion record;
no persisted schema or runtime entry points are changed.

## Completion Artifact
The pure pairing package returns validated standard-seeded knockout plans with
structural first-round byes and explicit decisive-predecessor advancement, while
drawn, unresolved, malformed, or bracket-incomplete inputs fail without producing
a plan.
