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
    correctness: 3
    scope_discipline: 1
    validation_trust: 2

  collaboration:
    ambiguity_handling: 2
    operator_load: 1
    trust_delta: 1

  notes: >
    Had to yell, forced toaster to write these evals. Simple shell sql tool escalated quickly.
---
# T8 Adding the Player Model and Database Tools

## Metadata
- Owner: unassigned
- Created: 2026-11-21
- Updated: 2026-11-21

## Why Needed
The database has no application entities or schema documentation yet, and developers lack a convenient way to inspect the Compose PostgreSQL database manually.

## Objective
Add the first player entity with a generated `BIGINT` primary key and a `VARCHAR(255)` name, document its schema, and provide a development SQL wrapper for the Compose database.

## Scope
- Add and register the SQLAlchemy player model.
- Create an Alembic migration for the player table.
- Document the player table and its fields in `docs/DATA.md`.
- Add a PowerShell helper for running `psql` against the Compose PostgreSQL service and document its use.
- Record the `BIGINT` primary-key rule in `AGENTS.md`.
- Add focused tests for the player model metadata.

## Non-Goals
- Add player API endpoints or tournament entities.
- Define player-name uniqueness or normalization rules.

## Target Files
- `AGENTS.md`
- `README.md`
- `app/models.py`
- `docs/DATA.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T8_player_model_and_database_tools.md`
- `migrations/env.py`
- `migrations/versions/`
- `tests/test_database.py`
- `tools/psql.ps1`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`
- `.\\venv\\Scripts\\alembic.exe upgrade --sql head`
- `docker compose -f .\\docker-compose.yml config --quiet`

## Rollback
Remove the player model, migration, database documentation and helper, revert the agent rule and README usage notes, and remove the T8 workflow records.

## Completion Artifact
The player model and migration define a generated `BIGINT` primary key and a required `VARCHAR(255)` name without uniqueness constraints. Schema documentation and a PowerShell Compose PostgreSQL `psql` wrapper are available. The wrapper uses the `fla_chess` user/database values from `.env.example` and passes a multi-word SQL query as one argument to `psql -c`. The full unittest suite passed (12 tests), markdown boundary and done-task evaluation checks passed (1 test each), Alembic offline SQL generation confirmed `BIGSERIAL` and `VARCHAR(255)`, Compose configuration passed, and a live query against the Compose database returned zero rows without error. A quoted query was also verified to remain intact as one argument.
