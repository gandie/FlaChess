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
# T24 Implement SPA Foundation

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
The current public frontend is only a hello-world page, so operators have no
application shell, URL-backed navigation, shared API behavior, or
database-independent smoke path before feature screens are added.

## Objective
Replace the placeholder with a responsive static SPA foundation that provides
navigation, reusable request/render/status primitives, and an explicit health
and backend-error smoke flow.

## Scope
- Create semantic application-shell HTML and responsive CSS.
- Add browser-native JavaScript modules for the API client, router, rendering
  primitives, and initial screens.
- Add a live health check and mapped 404 smoke interaction that require no
  database.
- Cover static asset serving and the smoke contract with focused tests.
- Align setup documentation and package data with the shipped frontend.

## Non-Goals
- Implement tournament, player, or lifecycle feature screens.
- Add a frontend framework, build step, authentication, or live updates.
- Add database-backed frontend behavior.

## Target Files
- `app/static/`
- `app/web.py`
- `pyproject.toml`
- `tests/test_app.py`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T24_implement_spa_foundation.md`

## Verification
- `node --check app\static\api.js; node --check app\static\router.js; node
  --check app\static\render.js; node --check app\static\app.js` passed.
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_app.py"`
  passed (9 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_done_task_evaluation_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (71 tests).

## Rollback
Restore the hello-world frontend, package-data glob, README wording, and
focused app tests, then remove T24 bookkeeping entries.

## Completion Artifact
The FastAPI-served root renders a responsive SPA shell with URL-backed
navigation. Its System view checks `/api/health`, demonstrates normalized 404
handling, and serves all static modules from the installed package. Focused
tests and the full 71-test suite pass, and this task is recorded in `done/`.
