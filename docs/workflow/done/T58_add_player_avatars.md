---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-11-26
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

# T58 Add Player Avatars

## Metadata
- Owner: unassigned
- Created: 2026-11-26
- Updated: 2026-11-26

## Why Needed
The player registry currently stores names only, so tournament rosters,
standings, pairings, and the final ceremony cannot visually identify players
at a glance. Player records need a reusable avatar that follows them through
all tournament presentation surfaces.

## Objective
Add validated avatar uploads to player records, normalize images for efficient
database storage, and render player avatars consistently across the operator
workspace and public tournament display.

## Scope
- Accept PNG, JPEG, and WebP uploads up to 5 MB.
- Center-crop and resize avatars to 200x200 PNG data URIs.
- Store avatars in the player database record.
- Support avatar preview, replacement, and removal in the player form.
- Include avatars in player, workspace, section operation, and registration
  response contracts.
- Show avatars with player names in rosters, pairings, standings, podiums, and
  the victory ceremony, with initials as the fallback.

## Non-Goals
- Add external file storage or CDN integration.
- Add authentication or access controls.
- Support arbitrary image formats or animated avatars.

## Target Files
- app/model_definitions/players.py
- app/player_avatars.py
- app/schemas.py
- app/player_registration_schemas.py
- app/tournament_workspace_schemas.py
- app/section_operation_schemas.py
- app/routes/
- app/static/
- migrations/versions/
- pyproject.toml
- tests/
- README.md
- docs/workflow/changelog/2026-11

## Verification
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_player_crud.py"
- Player CRUD focused tests passed (3 tests).
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_player_registration.py"
- Player registration focused tests passed (6 tests).
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_tournament_usability.py"
- Frontend usability focused tests passed (11 tests).
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"
- Markdown boundaries passed (1 test).
- .\venv\Scripts\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"
- Done-task evaluation boundaries passed (1 test).
- .\venv\Scripts\python.exe -m unittest discover .\tests\
- Full unittest discovery passed (188 tests).
- Refactor boundary validation passed (1 test).
- Python compile validation passed.
- `git diff --check` passed.
- Narrow-viewport Playwright inspection confirmed zero document and avatar
  editor overflow at 349 CSS pixels; the upload control and preview both use the
  full form width.

## Rollback
Revert the avatar migration, player contracts and avatar renderer, remove the
Pillow dependency, and restore the prior workflow records.

## Completion Artifact
Players can be created or edited with a validated avatar preview; the normalized
200x200 image persists as Base64 PNG text and is rendered throughout the
tournament UI with an initials fallback. The player table has an additive avatar
migration, all player-bearing response contracts carry avatars, and the public
display uses the images in pairings, standings, podiums, and the victory
ceremony. The creation/edit form uses a full-width, vertically stacked avatar
control so file help and preview content remain readable on narrow screens.
