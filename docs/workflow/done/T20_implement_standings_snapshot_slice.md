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
# T20 Implement Standings Snapshot Slice

## Metadata
- Owner: unassigned
- Created: 2026-11-23
- Updated: 2026-11-23

## Why Needed
The tournament data model now contains structure, rounds, results, and
configured tie-break rules, but no persisted snapshot identity or service can
calculate and preserve a reproducible section ranking.

## Objective
Implement standings snapshot persistence and a ranking/recomputation service
for completed game data, including focused calculations for deterministic
tie-break rules without inventing policy-dependent formulas.

## Scope
- Add section standing and standing-value models and migration.
- Define null-safe snapshot identity and recomputation semantics.
- Add schemas, read/recompute API routes, and SQLAdmin views.
- Calculate points, wins, draws, losses, ranks, and core deterministic
  tie-break values.
- Add focused model, schema, service, route, and migration tests.
- Mark the fifth data implementation slice complete in `docs/DATA.md`.

## Non-Goals
- Implement pairing, advancement, or lifecycle automation.
- Invent formulas for rating, performance, Koya, virtual-opponent, or fore
  Buchholz policy without explicit tournament rules.
- Recompute standings automatically when game results change.

## Target Files
- `app/models.py`
- `app/schemas.py`
- `app/api.py`
- `app/admin.py`
- `app/main.py`
- `app/tournament_standings.py`
- `migrations/versions/`
- `tests/`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest tests.test_section_standings`
  passed (7 tests).
- `.\\venv\\Scripts\\alembic.exe upgrade --sql head` generated the BIGSERIAL
  snapshot tables, constraints, foreign keys, and null-safe identity index.
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed
  (70 tests).
- Markdown and done-task evaluation boundary validation passed (1 test each).

## Rollback
Downgrade the standings migration, remove the standings service and integration
surfaces, restore the data-model checklist, and remove this task's workflow
records.

## Completion Artifact
Versioned standings tables and routes persist deterministic section snapshots;
recomputation replaces the selected snapshot atomically, and focused plus full
tests prove model constraints, calculations, ranking, and migration integrity.
