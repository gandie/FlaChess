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
# T13 Complete Tie-Break Data Model

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
DATA.md currently summarized tie-break configuration but did not contain every entity and field needed to calculate Swiss, round-robin, and knockout rankings from stored tournament data.

## Objective
Complete DATA.md with raw per-round participation, tie-break configuration, and optional normalized standings data.

## Scope
- Add per-round participant data for pairings, byes, forfeits, and unplayed rounds.
- Add section-level ordered tie-break configuration.
- Add normalized standing snapshots and tie-break values.
- Document constraints and tie-break calculation sources.

## Non-Goals
- Implement SQLAlchemy entities or migrations.
- Implement pairing or ranking algorithms.
- Add tournament CRUD changes.

## Target Files
- `docs/DATA.md`
- `docs/TIE_BREAKS.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T13_complete_tiebreak_data_model.md`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`

## Rollback
Restore the previous summarized tie-break design and remove T13 workflow records.

## Completion Artifact
DATA.md contains implementation-ready raw, configuration, and optional snapshot entities needed to calculate and display configured chess tie-breaks. Validation evidence: all 15 unittest tests passed and Markdown boundary validation passed.
