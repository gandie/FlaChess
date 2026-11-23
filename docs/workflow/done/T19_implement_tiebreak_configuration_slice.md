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
# T19 Implement Tie-Break Configuration Slice

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
Tournament transitions already use lifecycle hooks, but section configuration
has no lifecycle boundary that can protect tie-break rules once play begins.
The existing mechanism is tournament-specific, so section lifecycle behavior
would otherwise require duplicated state-machine logic.

## Objective
Abstract lifecycle transitions into one reusable mechanism, add a strict
section lifecycle, implement ordered tie-break configuration, and freeze that
configuration when a section is activated.

## Scope
- Refactor tournament transitions onto reusable lifecycle mechanics.
- Add section `draft -> active -> finished` transitions and API actions.
- Add Section Tie-Break persistence, schemas, routes, migration, constraints,
  and SQLAdmin controls.
- Reject tie-break changes while the owning section is active or finished.
- Add focused model, schema, lifecycle, route, and admin tests.
- Update the data-model implementation checklist.

## Non-Goals
- Add phase, round, or game lifecycle states.
- Implement tie-break calculations or standings snapshots.
- Add automatic section activation when a round is created.

## Target Files
- `app/lifecycle.py`
- `app/models.py`
- `app/schemas.py`
- `app/api.py`
- `app/admin.py`
- `app/main.py`
- `migrations/versions/`
- `tests/`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest tests.test_section_tiebreaks
  tests.test_section_tiebreak_routes` passed (11 tests).
- `.\\venv\\Scripts\\alembic.exe upgrade --sql head` generated the section
  lifecycle constraint, tie-break table, ordered uniqueness constraint, and
  null-safe configuration index.
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed
  (63 tests).

## Rollback
Downgrade the tie-break/section-lifecycle migration and remove the T19
implementation and workflow records.

## Completion Artifact
Tournament and section transitions use the shared lifecycle engine; ordered
tie-break rows are exposed consistently through the API and SQLAdmin; activating
a section locks configuration. Focused and full tests plus offline Alembic SQL
prove protected writes, strict transitions, and schema integrity.
