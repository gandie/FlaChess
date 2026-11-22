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
# T12 Tournament Data Structure Design

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
The next implementation session should be able to add Tournament and related models without discovering unresolved data structure decisions. DATA.md must capture each answered design branch before implementation.

## Objective
Complete the first Tournament data structure design through a guided operator decision interview.

## Scope
- Record the selected Tournament lifecycle states and state-machine convention.
- Resolve format representation and tournament/phase structure.
- Resolve participant registration semantics.
- Resolve round/game storage and score invariants.
- Update DATA.md with the resulting first implementation slice.

## Non-Goals
- Add SQLAlchemy models or migrations.
- Implement FastCRUD or SQLAdmin routes.
- Implement a reusable state-machine runtime.

## Target Files
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T12_tournament_data_structure_design.md`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`

## Rollback
Restore unanswered decision branches to planned/provisional notes and remove T12 workflow records until the design interview is complete.

## Completion Artifact
DATA.md now contains an implementation-ready Tournament first slice and records the selected lifecycle, format, participant, phase, section, round, game, pairing, and score decisions. The remaining design TODOs were closed for Game SQL constraints and source-backed tie-break configuration; detailed tie-break guidance is in `docs/TIE_BREAKS.md`. Validation evidence: all 15 full-suite unittest tests passed, the Markdown boundary test passed, and the done-task boundary test passed.
