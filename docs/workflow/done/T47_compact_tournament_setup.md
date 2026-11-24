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

# T47 Compact Tournament Setup

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Tournament setup still requires substantial scrolling because each section
renders its full member and available-player lists inline, repeated across
phases and sections.

## Objective
Reduce draft tournament overview height while keeping section roster management
available on demand and preserving existing active/history views.

## Scope
- Collapse section membership and assignment panels by default in draft workspaces.
- Show the assigned-player count in each section disclosure summary.
- Add focused frontend-contract coverage and update operator documentation.

## Non-Goals
- Changing roster assignment, seed, lifecycle, or API behavior.
- Hiding phase, section, readiness, or tournament-level setup controls.

## Target Files
- app/static/structure.js
- tests/test_tournament_usability.py
- README.md
- docs/workflow/changelog/2026-11.md

## Verification
- Focused tournament usability tests passed: 6 tests.
- .\venv\Scripts\python.exe -m unittest discover .\tests\ — passed: 176 tests.
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py" — passed: 1 test.
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py" — passed: 1 test.
- Reloaded a live active tournament; its section roster remained expanded. The live catalog had no draft tournament to visually inspect the new disclosure.

## Rollback
Revert the focused section-roster disclosure and its directly related test and documentation updates.

## Completion Artifact
Draft section member and available-player lists start collapsed behind an
accessible disclosure with an assigned-player count; active and historical
section views retain their current expanded roster presentation. Frontend
contract tests cover the draft-only disclosure and assigned count. The
changelog records the implementation, validation, and residual risk.
