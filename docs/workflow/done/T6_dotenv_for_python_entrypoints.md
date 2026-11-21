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
# T6 Loading Environment Files for Python Entry Points

## Metadata
- Owner: unassigned
- Created: 2026-11-21
- Updated: 2026-11-21

## Why Needed
FastAPI and Alembic currently depend on `DATABASE_URL` being exported into the process environment, while Docker Compose already reads the project `.env` file. Loading the same file for Python entry points removes this local setup mismatch.

## Objective
Use `python-dotenv` through one shared loader for FastAPI and Alembic, without overriding environment variables already supplied by the shell or container.

## Scope
- Add `python-dotenv` as a direct dependency.
- Add and use a shared loader for the FastAPI and Alembic entry points with `override=False`.
- Update local setup documentation and test the loader's precedence behavior.

## Non-Goals
- Change Docker Compose's environment-file behavior.
- Load dotenv files in unrelated scripts or tests.
- Change database URL format or credentials.

## Target Files
- `pyproject.toml`
- `app/config.py`
- `app/main.py`
- `migrations/env.py`
- `README.md`
- `tests/test_app.py`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T6_dotenv_for_python_entrypoints.md`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`
- `$env:DATABASE_URL = 'postgresql+asyncpg://user:password@localhost/fla_chess'; .\\venv\\Scripts\\alembic.exe upgrade --sql head`
- `.\\venv\\Scripts\\alembic.exe history`

## Rollback
Remove the dotenv dependency, shared loader, entry-point calls, related documentation and tests, and T6 workflow records.

## Completion Artifact
FastAPI and Alembic load the project `.env` automatically while preserving process-provided values. Validation completed: all 11 full-suite tests passed, the markdown boundary test passed, and the Alembic offline SQL and history commands passed. The focused FastAPI test file also passed all 8 tests.
