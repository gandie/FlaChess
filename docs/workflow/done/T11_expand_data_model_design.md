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
# T11 Expand Data Model Design

## Metadata
- Owner: unassigned
- Created: 2026-11-22
- Updated: 2026-11-22

## Why Needed
DATA.md is the main data structure design document, and it currently describes only the implemented Player table. Future tournament entities need a clear distinction between shipped schema and planned structure.

## Objective
Expand DATA.md with existing and planned entities, relationships, shared modeling conventions, and an actionable TODO section.

## Scope
- Separate implemented and planned database entities.
- Record Player as the existing table.
- Describe planned Tournament, tournament participant, Round, and Game structures.
- Capture known relationships from the project design.
- Identify unresolved design decisions without claiming them as implemented.

## Non-Goals
- Create models or migrations.
- Define final tournament-format policies.
- Implement CRUD routes or admin views.

## Target Files
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T11_expand_data_model_design.md`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`

## Rollback
Restore DATA.md to the Player-only description and remove T11 workflow records.

## Completion Artifact
DATA.md now separates the implemented Player table from planned Tournament, tournament participant, phase, round, and game entities. It includes shared modeling conventions and an actionable TODO list. Validation evidence: all 15 full-suite unittest tests passed and the Markdown boundary test passed (1 test).
