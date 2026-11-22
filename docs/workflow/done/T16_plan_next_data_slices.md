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
# T16 Plan Next Data Slices

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
The Tournament foundation is implemented, and DATA.md needs a current dependency-ordered implementation roadmap rather than the completed first-slice checklist.

## Objective
Replace the finished first implementation slice with the agreed second slice and explicit later slices.

## Scope
- Document phase, section, and section-participant work as the second slice.
- Document rounds and games as the following structural slice.
- Document tie-break configuration and standings as separate later slices.

## Non-Goals
- Implement any database entities in this task.
- Change the approved data model or lifecycle semantics.

## Target Files
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T16_plan_next_data_slices.md`

## Verification
- `.\venv\Scripts\python.exe -m unittest discover .\tests\`
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`

## Rollback
Restore the completed first-slice TODO block and remove the T16 workflow records.

## Completion Artifact
DATA.md identifies structure/membership as the second slice, followed by
rounds/games, tie-break configuration, and standings snapshots. Validation:
25 full-suite tests and the Markdown boundary test passed.
