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

# T49 Fix Seed Refresh And Layout Overlap

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Workspace state preservation restored stale generated seed values after section
assignments, while the new two-column narrow-desktop layout allowed date-time
fields and other controls to overflow and overlap.

## Objective
Keep section seed suggestions incrementing from backend state without losing
operator-edited fields, and eliminate control overlap at narrow desktop widths.

## Scope
- Mark generated seed values and preserve them only after operator edits.
- Add intrinsic shrink constraints and sidebar-local form layout rules.
- Add focused frontend contracts and browser-measured overlap verification.

## Non-Goals
- Changing section participant seed policy or backend API behavior.
- Redesigning the tournament setup information hierarchy.

## Target Files
- app/static/structure.js
- app/static/tournaments.js
- app/static/styles.css
- tests/test_tournament_usability.py
- README.md
- docs/workflow/changelog/2026-11.md

## Verification
- Focused tournament usability suite passed: 6 tests.
- Playwright verified untouched assignment seed advanced from 2 to 3 while an
  operator-edited seed remained 7.
- Playwright opened every disclosure at an 867px viewport and measured zero
  field/button overlap and zero controls escaping their containing forms.
- .\venv\Scripts\python.exe -m unittest discover .\tests\ — passed: 176 tests.
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" — passed: 1 test.

## Rollback
Revert the generated-seed state markers and the focused responsive shrink rules.

## Completion Artifact
Browser measurements show the next seed increments after assignment, no
workspace form/control overflow remains at the reported viewport, and full
validation passes. The changelog records implementation, validation, and the
remaining Docker rebuild requirement.
